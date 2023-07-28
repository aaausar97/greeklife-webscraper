from helper import constants, gsheet_helper, post_helper
from instaloader import Instaloader, Profile, exceptions, RateController, ConnectionException
import gspread

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD

class MyRateController(RateController):
    def sleep(self, secs: float):
        return super().sleep(secs)
    def handle_429(self, query_type: str) -> None:
        print('hit 429; trying again later')
        return super().handle_429(query_type)
    def query_waittime(self, query_type: str, current_time: float, untracked_queries: bool = False) -> float:
        return super().query_waittime(query_type, current_time, untracked_queries)
    def wait_before_query(self, query_type: str) -> None:
        return super().wait_before_query(query_type)

### -- start clients --

L = Instaloader(rate_controller=lambda ctx: MyRateController(ctx)) #instaloder client for scraping w/ rate controller context
sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions

### -- helper functions --

def login_to_insta():
    print(USERNAME, PASSWORD)
    try:
        L.load_session_from_file(username=USERNAME, filename=USERNAME)
    except Exception as e:
        L.login(USERNAME, PASSWORD)
        L.save_session_to_file(filename=USERNAME)

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
            posts = Profile.from_username(L.context, username).get_posts()
        except exceptions.ProfileNotExistsException:
            continue
        
        print(f'scraping {username}\n')
        rows_to_append = post_helper.scrape_posts(posts=posts)
        gsheet_helper.send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
    print('scraping complete')

if __name__ == "__main__":
    main()