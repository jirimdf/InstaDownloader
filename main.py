import argparse
import os
import sys
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SITE_URL = "https://fastdl.app/en/story-saver"
TIMEOUT = 20
LINKS_FILE = "downloaded_links.txt"
LOG_FILE = "task.txt"


def build_parser():
    parser = argparse.ArgumentParser(description="Download Instagram stories of a public account.")
    parser.add_argument("username", help="Instagram username of a public account")
    parser.add_argument("-f", "--folder", default="downloads",
                        help="Folder where the stories are saved (default: ./downloads)")
    parser.add_argument("--show-browser", action="store_true", help="Show the Chrome window (useful for debugging)")
    return parser


def extension_for(content_type):
    """Return the file extension for a Content-Type header, or None for anything else."""
    content_type = (content_type or "").lower()
    if content_type.startswith("image/"):
        return "jpg"
    if content_type.startswith("video/"):
        return "mp4"
    return None


def link_key(url):
    # The signature in a download link changes on every run, the "filename" parameter identifies the story
    filename = parse_qs(urlparse(url).query).get("filename")
    return filename[0] if filename else url


def load_downloaded_links(download_folder):
    path = os.path.join(download_folder, LINKS_FILE)
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {link_key(line.strip()) for line in f if line.strip()}


def record_downloaded_link(download_url, download_folder):
    with open(os.path.join(download_folder, LINKS_FILE), "a", encoding="utf-8") as f:
        f.write(download_url + "\n")


def build_filename(stories_folder, username, index, extension):
    download_date = datetime.now().strftime("%d%m%Y")
    base = f"jirimdf_Downloader_{username}_{download_date}_{index}"
    filename = os.path.join(stories_folder, f"{base}.{extension}")
    # Don't overwrite a story downloaded earlier on the same day
    counter = 2
    while os.path.exists(filename):
        filename = os.path.join(stories_folder, f"{base}_{counter}.{extension}")
        counter += 1
    return filename


def js_click(driver, element):
    # A JavaScript click is not blocked by ads or overlays covering the element
    driver.execute_script("arguments[0].click();", element)


def remove_overlays(driver):
    """Hide the cookie dialog and ad popups without accepting anything."""
    driver.execute_script("""
        document.querySelectorAll('.fc-consent-root, .ads-modal').forEach(e => e.remove());
        document.body.style.overflow = 'auto';
    """)


def find_story_links(driver, username):
    wait = WebDriverWait(driver, TIMEOUT)
    driver.get(SITE_URL)

    search_input = wait.until(EC.presence_of_element_located((By.ID, "search-form-input")))
    time.sleep(3)  # The cookie dialog appears a moment after the page loads
    remove_overlays(driver)
    search_input.send_keys(username)
    js_click(driver, driver.find_element(By.CSS_SELECTOR, ".search-form__button"))
    print(f"Searching for {username}...")

    tabs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tabs-component__item button")))
    time.sleep(5)
    remove_overlays(driver)

    # Reading body.text through WebDriver fails on large pages, so the check runs in JavaScript
    is_private = driver.execute_script(
        "return document.body.innerText.toLowerCase().includes('private account');")
    if is_private:
        raise RuntimeError(f"{username} is a private account. Only public accounts are supported.")

    stories_tab = next((t for t in tabs if t.get_attribute("textContent").strip().lower() == "stories"), None)
    if stories_tab is None:
        raise RuntimeError("Could not find the Stories tab. The website has probably changed.")
    js_click(driver, stories_tab)
    print("Opened the Stories tab.")
    time.sleep(5)

    # Load all stories
    for _ in range(50):
        see_more = driver.find_elements(By.CSS_SELECTOR, ".button--see-more")
        if not see_more:
            break
        js_click(driver, see_more[0])
        time.sleep(2)

    links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a.button--filled")]
    return [link for link in links if link]


def download_stories(links, username, download_folder):
    stories_folder = os.path.join(download_folder, "Stories")
    os.makedirs(stories_folder, exist_ok=True)
    downloaded = load_downloaded_links(download_folder)
    count = 0

    for index, url in enumerate(links, start=1):
        if link_key(url) in downloaded:
            print(f"Story {index} already downloaded, skipping.")
            continue

        response = requests.get(url, timeout=60)
        response.raise_for_status()
        extension = extension_for(response.headers.get("content-type"))
        if extension is None:
            print(f"Story {index} has an unknown content type, skipping.")
            continue

        filename = build_filename(stories_folder, username, index, extension)
        with open(filename, "wb") as file:
            file.write(response.content)
        record_downloaded_link(url, download_folder)
        downloaded.add(link_key(url))
        count += 1
        print(f"Downloaded story {index} to {filename}")

    return count


def get_instagram_stories(username, download_folder, show_browser=False):
    options = webdriver.ChromeOptions()
    if not show_browser:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    driver = webdriver.Chrome(options=options)

    try:
        links = find_story_links(driver, username)
    finally:
        driver.quit()

    if not links:
        print(f"{username} has no active stories right now.")
        return 0

    print(f"Found {len(links)} stories.")
    return download_stories(links, username, download_folder)


def main(argv=None):
    args = build_parser().parse_args(argv)
    username = args.username.strip().lstrip("@")
    os.makedirs(args.folder, exist_ok=True)

    with open(os.path.join(args.folder, LOG_FILE), "a", encoding="utf-8") as log:
        log.write(f"{datetime.now()} - The script ran for {username}\n")

    try:
        count = get_instagram_stories(username, args.folder, args.show_browser)
    except TimeoutException:
        print("The website did not respond in time or its layout has changed.")
        return 1
    except (RuntimeError, WebDriverException, requests.RequestException) as e:
        print(f"Error: {e}")
        return 1

    print(f"Done: {count} new stories downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
