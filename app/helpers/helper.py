from datetime import datetime, timedelta
from itertools import chain, takewhile
from PIL import Image
from .weekly_batch import Batches
import io
import json
import pytesseract
import re
import requests
import os
import time


with open('config.json', 'r') as f:
    config = json.load(f)

## -- CONSTANTS AND CONFIGS --
class constants:
    SINCE = datetime.now()
    UNTIL = SINCE - timedelta(days=config["util"]["days_to_scrape"])
    BASE = config["util"]["base_wait_time"]
    RAND = config["util"]["base_rand_time"]

    SHEET_URL = config["google_drive"]["sheet_url"]
    range_to_append = 'A1:G1'

    USERNAME = config["instagram"]["username"]
    PASSWORD = config["instagram"]["password"]

    BACKEND_URL = config["backend"]["url"]
    BACKEND_USERNAME = config["backend"].get("username")
    BACKEND_PASSWORD = config["backend"].get("password")
    BACKEND_AUTH_TYPE = config["backend"].get("auth_type", "basic")  # "basic" or "bearer"
    BACKEND_TOKEN = config["backend"].get("token")  # used when auth_type == "bearer"
    BACKEND_LOGIN_PATH = config["backend"].get("login_path")  # optional: path to obtain token with {username,password}
    
    EMAIL_REGEX = r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+'
    PHONE_REGEX = r'\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})'
    TAGGED_REGEX = r'\B@[\w\.-]+'


class gsheet_helper:
    def ready_gsheet(sheet):
        worksheet = sheet.get_worksheet(0)
        number_of_rows = worksheet.row_count
        worksheet.batch_clear([f'A2:M{number_of_rows+1}'])

    def send_data_to_sheets(rows_to_append, sheet):
        worksheet = sheet.get_worksheet(0)
        worksheet.append_rows(values=rows_to_append, 
                            value_input_option='USER_ENTERED', 
                            insert_data_option='INSERT_ROWS', 
                            table_range=constants.range_to_append)
        
    def get_usernames_from_sheets(sheet):
        batches = Batches()
        batches_list = batches.batches
        batches_list = batches.batch_profiles_from_list(sheet)
        batch_to_run = batches_list[batches.batch_emerg]
        if batches.num_batch_to_run:
            batch_to_run = batches_list[batches.num_batch_to_run]
        return batch_to_run

    def get_found_profiles(sheet):
        worksheet = sheet.get_worksheet(0)
        profiles = worksheet.get_values('B2:B')
        found_profiles_list = list(chain(*profiles))
        return found_profiles_list

class text_helper:
    def get_phones(caption, image_text=None):
        caption = caption.replace(' ', '').strip()
        phones = re.findall(constants.PHONE_REGEX, caption)
        if image_text:
            phones_img = re.findall(constants.PHONE_REGEX, image_text)
            phones.extend(phones_img)

        all_phones = ''

        for phone in phones:
            all_phones += f'{phone}\n'

        return all_phones

    def extract_text_from_image(url_to_image):
        session = requests.Session()
        # Minimal retries and error handling; no extra config
        for _ in range(3):
            try:
                response = session.get(url_to_image, timeout=10)
                img = Image.open(io.BytesIO(response.content))
                text = pytesseract.image_to_string(img)
                text = text.strip()
                return text
            except Exception:
                time.sleep(1)
                continue
        return ""

class post_helper:
    def scrape_video(post):
        post_shortcode = post.shortcode
        post_url = f'https://instagram.com/p/{post_shortcode}/'
        post_profile = post.owner_profile
        profile_full_name, profile_username = post_profile.full_name, post_profile.username
        post_caption = post.caption if post.caption else ""
        post_thumbnail_url = post.url
        post_video_url = post.video_url
        image_text = text_helper.extract_text_from_image(post_thumbnail_url)
        phone = text_helper.get_phones(caption=post_caption, image_text=image_text)
        raw_content = f"{post_caption}\n{image_text}".strip()
        values_to_append = [post.date_local, 
                            profile_username, 
                            profile_full_name, 
                            phone, 
                            '',
                            '',
                            post_caption, 
                            image_text,
                            post_url, 
                            post_thumbnail_url,
                            '',
                            raw_content]
        if not phone:
            return None
        return values_to_append

    def scrape_pic(post):
        post_shortcode = post.shortcode
        post_url = f'https://instagram.com/p/{post_shortcode}/'
        post_profile = post.owner_profile
        profile_full_name, profile_username = post_profile.full_name, post_profile.username
        post_caption = post.caption if post.caption else ""
        post_pic_url = post.url
        image_text = text_helper.extract_text_from_image(post_pic_url)
        phone = text_helper.get_phones(caption=post_caption, image_text=image_text)
        raw_content = f"{post_caption}\n{image_text}".strip()
        values_to_append = [post.date_local, 
                            profile_username, 
                            profile_full_name, 
                            phone, 
                            '', 
                            '', 
                            post_caption, 
                            image_text,
                            post_url, 
                            post_pic_url,
                            '',
                            raw_content]   
        if not phone:
            return None
        return values_to_append

    def scrape_posts(posts):
        rows_to_append = []
        try:
            for post in takewhile(lambda p: p.date_utc >= constants.UNTIL, posts):
                print(post)
                if post.is_video:
                    row_to_append = post_helper.scrape_video(post)
                else:
                    row_to_append = post_helper.scrape_pic(post)
                if row_to_append:
                    rows_to_append.append(row_to_append)
        except Exception:
            # swallow pagination/iteration errors and continue
            pass
        return rows_to_append


