from helpers import helper
from helpers.proxies import ProxyContext
from instaloader import Instaloader, Profile
from instaloader.exceptions import ProfileNotExistsException, TooManyRequestsException, ConnectionException, LoginRequiredException
import datetime, gspread, logging, os, random, time

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

def read_usernames(filename):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        usernames = read_file(filepath)
        return usernames
    else:
        create_file(filepath)
        return []

def read_file(filepath):
    with open(filepath) as f:
        usernames_raw = f.readlines()
        usernames = list(map(lambda username: username.strip(), usernames_raw))
        logging.info('read usernames.txt')
        return usernames

def create_file(filepath):
    with open(filepath, 'a+') as file:
        file.seek(0)
        logging.info('created usernames.txt')
        return 
    
def delete_search_file(filename):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        logging.info(f"{filename} has been deleted.")
    else:
        logging.info("searched file doesnt exist")

def save_username(username):
    with open(os.path.join(os.getcwd(), 'usernames.txt'), 'a+') as f:
        f.write(f'{username}\n')
        return

def cleaned_usernames(searched, to_search):
    searched_set = set(searched)
    to_search_set = set(to_search)
    res = list(to_search_set-searched_set)
    random.shuffle(res)
    return res

def login_to_insta():
    try:
        L.load_session_from_file(username=USERNAME)
    except Exception as e:
        logging.error(f'error: {e}')
        raise e

def wait(k):
    post_scrape_wait = helper.constants.BASE + random.randint(1, helper.constants.RAND) + min(random.expovariate(0.6), 15)
    if k%50 == 0: post_scrape_wait = random.randint(5, 10)*60
    elif k%30 == 0: post_scrape_wait = random.randint(1, 3)*60
    print(f'waiting {post_scrape_wait} seconds before next scrape')
    time.sleep(post_scrape_wait)   
    return

def get_profiles_to_search(sheet):
    to_search = helper.gsheet_helper.get_usernames_from_sheets(sheet=sheet)
    prev_search = read_usernames('usernames.txt')
    search = cleaned_usernames(prev_search, to_search)
    logging.info(f'searched: {len(prev_search)}')
    logging.info(f'batch: {search}, {len(search)}')
    return search

def scrape_profiles(search, sheet):
    for index, username in enumerate(search, start=1):
        if username == '': continue
        try:
            with ProxyContext():
                print(f'scraping {username}:{index}')
                profile = Profile.from_username(L.context, username)
                posts = profile.get_posts()
        except ProfileNotExistsException:
            print(f"Profile {username} does not exist.")
            continue
        except TooManyRequestsException as e:
            search.append(username)
            time.sleep(1)
            continue
        except ConnectionException as e:
            if "HTTP error code 401" in str(e):
                print(f"401: Profile {username} not found.")
                continue
            print(f"Connection Error: {e}")
            search.append(username)
            time.sleep(1)
            continue
        except LoginRequiredException as e:
            print(f"Login Required Error: {e}")
            search.append(username)
            time.sleep(1)
            continue
        except Exception as e:
            print(f"Other Error: {e}")
            search.append(username)
            wait(index)
            continue
        logging.info(f'scraped {username}:{index}')
        rows_to_append = helper.post_helper.scrape_posts(posts=posts)
        update_gsheet(rows_to_append=rows_to_append, sheet=sheet)
        save_username(username)
        #wait(index)

def update_gsheet(rows_to_append, sheet):
     if rows_to_append:
            helper.gsheet_helper.send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
            print('sheet updated')
            logging.info('sheet updated')

### ----- main() ----- 

def main():
    sheet = sheets_client.open_by_url(helper.constants.SHEET_URL)
    #gsheet_helper.ready_gsheet(sheet=sheet)
    search = get_profiles_to_search(sheet)
    print('scraping')
    scrape_profiles(search=search, sheet=sheet)
    print('scraping complete')
    delete_search_file('usernames.txt')
    logging.info('scraping complete')

if __name__ == "__main__":
    main()