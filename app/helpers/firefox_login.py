from selenium_profiles.profiles import profiles
from selenium.webdriver.common.by import By  # locate elements
from selenium_driverless import webdriver
from .helper import constants
import asyncio
import time

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD

options = webdriver.FirefoxOptions()
profile = profiles.Windows()


try:
    driver = webdriver.Firefox(profile=profile, options=options)
except Exception as e:
    raise SystemExit("Firefox driver failed: {}".format(e))

def login_with_firefox():
    # Navigate to Instagram login page
    driver.get('https://www.instagram.com/accounts/login/') 
    time.sleep(2)

    # Enter username and password
    username_input = driver.find_element(by='name', value='username')
    password_input = driver.find_element(by='name', value='password')
    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    # Click login button
    login_button = driver.find_element(by='xpath', value='//*[@id="loginForm"]/div/div[3]/button')
    login_button.click()
    time.sleep(10)
    print(driver.current_url)
    # Check if login was successful
    if driver.current_url == 'https://www.instagram.com/':
        print('Login successful')
    else:
        print('Login failed')

    # Close the driver
    driver.quit()

if __name__ == '__main__':
    login_with_firefox()