from selenium import webdriver
import os


class SeleniumClient:

    def __init__(self, driver_path=os.path.join(os.path.split(__file__)[0], f'chromedriver.exe')):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        self.driver = webdriver.Chrome(executable_path=driver_path, options=options)

    def get_usage_analytics_cookies(self, cookies):
        self.driver.get('https://app.schoology.com')
        for cookie in cookies:
            self.driver.add_cookie(cookie_dict=cookie)
        self.driver.get('https://app.schoology.com')
        self.driver.get('https://app.schoology.com/school_analytics')
        return self.driver.get_cookies()

    def __del__(self):
        self.driver.quit()