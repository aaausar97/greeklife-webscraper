from helpers import helper
from instaloader import Instaloader, Profile, exceptions
import gspread, logging, os, random, sys, time

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

def post_15_wait():
    delay = random.randint(15, 30)*60
    print('hit 15 scrapes: waiting {} seconds before next scrape'.format(delay))  
    time.sleep(delay)

def post_30_wait():
    delay = random.randint(30, 45)*60
    print('hit 30 scrapes: waiting {} seconds before next scrape'.format(delay))
    time.sleep(delay)

def post_50_wait():
    delay = random.randint(1,3)*45*60
    print('hit 45 scrapes: waiting {} seconds before next scrape'.format(delay))
    time.sleep(delay)

def wait(k):
    post_scrape_wait = helper.constants.BASE + random.randint(1, helper.constants.RAND) + min(random.expovariate(0.6), 15)
    wait_time = post_scrape_wait + random.randint(1, k*2)
    if k%50 == 0: post_50_wait()
    elif k%30 == 0: post_30_wait()
    elif k%15 == 0: post_15_wait()
    else:
        print(f'waiting {wait_time} seconds before next scrape')
        time.sleep(wait_time)    
    return

### ----- main() ----- 

def main():
    sheet = sheets_client.open_by_url(helper.constants.SHEET_URL)
    #gsheet_helper.ready_gsheet(sheet=sheet)
    to_search = helper.gsheet_helper.get_usernames_from_sheets(sheet=sheet)
    prev_search = read_usernames('usernames.txt')
    search = cleaned_usernames(prev_search, to_search)
    logging.info(f'searched: {len(prev_search)}')
    logging.info(f'batch: {search}, {len(search)}')
    login_to_insta()
    logging.info('scraping')
    k=1
    for username in search:
        if username == '': continue
        k+=1
        try:
            profile = Profile.from_username(L.context, username)
        except exceptions.AbortDownloadException as e:
            logging.error(f'error: {e}')
            if e.args[0].startswith('Redirected'):
                time.sleep(2500)
                sys.exit(1)
        except Exception as e:
            logging.error(f'error: {e}')
            wait(k)
            continue
        time.sleep(18)
        try:
            posts = profile.get_posts()
        except exceptions.AbortDownloadException as e:
            logging.error(f'error: {e}')
            if e.args[0].startswith('Redirected'):
                time.sleep(2500)
                sys.exit(1)
        except Exception as e:
            logging.error(f'error: {e}')
            wait(k)
            continue
        logging.info(f'scraping {username}:{k}')
        rows_to_append = helper.post_helper.scrape_posts(posts=posts)
        helper.gsheet_helper.send_data_to_sheets(rows_to_append=rows_to_append, sheet=sheet)
        save_username(username)
        logging.info('sheet updated')
        wait(k)
    print('scraping complete')
    delete_search_file('usernames.txt')
    logging.info('scraping complete')

if __name__ == "__main__":
    main()