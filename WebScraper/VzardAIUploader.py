import time
from enum import Enum

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
from concurrent.futures import ThreadPoolExecutor, as_completed

from DataProcessing import HTML_OUTPUT_FOLDER, SPLITTED_VIDEO_FOLDER
from WebScraper.ProxyUtil import *
from WebScraper.VideoTranscriptJobDescriptor import *
from WebScraper.WebScrapingUtility import find_element_if_present, click_element_if_clickable, JobStatus, \
    PageUnreachable

# --- Settings ---
UPLOAD_URL = "https://vizard.ai/upload?from=video-to-text&tool-page=%2Fen%2Ftools%2Fvideo-to-text"
WAIT_TIME_AFTER_UPLOAD = 60 * 10



def MainUploadLoop (driver,language='english',max_retries=3,threadName="Noname"):
    retry_count=0
    while retry_count < max_retries:
        print(f"{threadName}: Checking page state (Attempt {retry_count + 1}/{max_retries})...")

        # Use short timeouts to check for the presence of key elements
        transcript_button = find_element_if_present(driver, By.ID, "transcript_button" , 60*3)
        # Ensure language is lowercase for case-insensitive XPath comparison
        language_xpath = f"//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{language.lower()}']"
        language_button = find_element_if_present(driver, By.XPATH, language_xpath , timeout=5)

        cloudflare_xpath = "//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'checking if the site connection is secure')]"
        cloudflare_banner = find_element_if_present(driver, By.XPATH, cloudflare_xpath, timeout=5)

        retry_xpath = "//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'retry']"
        retry_button = find_element_if_present(driver, By.XPATH, retry_xpath, timeout=5)

        # Logic based on found elements
        if transcript_button:
            print(f"{threadName}: Found transcript button.")
            # Give it time to become clickable
            if click_element_if_clickable(driver, transcript_button, timeout=30):
                print(f"{threadName}: Transcript button clicked successfully.")
                break # Success, exit the loop
            else:
                print(f"{threadName}: Transcript button found but could not be clicked.")
                # You might want to increment retry_count or handle the error differently
                retry_count += 1
                time.sleep(5) # Pause before retrying
                continue

        elif language_button:
            print(f"{threadName}: Found language button '{language}'.")
            if click_element_if_clickable(driver, language_button, timeout=15):
                print(f"{threadName}: Language button clicked.")
                # Find and click the "Continue" button
                continue_xpath = "//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'continue']"
                continue_button = find_element_if_present(driver, By.XPATH, continue_xpath, timeout=5)
                if click_element_if_clickable(driver, continue_button, timeout=5):
                    print(f"{threadName}: 'Continue' button clicked.")
                    # Don't increment retry_count, the process is progressing
                    time.sleep(2) # Short pause for page load
                    # Go back to the start of the loop to look for the transcript button
                    continue
                else:
                    print(f"{threadName}: 'Continue' button not found or not clickable after selecting language.")
                    retry_count += 1
                    time.sleep(5)
                    continue
            else:
                print(f"{threadName}: Could not click the language button.")
                retry_count += 1
                time.sleep(5)
                continue

        elif cloudflare_banner:
            print(f"{threadName}: Cloudflare/Bot detection banner detected. Aborting.")
            # Here you might want to close the driver or handle it differently
            # return # Exits the containing function/method
            return

        elif retry_button:
            print(f"{threadName}: Found 'retry' button.")
            if click_element_if_clickable(driver, retry_button, timeout=10):
                retry_count += 1
                print(f"{threadName}: Clicked 'retry' button ({retry_count}/{max_retries}).")
                time.sleep(10) # Wait a bit after retry
                continue
            else:
                print(f"{threadName}: Could not click the 'retry' button.")
                # Still count it as an attempt
                retry_count += 1
                time.sleep(5)
                continue

        else:
            # None of the expected elements were found within the short timeouts
            print(f"{threadName}: No known state element found. Waiting and retrying...")
            retry_count += 1
            # Wait a bit before the next general attempt
            time.sleep(15)

        # After the loop
    if retry_count >= max_retries:
        print(f"{threadName}: Maximum number of retries ({max_retries}) reached. Could not proceed.")





