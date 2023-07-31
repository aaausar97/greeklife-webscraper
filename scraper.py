from helper import constants, gsheet_helper, post_helper
from instaloader import Instaloader, Profile, exceptions, RateController, ConnectionException
import gspread
import random
import time
import os

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD

class MyRateController(RateController):
    def sleep(self, secs: float):
        rand = float(constants.BASE + random.randint(0, constants.RAND))
        return super().sleep(secs + rand)
    def handle_429(self, query_type: str) -> None:
        print('hit 429')
        return super().handle_429(query_type)

### -- start clients --

L = Instaloader(sanitize_paths=True, 
                rate_controller=lambda ctx: MyRateController(ctx), 
                fatal_status_codes=['302'],
                iphone_support=False,
                download_videos=False,
                max_connection_attempts=1,
                request_timeout=1800,
            )
sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions

### -- helper functions --

def login_to_insta():
    cwd = os.path.dirname()
    session_filepath = os.path.join(cwd, f'session-{USERNAME}')
    print(USERNAME, PASSWORD)
    if not os.path.exists(session_filepath):
        L.login(USERNAME, PASSWORD)
        L.save_session_to_file(filename=session_filepath)
    else:
        L.load_session_from_file(username=USERNAME, filename=session_filepath)


### ----- main() ----- 

def main():
    sheet = sheets_client.open_by_url(constants.SHEET_URL)  
    gsheet_helper.ready_gsheet(sheet=sheet)
    login_to_insta()

    usernames = gsheet_helper.get_usernames_from_sheets(sheet=sheet)
    for username in usernames: 
        if username == '':
            continue     

        try:
            profile = Profile.from_username(L.context, username)
        except Exception as e:
            print(f'error: {e}')
            continue
        time.sleep(float(constants.BASE) + random.randint(0, 15))
        try:
            posts = profile.get_posts()
        except Exception as e:
            print(f'error: {e}')
            continue
        print(f'scraping {username}')
        rows_to_append = post_helper.scrape_posts(posts=posts)
        gsheet_helper.send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
        print('sheet updated\n')
        time.sleep(float(constants.BASE + constants.RAND))
    print('scraping complete')

if __name__ == "__main__":
    main()