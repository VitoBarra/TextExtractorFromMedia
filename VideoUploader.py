import json
import time
from enum import Enum

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
from concurrent.futures import ThreadPoolExecutor, as_completed

from ProxyUtil import *
from VideoTranscriptJobDescriptor import *


class JobStatus(Enum):
    Succeeded = 0
    ProxyError = 1
    Error = 2




# --- Settings ---
UPLOAD_URL = "https://vizard.ai/upload?from=video-to-text&tool-page=%2Fen%2Ftools%2Fvideo-to-text"
WAIT_TIME_AFTER_UPLOAD = 60 * 10


class PageUnreachable(BaseException):
    pass


def upload_video(job:VideoTranscriptJobDescriptor, proxy:object = None):
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
        if proxy is not None:
            proxy_string =f"{proxy['ip']}:{proxy['port']}"
            driver = Driver(uc=True, headless=False, proxy=proxy_string )
        else:
            # initialize the driver in GUI mode with UC enabled
            driver = Driver(uc=True, headless=False)

        # Refresh the page before each upload (optional, depends on the site)
        try:
            driver.uc_open_with_reconnect(UPLOAD_URL, 6)

            # Find file input and upload
            time.sleep(2)
            file_input = driver.find_element(By.ID, "file-input")
        except Exception:
            raise PageUnreachable
        file_input.send_keys(job.VideoName)

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
        print (f"{threadName}: waiting for transcript button")
        # Wait for the URL to change
        transcript_div = WebDriverWait(driver, WAIT_TIME_AFTER_UPLOAD).until(EC.element_to_be_clickable((By.ID, "transcript_button")))

        # Click the div
        transcript_div.click()
        # Get the scrollable container
        text_area = driver.find_element(By.ID, "textArea")

        i = 0

        while True:
            try:
                # Try to find paragraph by its ID
                paragraph = text_area.find_element(By.ID, f"paragraph_{i}")

                # Scroll this paragraph into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", paragraph)
                time.sleep(0.5)  # Small pause to allow loading

                print(f"{threadName}: Scrolled to paragraph_{i}")

                i += 1  # Go to the next paragraph

            except Exception:
                # If no paragraph with the next ID is found, we assume we finished
                print(f"{threadName}: No more paragraphs found after paragraph_{i-1}. Finished scrolling.")
                break

        print(f"{threadName}: Scrolling complete.")



        # Save the HTML output
        # At this point, all paragraphs should be loaded
        text_area_HTML = text_area.get_attribute("innerHTML")

        html_filename = os.path.join(OUTPUT_FOLDER,job.VideoProjectFolder, f"{os.path.splitext(os.path.basename(job.VideoName))[0]}.html")
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






def try_upload(jobDesc:VideoTranscriptJobDescriptor, proxy:str) ->(str,JobStatus):
    try:
        upload_video(jobDesc, proxy)
        return proxy,JobStatus.Succeeded  # Success
    except PageUnreachable:
        return proxy,JobStatus.ProxyError
    except Exception as e :
        print(f"Exception : {e}")
        return proxy,JobStatus.Error


def is_file_recent(file_path, max_age_seconds):
    if not os.path.exists(file_path):
        return False
    file_mtime = os.path.getmtime(file_path)
    return (time.time() - file_mtime) < max_age_seconds



def load_proxies_from_file(file_path):
    with open(file_path, "r") as f:
        return  json.load(f)

PROXY_FILE =  'proxy_list.json'
MAX_AGE_SECONDS = 3600

if __name__ == "__main__":
    # --- Create output folder if it doesn't exist ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    video_jobs = GenerateJobsFromVideo()



    # Controllo se il file è recente e lo uso, altrimenti chiamo la funzione
    if is_file_recent(PROXY_FILE, MAX_AGE_SECONDS):
        proxy_list = load_proxies_from_file(PROXY_FILE)
        print(f"loaded {len(proxy_list)} proxy from file {PROXY_FILE}")
    else:
        proxy_list = fetchHTTPS_proxies()
        # proxy_list = fetch_proxies()
        # proxy_list = fetch_proxy_swiftshadow()
        with open(PROXY_FILE, "w") as f:
            json.dump( proxy_list, f)
        print(f"downloaded {len(proxy_list)} saved in file {PROXY_FILE}")


    MAX_ATTEMPTS = 1

    # Track how many times each job was attempted
    job_attempts = {job: 0 for job in video_jobs}
    while True:
        incomplete_jobs = [job for job in video_jobs if not job.IsCompleted and job_attempts[job] < MAX_ATTEMPTS]

        if not incomplete_jobs:
            print("All jobs completed (or reached max attempts).")
            break

        for job in incomplete_jobs:
            if job.Lock.locked():
                continue
            print(f"Trying job: {job}")

            with ThreadPoolExecutor(max_workers=10) as executor:
                proxyTried =0
                futures = {executor.submit(try_upload, job, proxy): proxy for proxy in proxy_list}
                proxy_to_try = len(proxy_list)
                for future in as_completed(futures):
                    proxyTried= proxyTried + 1
                    proxy , status = future.result()
                    if status == JobStatus.Succeeded:
                        print(f"job {job} succeeded with proxy {proxy['ip']}:{proxy['port']}")
                        job.IsCompleted = True
                        break
                    else:
                        print(f"job progress, proxy tried:  {proxyTried}/{proxy_to_try}")
                        if status == JobStatus.ProxyError:
                            proxy_list.remove(proxy) # remove bad proxy for next job
                            # Save tried proxies to file
                            with open(PROXY_FILE, 'w') as f:
                                json.dump(proxy_list, f, indent=2)

                if not job.IsCompleted:
                    print(f"Upload failed for job {job}. Will retry.")
                    job_attempts[job] += 1

        # Optional: avoid hammering in a tight loop
        time.sleep(2)
