from helper import constants, gsheet_helper, post_helper
from instaloader import Instaloader, Profile
import gspread
import random
import time
import os

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD

### -- start clients --

L = Instaloader(
                sleep=True,
                sanitize_paths=True, 
                iphone_support=False,
                download_videos=False,
                max_connection_attempts=1,
            )
sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions

### -- helper functions --

def login_to_insta():
    cwd = os.getcwd()
    session_filepath = os.path.join(cwd, f'session-{USERNAME}')
    print(USERNAME, PASSWORD)
    if not os.path.exists(session_filepath):
        L.login(USERNAME, PASSWORD)
        L.save_session_to_file(filename=session_filepath)
    else:
        L.load_session_from_file(username=USERNAME, filename=session_filepath)

def refresh_session():
    session_filepath = os.path.join(os.getcwd(), f'session-{USERNAME}')
    L.login(USERNAME, PASSWORD)
    L.save_session_to_file(filename=session_filepath)

def handle_logout():
    delay = 1800
    print('logged out, logging in after {} seconds'.format(delay))
    time.sleep(delay)
    refresh_session()

### ----- main() ----- 

def main():
    sheet = sheets_client.open_by_url(constants.SHEET_URL)  
    gsheet_helper.ready_gsheet(sheet=sheet)
    print('sheet ready\n')
    login_to_insta()
    usernames = gsheet_helper.get_usernames_from_sheets(sheet=sheet)
    random.shuffle(usernames)
    print('scraping\n')
    k=0
    for username in usernames:
        if username == '': continue    
        if k%250 == 0: time.sleep(random.int(30, 45)*60)
        if k%500 == 0: time.sleep(60*60)
        k+=1
        try:
            profile = Profile.from_username(L.context, username)
        except Exception as e:
            print(f'error: {e}')
            continue

        try:
            posts = profile.get_posts()
        except Exception as e:
            print(f'error: {e}')
            continue

        print(f'scraping {username}:{k}')
        rows_to_append = post_helper.scrape_posts(posts=posts)
        gsheet_helper.send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
        print('sheet updated')

        post_scrape_wait = float(constants.BASE + min(random.expovariate(.6, constants.RAND)))
        print(f'waiting {post_scrape_wait} seconds before next scrape\n')
        time.sleep(post_scrape_wait)
    print('scraping complete')

if __name__ == "__main__":
    main()