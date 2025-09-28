import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
from selenium.webdriver.common.by import By

from DataProcessing import HTML_OUTPUT_FOLDER, SPLITTED_VIDEO_FOLDER
from WebScraper.ProxyUtil import *
from WebScraper.VideoTranscriptJobDescriptor import *
from WebScraper.WebScrapingUtility import find_element_if_present, click_element_if_clickable, JobStatus, PageUnreachable
from Utility.Logger import info, warning, error, debug

# --- Settings ---
UPLOAD_URL = "https://vizard.ai/upload?from=video-to-text&tool-page=%2Fen%2Ftools%2Fvideo-to-text"
WAIT_TIME_AFTER_UPLOAD = 60 * 10


def MainUploadLoop(driver, language='english', max_retries=3, threadName="Noname"):
    retry_count = 0
    while retry_count < max_retries:
        info(f"{threadName}: Checking page state (Attempt {retry_count + 1}/{max_retries})...")

        transcript_button = find_element_if_present(driver, By.ID, "transcript_button", 60*3)
        language_xpath = f"//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{language.lower()}']"
        language_button = find_element_if_present(driver, By.XPATH, language_xpath, timeout=5)

        cloudflare_xpath = "//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'checking if the site connection is secure')]"
        cloudflare_banner = find_element_if_present(driver, By.XPATH, cloudflare_xpath, timeout=5)

        retry_xpath = "//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'retry']"
        retry_button = find_element_if_present(driver, By.XPATH, retry_xpath, timeout=5)

        if transcript_button:
            info(f"{threadName}: Found transcript button.")
            if click_element_if_clickable(driver, transcript_button, timeout=30):
                info(f"{threadName}: Transcript button clicked successfully.")
                break
            else:
                warning(f"{threadName}: Transcript button found but could not be clicked.")
                retry_count += 1
                time.sleep(5)
                continue

        elif language_button:
            info(f"{threadName}: Found language button '{language}'.")
            if click_element_if_clickable(driver, language_button, timeout=15):
                info(f"{threadName}: Language button clicked.")
                continue_xpath = "//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'continue']"
                continue_button = find_element_if_present(driver, By.XPATH, continue_xpath, timeout=5)
                if click_element_if_clickable(driver, continue_button, timeout=5):
                    info(f"{threadName}: 'Continue' button clicked.")
                    time.sleep(2)
                    continue
                else:
                    warning(f"{threadName}: 'Continue' button not found or not clickable after selecting language.")
                    retry_count += 1
                    time.sleep(5)
                    continue
            else:
                warning(f"{threadName}: Could not click the language button.")
                retry_count += 1
                time.sleep(5)
                continue

        elif cloudflare_banner:
            warning(f"{threadName}: Cloudflare/Bot detection banner detected. Aborting.")
            return

        elif retry_button:
            info(f"{threadName}: Found 'retry' button.")
            if click_element_if_clickable(driver, retry_button, timeout=10):
                retry_count += 1
                info(f"{threadName}: Clicked 'retry' button ({retry_count}/{max_retries}).")
                time.sleep(10)
                continue
            else:
                warning(f"{threadName}: Could not click the 'retry' button.")
                retry_count += 1
                time.sleep(5)
                continue

        else:
            warning(f"{threadName}: No known state element found. Waiting and retrying...")
            retry_count += 1
            time.sleep(15)

    if retry_count >= max_retries:
        error(f"{threadName}: Maximum number of retries ({max_retries}) reached. Could not proceed.")


