from datetime import datetime
from itertools import chain
import json
import gspread
import random



with open('config.json', 'r') as f:
    config = json.load(f)

sheets_client = gspread.service_account(filename='google_creds.json') # gspread client for google sheets interactions



## -- CONSTANTS AND CONFIGS --
class Constants:
    def __init__(self) -> None:
        self.sheet_url = config["google_drive"]["sheet_url"]
        self.today = datetime.now()
        self.day_of_week = self.today.weekday()
        self.num_batch_to_run = self.day_of_week


class Batches(Constants):
    def __init__(self) -> None:
        # a list of 7 empty lists, one for each day of the week
        self.batches = [ [] for i in range(7) ]
        self.constants = Constants()
        self.num_batch_to_run = self.constants.num_batch_to_run
        self.batch_emerg = random.randint(0, 6)

    def get_profile_list(self, sheet):
        prefix = 'https://www.instagram.com/'
        formated_profile_list = []
        worksheets = sheet.worksheets()
        worksheet_count = len(worksheets)
        for n in range(1,worksheet_count):
            worksheet = worksheets[n]
            profiles = worksheet.get_values('A:A')
            profiles_list = list(chain(*profiles))
            for profile in profiles_list:
                formated_profile_list.append(profile[len(prefix):].rstrip('/')) #extract username from URLs
        return formated_profile_list
    
    def batch_profiles_from_list(self, sheet):
        list_of_profiles=self.get_profile_list(sheet)
        batch_size = len(list_of_profiles) // 6
        for i in range(6):
            self.batches[i] = list_of_profiles[i*batch_size:(i+1)*batch_size]
        self.batches[6] = list_of_profiles[6*batch_size:]
        return self.batches


if __name__ == "__main__":
    batches = Batches()
    sheet = sheets_client.open_by_url(batches.constants.sheet_url)
    batches.batch_profiles_from_list(sheet)
    print(batches.constants.sheet_url)
    print(datetime.now().weekday())
    print(batches.batches[batches.num_batch_to_run])