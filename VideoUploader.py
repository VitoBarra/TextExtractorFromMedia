import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver




# --- Settings ---
VIDEO_FOLDER = "data"  # Change this
OUTPUT_FOLDER = "transcript"                # Where HTML files will be saved
UPLOAD_URL = "https://vizard.ai/upload?from=video-to-text&tool-page=%2Fen%2Ftools%2Fvideo-to-text"         # Change this
WAIT_TIME_AFTER_UPLOAD = 3600                  # Adjust depending on upload processing time

# Allowed video/audio extensions
ALLOWED_EXTENSIONS = (".mp4", ".mov", ".3gp", ".avi", ".mp3", ".wav", ".m4a")

# --- Create output folder if it doesn't exist ---
os.makedirs(OUTPUT_FOLDER, exist_ok=True)



# initialize the driver in GUI mode with UC enabled
driver = Driver(uc=True, headless=False)
driver.uc_open_with_reconnect(UPLOAD_URL , 6)

# Save the current URL
start_url = driver.current_url

# Initialize an empty dictionary to store folder names and video file paths
folder_video_map = {}

# Loop through subfolders and files using os.walk
for root, dirs, files in os.walk(VIDEO_FOLDER):
    # Filter for allowed video files in the current directory
    video_files = [f for f in files if f.lower().endswith(ALLOWED_EXTENSIONS)]

    # If there are any video files in this folder, add them to the map
    if video_files:
        folder_name = os.path.basename(root)  # Get the folder name (just the last part of the path)
        folder_video_map[folder_name] = [os.path.abspath(os.path.join(root, f)) for f in video_files]

# folder_video_map now contains the folder names as keys and lists of file paths as values

# --- Upload each file ---
for folder_name, video_list in folder_video_map.items():
    for videoPath in video_list:
        print(f"Uploading file (absolute path): {videoPath}")

        # Refresh the page before each upload (optional, depends on the site)
        driver.get(UPLOAD_URL)
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


        # Scroll until no more new content
        last_height = 0
        while True:
            # Scroll to bottom
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", text_area)

            # Wait for content to load
            time.sleep(1)

            # Get the new height
            new_height = driver.execute_script("return arguments[0].scrollHeight", text_area)

            if new_height == last_height:
                break

            last_height = new_height

        print("Finished scrolling!")

        # Save the HTML output
        # At this point, all paragraphs should be loaded
        text_area_HTML = text_area.get_attribute("innerHTML")

        html_filename = os.path.join(OUTPUT_FOLDER +"/" + folder_name, f"{os.path.splitext(videoPath)[0]}.html")
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(text_area_HTML)

        print(f"Saved HTML to {html_filename}\n")

# --- Cleanup ---
driver.quit()
print("All done!")









