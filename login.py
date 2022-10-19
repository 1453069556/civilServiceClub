from tkinter import Listbox
from tkinter.scrolledtext import ScrolledText

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from utils import log, has_element

url_login = "https://gateway.csc.sg/webclub/facilities/"


def login(driver, user_name, password, text: ScrolledText):
    login_ok = False
    driver.get(url_login)
    while not login_ok:
        driver.implicitly_wait(3)
        try:
            if driver.find_element(By.ID, 'log-in'):
                log(driver, "当前页面：登录页", text)
                driver.find_element(By.NAME, 'login').send_keys(user_name)
                driver.find_element(By.NAME, 'password').send_keys(password)
                # 点击登录
                driver.find_element(By.XPATH, '//button[@name="Login"]').submit()
                WebDriverWait(driver, 3)
            # 登录频繁提示 ，点击Disconnect
            if has_element(driver, By.XPATH, "//*[contains(text(),'Disconnect')]"):
                log(driver, "当前页面：登录频繁，点击Disconnect！", text)
                driver.find_element(By.XPATH, "//*[contains(text(),'Disconnect')]").click()
            if driver.find_element(By.XPATH, "//*[contains(text(),'Facilities')]"):
                log(driver, "当前页面：主页面，登陆成功！", text)
                login_ok = True
        # 发生错误时，打印报错原因
        except Exception as e:
            print(e)
