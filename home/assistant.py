import re
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube, exceptions as pytube_exceptions
from selenium.webdriver.common.by import By
import requests

def initialize_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--profile-directory=Default')
    options.add_argument('--user-data-dir=/root/MyPersonalBot/chrome/')
    return webdriver.Chrome(options=options)

def is_instagram(url) -> bool:
    instagram_pattern = r"https?://(?:www\.)?instagram\.com/reel/.*"
    return bool(re.match(instagram_pattern, url))

def is_youtube(url) -> bool:
    youtube_pattern = r"(?:https?:\/\/)?(?:www\.)?youtu(?:\.be\/|be.com\/\S*(?:watch|embed|shorts)(?:(?:(?=\/[-a-zA-Z0-9_]{11,}(?!\S))\/)|(?:\S*v=|v\/)))([-a-zA-Z0-9_]{11,})"
    return bool(re.match(youtube_pattern, url))

def download_video(url, driver, youtube_api_key=None) -> bytes:
    if is_instagram(url):
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        element = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
        reel_source = element.get_attribute('src')
        return requests.get(reel_source).content
    elif is_youtube(url):
        try:
            youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            video_id = YouTube(url).video_id
            request = youtube.videos().list(part='contentDetails', id=video_id)
            response = request.execute()
            duration = response['items'][0]['contentDetails']['duration']
            if 'PT' in duration:
                video_stream = YouTube(url).streams.filter(file_extension='mp4').first()
                return requests.get(video_stream.url).content
            else:
                raise ValueError("Qo'llab-quvvatlanmaydigan video davomiyligi")
        except HttpError as e:
            if e.resp.status == 403 and 'ageRestricted' in str(e):
                raise pytube_exceptions.AgeRestrictedError(video_id)
            else:
                raise
    else:
        raise ValueError("Qo'llab-quvvatlanmaydigan video platformasi")
