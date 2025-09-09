import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time

def get_instagram_stories(username, download_folder):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    driver.get("https://fastdl.app/")

    try:
        # Cookies consent
        print("Waiting for cookies button...")
        cookies_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Consent']"))
        )
        cookies_button.click()
        print("Cookies button clicked.")

        # Username input
        print("Waiting for username input...")
        url_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='search-form-input']"))
        )
        url_input.send_keys(f"{username}")
        print("Username entered.")

        # Download button
        print("Waiting for download button...")
        download_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[@class='search-form__button']"))
        )
        download_button.click()
        print("Download button clicked.")

        # Remove popup ad if it appears
        try:
            print("Removing popup ad...")
            popup_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ads-modal"))
            )
            driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, popup_element)
            print("Popup ad removed.")
        except Exception as e:
            print("No popup ad detected or an error occurred:", e)

        time.sleep(6)

        # Click the "Stories" tab
        try:
            print("Waiting for 'Stories' tab...")
            stories_tab = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//li[@class='tabs-component__item']/button[contains(text(), 'stories')]"))
            )
            stories_tab.click()
            print("'Stories' tab clicked.")
        except Exception as e:
            print("An error occurred while trying to click the 'Stories' tab:", e)
            return False

        # Click "See more" buttons until they no longer appear
        while True:
            try:
                see_more_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@class='button button--see-more profile-media-list__button--see-more']"))
                )
                see_more_button.click()
                print("See more button clicked.")
                time.sleep(2)  # Wait for new content to load
            except:
                print("No more 'See more' buttons.")
                break

        # Wait for download buttons to become clickable
        print("Waiting for download buttons to become clickable...")
        download_buttons = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.button--filled"))
        )
        print(f"Found {len(download_buttons)} download buttons.")

        # Downloading stories
        for index, download_button in enumerate(download_buttons):
            download_url = download_button.get_attribute("href")
            response = requests.head(download_url)
            content_type = response.headers.get('content-type')

            if 'image' in content_type:
                extension = "jpg"
            elif 'video' in content_type:
                extension = "mp4"
            else:
                print(f"Unknown content type: {content_type}. Skipping download.")
                continue

            download_date = datetime.now().strftime("%d%m%Y")
            filename = os.path.join(download_folder, "Stories", f"jirimdf_Downloader_{username}_{download_date}_{index + 1}.{extension}")

            if not is_already_downloaded(download_url, download_folder):
                print(f"Downloading {download_url} to {filename}...")
                response = requests.get(download_url)
                with open(filename, 'wb') as file:
                    file.write(response.content)
                record_downloaded_link(download_url, download_folder)
                print(f"Downloaded {download_url}.")
            else:
                print(f"Link already downloaded: {download_url}")

    except Exception as e:
        print("An error occurred:", e)
        return False

    finally:
        driver.quit()

def is_already_downloaded(download_url, download_folder):
    downloaded_links_file = os.path.join(download_folder, "downloaded_links.txt")
    if os.path.exists(downloaded_links_file):
        with open(downloaded_links_file, "r") as f:
            existing_links = [line.strip().split('&')[0] for line in f.readlines()]
            return download_url.split('&')[0] in existing_links
    return False

def record_downloaded_link(download_url, download_folder):
    downloaded_links_file = os.path.join(download_folder, "downloaded_links.txt")
    with open(downloaded_links_file, "a") as f:
        f.write(download_url + "\n")

def run_script():
    ######################################################################
    # Folder
    download_folder = r"(YOUR FOLDER PATH)"
    # Example = r"C:\Users\PC\Downloads\InstaDownloader\"
    # Example = r"/home/kali/Downloads/InstaDownloader/"
    # User id
    username = "jiri_mdf"
    ######################################################################

    stories_folder = os.path.join(download_folder, "Stories")
    if not os.path.exists(stories_folder):
        os.makedirs(stories_folder)

    downloaded_links_file = os.path.join(download_folder, "downloaded_links.txt")
    if not os.path.exists(downloaded_links_file):
        with open(downloaded_links_file, "w"):
            pass

    task_file_path = os.path.join(download_folder, 'task.txt')
    with open(task_file_path, 'a') as task_file:
        task_file.write(f'{datetime.now()} - The script ran\n')

    if not get_instagram_stories(username, download_folder):
        return False

run_script()