def upload_video(job: VideoTranscriptJobDescriptor, proxy: dict[str] = None, headless_Mode=False):
    job.Lock.acquire()
    if job.IsCompleted:
        job.Lock.release()
        return
    else:
        job.Lock.release()

    threadName = threading.get_ident()
    ConditionSettedByMe = False
    driver = None
    try:
        driver = Driver(uc=True, headless=headless_Mode,
                        proxy=f"{proxy['ip']}:{proxy['port']}" if proxy else None)

        try:
            driver.uc_open_with_reconnect(UPLOAD_URL, 6)
            time.sleep(2)
            file_input = driver.find_element(By.ID, "file-input")
        except Exception:
            raise PageUnreachable

        file_input.send_keys(str(job.VideoPath))

        if job.Lock.locked():
            info(f"{threadName}: Waiting on lock acquisition")

        job.Lock.acquire()
        ConditionSettedByMe = True
        if job.IsCompleted:
            return
        info(f"{threadName}: Waiting that the upload finishes...blocking other instances")

        upload_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'win-confirm-button') and contains(text(), 'Upload')]"))
        )
        upload_button.click()
        driver.uc_gui_click_captcha()

        MainUploadLoop(driver, job.Language, 3, threadName=str(threadName))

        text_area = driver.find_element(By.ID, "textArea")
        paragraph_count = 0
        while True:
            try:
                paragraph = text_area.find_element(By.ID, f"paragraph_{paragraph_count}")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", paragraph)
                time.sleep(0.5)
                info(f"{threadName}: Scrolled to paragraph_{paragraph_count}")
                paragraph_count += 1
            except Exception:
                info(f"{threadName}: No more paragraphs found after paragraph_{paragraph_count-1}. Finished scrolling.")
                break

        info(f"{threadName}: Scrolling complete.")

        text_area_HTML = text_area.get_attribute("innerHTML")
        html_filename = job.GetHTMLOutputFilePath()
        os.makedirs(os.path.dirname(html_filename), exist_ok=True)
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(text_area_HTML)
        info(f"{threadName}: Saved HTML to {html_filename}\n")
        job.IsCompleted = True

    except Exception:
        raise
    finally:
        if driver:
            driver.quit()
        if ConditionSettedByMe:
            job.Lock.release()
            info(f"{threadName}: lock released for job {job}")


def try_upload(jobDesc: VideoTranscriptJobDescriptor, proxy: dict[str], headless_mode=False) -> JobStatus:
    try:
        upload_video(jobDesc, proxy, headless_mode)
        return JobStatus.Success
    except PageUnreachable:
        return JobStatus.PageConnectionError
    except Exception as e:
        error(f"try_upload Exception: {e}")
        return JobStatus.GenericError


def UploadVideoFolder(Input_folder=SPLITTED_VIDEO_FOLDER, output_folder=HTML_OUTPUT_FOLDER, headless_Mode=False):
    """
    :param Input_folder:
    :param output_folder:
    :param headless_Mode:
    :return: true if all jobs completed successfully
    """
    MAX_AGE_SECONDS = 1800
    MAX_RETRIES = 3
    proxy_failures = {}

    proxy_list = getProxyList(PROXY_FILE, MAX_AGE_SECONDS)
    video_jobs = GenerateJobsFromVideo(Input_folder, output_folder)
    incomplete_jobs = [job for job in video_jobs if not os.path.isfile(job.GetHTMLOutputFilePath())]

    if not incomplete_jobs:
        info("All transcription jobs completed successfully")
        return True

    while proxy_list:
        for job in incomplete_jobs:
            if job.Lock.locked():
                continue
            info(f"Processing transcription job: {job}")

            with ThreadPoolExecutor(max_workers=8) as executor:
                proxyTried = 0
                futures = {executor.submit(try_upload, job, proxy, headless_Mode): proxy for proxy in proxy_list}
                proxy_to_try = len(proxy_list)
                for future in as_completed(futures):
                    proxyTried += 1
                    proxy = futures[future]
                    status = future.result()
                    proxy_str = f"{proxy['ip']}:{proxy['port']}"

                    info(f"Job progress, proxy tried: {proxyTried}/{proxy_to_try}")
                    if status == JobStatus.Success:
                        info(f"Job {job} completed successfully with proxy {proxy_str}")
                        job.IsCompleted = True
                        incomplete_jobs.remove(job)
                        break
                    elif status == JobStatus.PageConnectionError:
                        proxy_list.remove(proxy)
                        WriteJson(PROXY_FILE, proxy_list)
                    elif status == JobStatus.GenericError:
                        proxy_failures[proxy_str] = proxy_failures.get(proxy_str, 0) + 1
                        if proxy_failures[proxy_str] >= MAX_RETRIES:
                            proxy_list.remove(proxy)
                            del proxy_failures[proxy_str]
                            WriteJson(PROXY_FILE, proxy_list)
                            warning(f"Removed proxy {proxy_str} after {MAX_RETRIES} failures")

                if not job.IsCompleted:
                    error(f"Upload failed for job {job}")

        time.sleep(2)

    return all(job.IsCompleted for job in video_jobs)
