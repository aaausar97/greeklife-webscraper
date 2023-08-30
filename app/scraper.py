from helpers import helper
from instaloader import Instaloader, Profile
import gspread
import logging
import os
import random
import time

USERNAME = helper.constants.USERNAME
PASSWORD = helper.constants.PASSWORD

### -- start clients --

L = Instaloader(
                sleep=True,
                sanitize_paths=True, 
                iphone_support=False,
                download_videos=False,
                max_connection_attempts=1,
            )

sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions

logging.basicConfig(filename='scraper.log', 
                    filemode='w', # overwrite log file
                    level=logging.INFO, 
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p'
                )

### -- helper functions --

def login_to_insta():
    cwd = os.getcwd()
    session_filepath = os.path.join(cwd, f'session-{USERNAME}')
    try:
        if not os.path.exists(session_filepath):
            L.login(USERNAME, PASSWORD)
            L.save_session_to_file(filename=session_filepath)
        else:
            L.load_session_from_file(username=USERNAME, filename=session_filepath)
        logging.info('logged in')
    except Exception as e:
        logging.error('login failed: {}'.format(e))
        raise e
    
def login_to_insta_2():
    try:
        L.load_session_from_file(username=USERNAME)
    except Exception as e:
        logging.error('login failed: {}'.format(e))
        raise e

def refresh_session():
    session_filepath = os.path.join(os.getcwd(), f'session-{USERNAME}')
    L.login(USERNAME, PASSWORD)
    L.save_session_to_file(filename=session_filepath)

def handle_logout():
    delay = 1800
    logging.info('logged out, logging in after {} seconds'.format(delay))
    time.sleep(delay)
    refresh_session()

def post_100_wait():
    delay = random.randint(15, 30)*60
    print('hit 100 scrapes: waiting {} seconds before next scrape'.format(delay))  
    time.sleep(delay)

def post_250_wait():
    delay = random.randint(45, 60)*60
    print('hit 250 scrapes: waiting {} seconds before next scrape'.format(delay))
    time.sleep(delay)

def post_500_wait():
    delay = random.randint(1,3)*45*60
    print('hit 500 scrapes: waiting {} seconds before next scrape'.format(delay))
    time.sleep(delay)

def wait(k):
    post_scrape_wait = helper.constants.BASE + random.randint(1, helper.constants.RAND) + min(random.expovariate(0.6), 15)
    wait_time = post_scrape_wait + random.randint(1, k*2)
    if k%50 == 0: post_500_wait()
    elif k%30 == 0: post_250_wait()
    elif k%20 == 0: post_100_wait()
    else:
        print(f'waiting {wait_time} seconds before next scrape')
        time.sleep(wait_time)    
    return
### ----- main() ----- 

def main():
    sheet = sheets_client.open_by_url(helper.constants.SHEET_URL)
    #gsheet_helper.ready_gsheet(sheet=sheet)
    search = helper.gsheet_helper.get_usernames_from_sheets(sheet=sheet)
    random.shuffle(search)
    login_to_insta_2()
    logging.info(f'batch to run: {search}')
    logging.info('scraping')
    k=1
    for username in search:
        if username == '': continue
        wait(k)
        k+=1
        try:
            profile = Profile.from_username(L.context, username)
        except Exception as e:
            logging.error(f'error: {e}')
            pass
        time.sleep(20)
        try:
            posts = profile.get_posts()
        except Exception as e:
            logging.error(f'error: {e}')
            pass
        logging.info(f'scraping {username}:{k}')
        rows_to_append = helper.post_helper.scrape_posts(posts=posts)
        helper.gsheet_helper.send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
        logging.info('sheet updated')
    print('scraping complete')
    logging.info('scraping complete')

if __name__ == "__main__":
    main()