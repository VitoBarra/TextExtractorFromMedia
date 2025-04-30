import os
import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
from ProxyUtil import *
import random as rnd



# --- Settings ---
VIDEO_FOLDER = "data"
OUTPUT_FOLDER = "transcript"                # Where HTML files will be saved
UPLOAD_URL = "https://vizard.ai/upload?from=video-to-text&tool-page=%2Fen%2Ftools%2Fvideo-to-text"         # Change this

WAIT_TIME_AFTER_UPLOAD = 3600                  # Adjust depending on upload processing time

# Allowed video/audio extensions
ALLOWED_EXTENSIONS = (".mp4", ".mov", ".3gp", ".avi", ".mp3", ".wav", ".m4a")


def upload_video(proxy:object = None):
    if proxy is not None:
        proxy_string =f"{proxy['ip']}:{proxy['port']}"
        print(f"Using proxy: {proxy_string}")
        driver = Driver(uc=True, headless=False, proxy=proxy_string )
    else:
        # initialize the driver in GUI mode with UC enabled
        driver = Driver(uc=True, headless=False)


    # Initialize an empty dictionary to store folder names and video file paths
    folder_video_map = {}

    # Loop through subfolders and files using os.walk
    for root, dirs, files in os.walk(VIDEO_FOLDER):
        # Filter for allowed video files in the current directory
        video_files = [f for f in files if f.lower().endswith(ALLOWED_EXTENSIONS)]

        # If there are any video files in this folder, add them to the map
        if video_files:
            folder_name = os.path.basename(root)  # Get the parent folder name (just the last part of the path)
            if folder_name.lower() == "data":
                continue
            folder_video_map[folder_name] = [os.path.abspath(os.path.join(root, f)) for f in video_files]


    # --- Upload each file ---
    for folder_name, video_list in folder_video_map.items():
        for videoPath in video_list:
            print(f"Uploading file (absolute path): {videoPath}")

            # Refresh the page before each upload (optional, depends on the site)
            driver.uc_open_with_reconnect(UPLOAD_URL, 6)
            time.sleep(2)

            print(f"finding the element to upload the file")
            # Find file input and upload
            file_input = driver.find_element(By.ID, "file-input")
            file_input.send_keys(videoPath)

            # Wait for upload & processing
            print(f"Waiting with timeout: {WAIT_TIME_AFTER_UPLOAD} seconds...")
            # Locate the element by text and class
            upload_button = WebDriverWait(driver, WAIT_TIME_AFTER_UPLOAD).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'win-confirm-button') and contains(text(), 'Upload')]"))
            )
            upload_button.click()
            driver.uc_gui_click_captcha()

            # Wait for the URL to change
            transcript_div = WebDriverWait(driver, WAIT_TIME_AFTER_UPLOAD).until(EC.element_to_be_clickable((By.ID, "transcript_button")))

            # Click the div
            transcript_div.click()
            # Get the scrollable container
            text_area = driver.find_element(By.ID, "textArea")



            # actions = ActionChains(driver)
            # actions.move_to_element(text_area).scroll_by_amount()
            # # Scroll until no more new content

            i = 0

            while True:
                try:
                    # Try to find paragraph by its ID
                    paragraph = text_area.find_element(By.ID, f"paragraph_{i}")

                    # Scroll this paragraph into view
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", paragraph)
                    time.sleep(0.5)  # Small pause to allow loading

                    print(f"Scrolled to paragraph_{i}")

                    i += 1  # Go to the next paragraph

                except Exception:
                    # If no paragraph with the next ID is found, we assume we finished
                    print(f"No more paragraphs found after paragraph_{i-1}. Finished scrolling.")
                    break

            print("Scrolling complete.")



            # Save the HTML output
            # At this point, all paragraphs should be loaded
            text_area_HTML = text_area.get_attribute("innerHTML")

            html_filename = os.path.join(OUTPUT_FOLDER, folder_name, f"{os.path.splitext(os.path.basename(videoPath))[0]}.html")
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(text_area_HTML)

            print(f"Saved HTML to {html_filename}\n")

    # --- Cleanup ---
    driver.quit()
    print("All done!")




if __name__ == "__main__":
    # --- Create output folder if it doesn't exist ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    proxy_list = fetchHTTPS_proxies()
    # proxy_list = fetch_proxies()
    # proxy_list = fetch_proxy_swiftshadow()


    for proxy in proxy_list:
        try:
            upload_video(proxy)
            break
        except Exception :
            print(f"failed to upload with proxy {proxy['ip']}:{proxy['port']}")


