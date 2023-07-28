from helper import constants, gsheet_helper, post_helper
from instaloader import Instaloader, Profile, exceptions, RateController, ConnectionException
import gspread
import random
import json
from argparse import ArgumentParser
from glob import glob
from os.path import expanduser
from platform import system
from sqlite3 import OperationalError, connect

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD

class MyRateController(RateController):
    def sleep(self, secs: float):
        return super().sleep(secs)
    def handle_429(self, query_type: str) -> None:
        print('hit 429; trying again later')
        return super().handle_429(query_type)
    def query_waittime(self, query_type: str, current_time: float, untracked_queries: bool = False) -> float:
        return super().query_waittime(query_type, current_time, untracked_queries) + constants.BASE + random.randint(0, constants.RAND)
    def wait_before_query(self, query_type: str) -> None:
        return super().wait_before_query(query_type)

### -- start clients --

L = Instaloader(rate_controller=lambda ctx: MyRateController(ctx)) #instaloder client for scraping w/ rate controller context
sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions

### -- helper functions --

def login_to_insta(username, args):
    try:
        L.load_session_from_file(filename=username)
    except:
        try:
            import_session(args.cookiefile or get_cookiefile(), args.sessionfile)
        except (ConnectionException, OperationalError) as e:
            raise SystemExit("Cookie import failed: {}".format(e))

def get_cookiefile():
    default_cookiefile = {
        "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
        "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
    }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
    cookiefiles = glob(expanduser(default_cookiefile))
    if not cookiefiles:
        raise SystemExit("No Firefox cookies.sqlite file found. Use -c COOKIEFILE.")
    return cookiefiles[0]

def import_session(cookiefile, sessionfile):
    print("Using cookies from {}.".format(cookiefile))
    conn = connect(f"file:{cookiefile}?immutable=1", uri=True)
    try:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'"
        )
    except OperationalError:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'"
        )
    L.context._session.cookies.update(cookie_data)
    username = L.test_login()
    if not username:
        raise SystemExit("Not logged in. Are you logged in successfully in Firefox?")
    print("Imported session cookie for {}.".format(username))
    L.context.username = username
    L.save_session_to_file(sessionfile)

### ----- main() ----- 

def main():
    print(USERNAME, PASSWORD)
    p = ArgumentParser()
    p.add_argument("-c", "--cookiefile")
    p.add_argument("-f", "--sessionfile")
    args = p.parse_args()

    sheet = sheets_client.open_by_url(constants.SHEET_URL)  
    gsheet_helper.ready_gsheet(sheet=sheet)
    login_to_insta(username=USERNAME, args=args)

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