from .helper import constants
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twocaptcha import TwoCaptcha
import os
import requests
import shutil
import time

USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD
API_KEY = 'f33d05b0423ccd481c039ff7cfc9ee88'

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

try:
   solver = TwoCaptcha(API_KEY)
except Exception as e:
    raise SystemExit("Captcha Solver Failed: {}".format(e))

def login_with_firefox():
    # Navigate to Instagram login page
    driver.get('https://www.instagram.com/') 
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
    print("attempted login")
    print(driver.current_url)

    # Check/Solve CAPTCHA
    if 'challenge' in driver.current_url:
        print('CAPTCHA detected')
        try:
            # Switch to the reCAPTCHA iframe
            iframe_xpath = '//iframe[@id="recaptcha-iframe"]'
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, iframe_xpath))
            )
            # iframe = driver.find_element(By.ID, 'recaptcha-iframe')
            driver.switch_to.frame(iframe)

            # Retrieve the site key
            #captcha_site_key = driver.find_element(By.CLASS_NAME, 'g-recaptcha').get_attribute('data-sitekey')
            captcha_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]'))
            )

            captcha_site_key = captcha_element.get_attribute('data-sitekey')

            driver.switch_to.default_content()  # Switch back to default content

            page_url = driver.current_url

            cookies = driver.get_cookies()
            cookies_string = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            print(cookies_string)
            user_agent = driver.execute_script("return navigator.userAgent;")
            print(user_agent)

            # Solve CAPTCHA using 2captcha-python
            print("sending captcha info")
            print(captcha_site_key)
            print(page_url)
            result = solver.recaptcha(sitekey=captcha_site_key, url=page_url, userAgent=user_agent, cookies=cookies_string, enterprise=1)
            print(result)
            captcha_solution = result['code']

            # Switch back to the reCAPTCHA iframe to submit the solution
            driver.switch_to.frame(iframe)
            driver.execute_script("document.getElementById('g-recaptcha-response').style.display = 'block';")
            captcha_input = driver.find_element(By.ID, 'g-recaptcha-response')
            captcha_input.send_keys(captcha_solution)
            driver.switch_to.default_content()  # Switch back to default content

            # Click the login button again to submit the CAPTCHA solution
            login_button.click()
            time.sleep(5)
        except Exception as e:
            print(f"Error solving or submitting CAPTCHA: {e}")
            return
    print(driver.current_url)
    driver.get('https://www.instagram.com/')
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
    print('saved cookies')

if __name__ == '__main__':
    login_with_firefox()
