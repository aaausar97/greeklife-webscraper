from datetime import datetime, timedelta
from instaloader import Instaloader, Profile, exceptions, RateController
from itertools import chain, takewhile
from PIL import Image
import gspread
import io
import json
import pytesseract
import re
import requests
import time
import random

with open('config.json', 'r') as f:
    config = json.load(f)

## -- CONSTANTS AND CONFIGS --

SINCE = datetime.now()
UNTIL = SINCE - timedelta(days=config["util"]["days_to_scrape"])
BASE = config["util"]["base_wait_time"]
RAND = config["util"]["base_rand_time"]

SHEET_URL = config["google_drive"]["sheet_url"]
range_to_append = 'A1:G1'

USERNAME = config["instagram"]["username"]
PASSWORD = config["instagram"]["password"]

EMAIL_REGEX = r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+'
PHONE_REGEX = r'\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})'
TAGGED_REGEX = r'\B@[\w\.-]+'


class MyRateController(RateController):
    def sleep(self, secs: float):
        return super().sleep(secs)
    def handle_429(self, query_type: str) -> None:
        print('hit 429; trying again later')
        return super().handle_429(query_type)
    def query_waittime(self, query_type: str, current_time: float, untracked_queries: bool = False) -> float:
        return super().query_waittime(query_type, current_time, untracked_queries) + BASE + random.randint(0,RAND)
    def wait_before_query(self, query_type: str) -> None:
        return super().wait_before_query(query_type)
    
### -- start clients --

L = Instaloader(rate_controller=lambda ctx: MyRateController(ctx)) #instaloder client for scraping w/ rate controller context
sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions

### -- helper functions --

def login_to_insta(username, password):
    try:
        L.load_session_from_file(filename=username)
    except:
        L.login(user=username, passwd=password)
        L.save_session_to_file(filename=username)

def ready_gsheet(sheet):
    worksheet = sheet.get_worksheet(0)
    number_of_rows = worksheet.row_count
    worksheet.batch_clear([f'A2:M{number_of_rows+1}'])

def get_usernames_from_sheets(sheet):
    prefix = 'https://www.instagram.com/'
    formated_profile_list = []
    for n in range(1,6): # update to use worksheet name
        worksheet = sheet.get_worksheet(n)
        profiles = worksheet.get_values('A:A')
        profiles_list = list(chain(*profiles))
        for profile in profiles_list:
            formated_profile_list.append(profile[len(prefix):].rstrip('/')) #extract username from URLs
    return formated_profile_list

def get_phones_emails_and_tags(caption, image_text=None):
    caption = caption.replace(' ', '').strip()
    emails = re.findall(EMAIL_REGEX, caption)
    phones = re.findall(PHONE_REGEX, caption)
    tagged = re.findall(TAGGED_REGEX, caption)
    if image_text:
        emails_img = re.findall(EMAIL_REGEX, image_text)
        phones_img = re.findall(PHONE_REGEX, image_text) #expand regex for phone numbers
        tagged_img = re.findall(TAGGED_REGEX, image_text)
        emails.extend(emails_img)
        phones.extend(phones_img)
        tagged.extend(tagged_img)

    all_emails = ''
    all_phones = ''
    all_tagged = ''
    for email in emails:
        all_emails += f'{email}\n'
    for phone in phones:
        all_phones += f'{phone}\n'
    for tag in tagged:
        all_tagged += f'{tag}\n'

    return (all_emails, all_phones, all_tagged)

def extract_text_from_image(url_to_image):
    response = requests.get(url_to_image)
    img = Image.open(io.BytesIO(response.content))
    text = pytesseract.image_to_string(img)
    text = text.replace(" ", "")
    text = text.strip()
    return text

def scrape_video(post):
    post_shortcode = post.shortcode
    post_url = f'https://instagram.com/p/{post_shortcode}/'
    post_profile = post.owner_profile
    profile_full_name, profile_username = post_profile.full_name, post_profile.username
    post_caption = post.caption if post.caption else ""
    post_thumbnail_url = post.url
    post_video_url = post.video_url
    image_text = extract_text_from_image(post_thumbnail_url)
    email, phone, tagged = get_phones_emails_and_tags(caption=post_caption, image_text=image_text)
    values_to_append = [str(post.date_local), 
                        str(profile_username), 
                        str(profile_full_name), 
                        str(phone), 
                        str(email), 
                        str(tagged), 
                        str(post_caption), 
                        str(image_text),
                        str(post_url), 
                        str(post_video_url)]
    if not email and not phone and not tagged:
        return None
    return values_to_append

def scrape_pic(post):
    post_shortcode = post.shortcode
    post_url = f'https://instagram.com/p/{post_shortcode}/'
    post_profile = post.owner_profile
    profile_full_name, profile_username = post_profile.full_name, post_profile.username
    post_caption = post.caption if post.caption else ""
    post_pic_url = post.url
    image_text = extract_text_from_image(post_pic_url)
    email, phone, tagged = get_phones_emails_and_tags(caption=post_caption, image_text=image_text)
    values_to_append = [str(post.date_local), 
                        str(profile_username), 
                        str(profile_full_name), 
                        str(phone), 
                        str(email), 
                        str(tagged), 
                        str(post_caption), 
                        str(image_text),
                        str(post_url), 
                        str(post_pic_url)]   
    if not email and not phone and not tagged:
        return None
    return values_to_append

def scrape_posts(posts):
    rows_to_append = []
    for post in takewhile(lambda p: p.date_utc >= UNTIL, posts):
        print(post)
        if post.is_video:
            row_to_append = scrape_video(post)
        else:
            row_to_append = scrape_pic(post)
        if row_to_append:
            rows_to_append.append(row_to_append)
    return rows_to_append

def send_data_to_sheets(rows_to_append, sheet):
    worksheet = sheet.get_worksheet(0)
    worksheet.append_rows(values=rows_to_append, 
                          value_input_option='USER_ENTERED', 
                          insert_data_option='INSERT_ROWS', 
                          table_range=range_to_append)


## -- old utils --

# RATE LIMITING: instagram API rate limits are 200 requests/hr
# Scraper will handle rate limiting itself, as long as its the only run
# and there was enough time between runs. Scrapper assumes there have been no other
# instances of the application being run or API hits on other devices

def wait():
    wait = BASE + random.randint(0,RAND)
    print(f'waiting {wait} seconds until next scrape')
    time.sleep(wait) # short pause between profiles
    return

def stall():
    print(f'waiting {STALL} seconds until next scrape')
    time.sleep(STALL) # short stall after scraping multiple profile
    return

### ----- main() ----- 

def main():
    sheet = sheets_client.open_by_url(SHEET_URL)  
    login_to_insta(username=USERNAME, password=PASSWORD)
    ready_gsheet(sheet=sheet)  
    usernames = get_usernames_from_sheets(sheet=sheet)
    for username in usernames: 
        if username == '':
            continue     

        try:
            posts = Profile.from_username(L.context, username).get_posts()
        except exceptions.ProfileNotExistsException:
            continue
        
        print(f'scraping {username}\n')
        rows_to_append = scrape_posts(posts=posts)
        send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
    print('scraping complete')

if __name__ == "__main__":
    main()