from itertools import chain, takewhile
from datetime import datetime, timedelta
import re
import requests
import pytesseract
from PIL import Image
import io
import json


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
        prefix = 'https://www.instagram.com/'
        formated_profile_list = []
        for n in range(1,6): # update to use worksheet name
            worksheet = sheet.get_worksheet(n)
            profiles = worksheet.get_values('A:A')
            profiles_list = list(chain(*profiles))
            for profile in profiles_list:
                formated_profile_list.append(profile[len(prefix):].rstrip('/')) #extract username from URLs
        return formated_profile_list


class text_helper:
    def get_phones(caption, image_text=None):
        caption = caption.replace(' ', '').strip()
        phones = re.findall(constants.PHONE_REGEX, caption)
        #emails = re.findall(constants.EMAIL_REGEX, caption)
        #tagged = re.findall(constants.TAGGED_REGEX, caption)
        if image_text:
            phones_img = re.findall(constants.PHONE_REGEX, image_text) #expand regex for phone numbers
            phones.extend(phones_img)
            #emails_img = re.findall(constants.EMAIL_REGEX, image_text)
            #tagged_img = re.findall(constants.TAGGED_REGEX, image_text)
            #emails.extend(emails_img)
            #tagged.extend(tagged_img)

        all_phones = ''
        # all_emails = ''
        # all_tagged = ''

        for phone in phones:
            all_phones += f'{phone}\n'
        '''
        for email in emails:
            all_emails += f'{email}\n'
        for tag in tagged:
            all_tagged += f'{tag}\n'
        '''
        return all_phones

    def extract_text_from_image(url_to_image):
        response = requests.get(url_to_image)
        img = Image.open(io.BytesIO(response.content))
        text = pytesseract.image_to_string(img)
        text = text.replace(" ", "")
        text = text.strip()
        return text

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
        phone = text_helper.get_phones_emails_and_tags(caption=post_caption, image_text=image_text)
        values_to_append = [str(post.date_local), 
                            str(profile_username), 
                            str(profile_full_name), 
                            str(phone), 
                            '',
                            '',
                            str(post_caption), 
                            str(image_text),
                            str(post_url), 
                            str(post_video_url)]
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
        phone = text_helper.get_phones_emails_and_tags(caption=post_caption, image_text=image_text)
        values_to_append = [str(post.date_local), 
                            str(profile_username), 
                            str(profile_full_name), 
                            str(phone), 
                            '', 
                            '', 
                            str(post_caption), 
                            str(image_text),
                            str(post_url), 
                            str(post_pic_url)]   
        if not phone:
            return None
        return values_to_append

    def scrape_posts(posts):
        rows_to_append = []
        for post in takewhile(lambda p: p.date_utc >= constants.UNTIL, posts):
            print(post)
            if post.is_video:
                row_to_append = post_helper.scrape_video(post)
            else:
                row_to_append = post_helper.scrape_pic(post)
            if row_to_append:
                rows_to_append.append(row_to_append)
        return rows_to_append