def upload_video(job:VideoTranscriptJobDescriptor, proxy:dict[str] = None , headless_Mode = False):
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
                        proxy=f"{proxy['ip']}:{proxy['port']}" if proxy is not None else None )

        # Refresh the page before each upload (optional, depends on the site)
        try:
            driver.uc_open_with_reconnect(UPLOAD_URL, 6)

            # Find file input and upload
            time.sleep(2)
            file_input = driver.find_element(By.ID, "file-input")
        except Exception:
            raise PageUnreachable
        file_input.send_keys(str(job.VideoPath))

        if job.Lock.locked():
            print(f"{threadName}: Waiting on lock acquisition")

        job.Lock.acquire()
        ConditionSettedByMe = True
        if job.IsCompleted:
            return
        print(f"{threadName}: Waiting that the upload finishes...blocking other instances")

        # Locate the element by text and class
        upload_button = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'win-confirm-button') and contains(text(), 'Upload')]")))

        upload_button.click()
        driver.uc_gui_click_captcha()

        MainUploadLoop(driver,job.Language,3, threadName=str(threadName))

        # Get the scrollable container
        text_area = driver.find_element(By.ID, "textArea")


        paragraph_count = 0
        while True:
            try:
                # Try to find paragraph by its ID
                paragraph = text_area.find_element(By.ID, f"paragraph_{paragraph_count}")

                # Scroll this paragraph into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", paragraph)
                time.sleep(0.5)  # Small pause to allow loading

                print(f"{threadName}: Scrolled to paragraph_{paragraph_count}")

                paragraph_count += 1  # Go to the next paragraph

            except Exception:
                # If no paragraph with the next ID is found, we assume we finished
                print(f"{threadName}: No more paragraphs found after paragraph_{paragraph_count-1}. Finished scrolling.")
                break

        print(f"{threadName}: Scrolling complete.")



        # Save the HTML output
        # At this point, all paragraphs should be loaded
        text_area_HTML = text_area.get_attribute("innerHTML")
        html_filename = job.GetHTMLOutputFilePath()
        # Ensure the directory exists
        os.makedirs(os.path.dirname(html_filename), exist_ok=True)
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(text_area_HTML)

        print(f"{threadName}: Saved HTML to {html_filename}\n")
        job.IsCompleted = True
    except Exception:
        raise
    finally:
        # --- Cleanup ---
        if driver is not None:
            driver.quit()
        if ConditionSettedByMe:
            job.Lock.release()
            print(f"{threadName}: lock released for job {job}")






def try_upload(jobDesc:VideoTranscriptJobDescriptor, proxy:dict[str], headless_mode = False) ->JobStatus:
    try:
        upload_video(jobDesc, proxy, headless_mode)
        return JobStatus.Success  # Success
    except PageUnreachable:
        return JobStatus.PageConnectionError
    except Exception as e :
        print(f"Try_update Exception : {e}")
        return JobStatus.GenericError

def UploadVideoFolder(Input_folder=SPLITTED_VIDEO_FOLDER, output_folder = HTML_OUTPUT_FOLDER, headless_Mode = False):
    """
    :param Input_folder:
    :param output_folder:
    :param headless_Mode:
    :return: true if all jobs completed successfully
    """
    MAX_AGE_SECONDS = 1800
    MAX_RETRIES = 3
    proxy_failures = {}  # Track consecutive failures for each proxy


    proxy_list = getProxyList(PROXY_FILE,MAX_AGE_SECONDS)
    video_jobs = GenerateJobsFromVideo(Input_folder, output_folder)

    incomplete_jobs = [job for job in video_jobs if not os.path.isfile(job.GetHTMLOutputFilePath())]

    if not incomplete_jobs:
        print("All transcription jobs completed successfully")
        return True

    while len(proxy_list)>0:

        for job in incomplete_jobs:
            if job.Lock.locked():
                continue
            print(f"Processing transcription job: {job}")

            with ThreadPoolExecutor(max_workers=8) as executor:
                proxyTried = 0
                futures = {executor.submit(try_upload, job, proxy, headless_Mode): proxy for proxy in proxy_list}
                proxy_to_try = len(proxy_list)
                for future in as_completed(futures):
                    proxyTried= proxyTried + 1

                    proxy = futures[future]
                    status = future.result()
                    proxy_str = f"{proxy['ip']}:{proxy['port']}"

                    print(f"job progress, proxy tried:  {proxyTried}/{proxy_to_try}")
                    if status == JobStatus.Success:
                        print(f"Job {job} completed successfully with proxy {proxy_str}")
                        job.IsCompleted = True
                        incomplete_jobs.remove(job)
                        break
                    elif status == JobStatus.PageConnectionError:
                        proxy_list.remove(proxy)  # Remove non-working proxy for next job
                        # Save working proxies to file
                        WriteJson(PROXY_FILE, proxy_list)
                    elif status == JobStatus.GenericError:
                        proxy_failures[proxy_str] = proxy_failures.get(proxy_str, 0) + 1
                        if proxy_failures[proxy_str] >= MAX_RETRIES:  # Remove proxy after maximum allowed failures
                            proxy_list.remove(proxy)
                            del proxy_failures[proxy_str]  # Clean up failure tracking
                            # Save updated proxy list
                            WriteJson(PROXY_FILE, proxy_list)
                            print(f"Removed proxy {proxy} after {MAX_RETRIES} failures")

                if not job.IsCompleted:
                    print(f"Upload failed for job {job}")

        time.sleep(2)
    return all(job.IsCompleted for job in video_jobs)

