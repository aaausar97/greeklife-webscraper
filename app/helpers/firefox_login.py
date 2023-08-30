from .helper import constants
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import shutil
import time

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD

pd = os.path.join(os.getcwd(), 'profile/')
cookiesDir = os.path.join(pd, 'cookies.sqlite')

options = webdriver.FirefoxOptions()
options.add_argument("-headless")
options.add_argument("disable-blink-features=AutomationControlled");
options.add_argument("--disable-cookie-encryption")
options.add_argument("window-size=1920,1280");
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36");

try:
    driver = webdriver.Firefox(options=options)
    
except Exception as e:
    raise SystemExit("Firefox driver failed: {}".format(e))

def login_with_firefox():
    # Navigate to Instagram login page
    driver.get('https://www.instagram.com/accounts/login/') 
    print(driver.current_url)
    time.sleep(2)

    # Enter username and password
    username_input = driver.find_element(by='name', value='username')
    password_input = driver.find_element(by='name', value='password')
    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    # Click login button
    login_button = driver.find_element(By.XPATH, value='//*[@id="loginForm"]/div/div[3]/button')
    login_button.click()
    time.sleep(5)
    print(driver.current_url)
    time.sleep(5)
    driver.get('https://www.instagram.com/')
    print(driver.current_url)
    # Check if login was successful
    if driver.current_url == 'https://www.instagram.com/':
        print('Login successful')
    else:
        print('Login failed')

    # Get the cookie file
    capability = driver.capabilities
    browserDir = capability['moz:profile']
    cookieFile = os.path.join(browserDir, 'cookies.sqlite')
    shutil.copyfile(cookieFile, cookiesDir)

if __name__ == '__main__':
    login_with_firefox()