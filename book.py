import datetime
import threading
import time
from tkinter import Listbox
from tkinter.scrolledtext import ScrolledText

from selenium.common import ElementClickInterceptedException
from NewException import AcceptableException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from utils import log, has_element
import dataBaseSqlite as database


def facilities_booking(driver: WebDriver, days: int, text: ScrolledText):
    big_class_is_ok = False
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=days)
    n_days = now + delta
    p_date = n_days.strftime('%y%m%d')
    while not big_class_is_ok:
        if has_element(driver, By.CLASS_NAME, 'box1'):
            log(driver, "当前动作：点击facilities_booking成功", text)
            driver.find_element(By.CLASS_NAME, 'box1').click()
            driver.implicitly_wait(3)
        if has_element(driver, By.XPATH, "//*[contains(text(),'Tessensohn Clubhouse')]"):
            log(driver, "当前动作：选择Tessensohn Clubhouse", text)
            driver.find_element(By.XPATH, "//*[contains(text(),'Tessensohn Clubhouse')]").click()
            driver.implicitly_wait(3)
        if has_element(driver, By.XPATH, "//*[contains(text(),'BADMINTON COURTS BOOKING')]"):
            log(driver, "当前动作：选择BADMINTON COURTS BOOKING", text)
            driver.find_element(By.XPATH, "//*[contains(text(),'BADMINTON COURTS BOOKING')]").click()
            driver.implicitly_wait(3)
        if has_element(driver, By.XPATH, "//option[@value='" + p_date + "']"):
            log(driver, "当前动作：选择日期" + p_date, text)
            driver.find_element(By.XPATH, "//option[@value='" + p_date + "']").click()
            driver.implicitly_wait(3)
        if has_element(driver, By.XPATH, "//*[contains(text(),'Next Step')]"):
            log(driver, "当前动作：点击下一步", text)
            next_step = driver.find_element(By.XPATH, "//*[contains(text(),'Next Step')]")
            # 先执行javaScript,否则无法点击
            driver.execute_script("arguments[0].click();", next_step)
            driver.implicitly_wait(3)
        if has_element(driver, By.XPATH, "//*[contains(text(),'TIME SLOT SELECTION')]"):
            log(driver, "当前页面：选择预定时间段", text)
            big_class_is_ok = True
    return p_date


mu = threading.Lock()  ###通过工厂方法获取一个新的锁对象


# //tr[@class='facility-cells']/td[contains(text(), '07:00')]
def time_slot_selection(driver: WebDriver, text: ScrolledText, p_time1, p_time2, param):
    global mu
    time_slot_is_ok = False
    name_1 = None
    name_2 = None
    facility_cells_time = None
    if has_element(driver, By.CLASS_NAME, "name-1"):
        name_1 = driver.find_element(By.XPATH, "//div[@class='name-1']//div[@class='name-sub']").text
        print("name_1:" + name_1)
    if has_element(driver, By.CLASS_NAME, "name-2"):
        name_2 = driver.find_element(By.XPATH, "//div[@class='name-2']//div[@class='name-sub']").text
        print("name_2:" + name_2)
    if has_element(driver, By.CLASS_NAME, "name-2"):
        facility_cells_time = driver.find_element(By.XPATH, "//div[@class='name-3']//div[@class='name-sub']").text
        print("facility_cells_time:" + facility_cells_time)
    while not time_slot_is_ok:
        if has_element(driver, By.XPATH, "//div[@class='facility-table']//tr[@class='facility-cells']"):
            opens = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            print("当前节点共" + str(len(opens)))
            # 初始化操作
            log(driver, "开始初始化！", text)
            update(driver, "BADMINTON COURTS BOOKING", opens, name_1, name_2, facility_cells_time)
            result = []
            hours = 0
            while len(list(result)) == 0:
                # 取出两个checkBox，时间段不能重复
                result = database.get_time_slot(facility_cells_time, 2, p_time1, p_time2)
                if len(list(result)) == 0:
                    p_time1 = param.get("p_min_time") + hours
                    hours = hours + 1
                    p_time2 = param.get("p_min_time") + hours
                    hours = hours + 1
                    if p_time1 > 9:
                        p_time1 = str(p_time1) + ":00"
                    else:
                        p_time1 = "0" + str(p_time1) + ":00"
                    if p_time2 > 9:
                        p_time2 = str(p_time2) + ":00"
                    else:
                        p_time2 = "0" + str(p_time2) + ":00"
                else:
                    break
            # 选中2个checkBox
            # TODO 此处考虑加锁
            if mu.acquire():  ##加锁
                for i in result:
                    log(driver, "当前动作：选中" + i[9], text)
                    index = 100
                    while True:
                        try:
                            driver.find_element(By.XPATH, "//input[@name='" + str(i[9]) + "']").click()
                            database.update_time_slot_is_order("BADMINTON COURTS BOOKING", name_1, name_2,
                                                               facility_cells_time,
                                                               i[9])
                        except ElementClickInterceptedException as e:
                            index += 99
                            print("拉动滚动条" + str(index))
                            driver.execute_script("window.scrollTo(0," + str(index) + ");")
                        else:
                            break
                mu.release()  ##释放锁
            # 点击下一步
            if has_element(driver, By.XPATH, "//*[contains(text(),'Next Step')]"):
                log(driver, "当前动作：已经选完时间段，Next Step", text)
                next_step = driver.find_element(By.XPATH, "//*[contains(text(),'Next Step')]")
                # 先执行javaScript,否则无法点击
                driver.execute_script("arguments[0].click();", next_step)
            if has_element(driver, By.XPATH, "//*[contains(text(),'No slots selected')]"):
                log(driver, "No slots selected,无可选日期，暂退出脚本处理", text)
                # 暂时以结束脚本作为处理方案
                exit()
            if has_element(driver, By.XPATH, "//*[contains(text(),'BOOKING DETAILS')]"):
                log(driver, "当前页面：订单界面", text)
                time_slot_is_ok = True
            # Cannot book more than 2 slots per day for advanced booking
            if has_element(driver, By.XPATH, "//*[contains(text(),'Cannot book more')]"):
                log(driver, "预定场地超过2,将等待10分钟再次尝试", text)
                # 等待10分钟
                time.sleep(10 * 60)
                # 抛出异常，重跑
                raise AcceptableException("预定场地超过2,再次尝试")
                # 暂时以结束脚本作为处理方案
                # exit()


def booking_details(driver: WebDriver, text: ScrolledText):
    is_ok = False
    while not is_ok:
        if has_element(driver, By.XPATH, "//*[contains(text(),'BOOKING DETAILS')]"):
            log(driver, "当前动作：订单详情，点击确认Next Step", text)
            next_step = driver.find_element(By.XPATH, "//*[contains(text(),'Next Step')]")
            # 先执行javaScript,否则无法点击
            driver.execute_script("arguments[0].click();", next_step)
        if has_element(driver, By.XPATH, "//*[contains(text(),'Booking Confirmation')]"):
            log(driver, "当前界面：预定确认BOOKING CONFIRMATION", text)
            is_ok = True


def booking_confirmation(driver: WebDriver, email: str, text: ScrolledText):
    is_ok = False
    while not is_ok:
        if len(str(email).strip()) != 0:
            if has_element(driver, By.NAME, "emailaddr"):
                log(driver, "当前动作：输入邮箱" + email, text)
                email_addr = driver.find_element(By.NAME, "emailaddr")
                email_addr.clear()
                email_addr.send_keys(email)
        if has_element(driver, By.XPATH, "//div[contains(text(),'Confirm Booking')]"):
            log(driver, "当前动作：预定确认，点击确认Confirm Booking", text)
            next_step = driver.find_element(By.XPATH, "//div[contains(text(),'Confirm Booking')]")
            # 先执行javaScript,否则无法点击
            driver.execute_script("arguments[0].click();", next_step)
        if has_element(driver, By.XPATH, "//*[contains(text(),'Payment Details')]"):
            log(driver, "当前界面：付款详细信息Payment Details", text)
            is_ok = True


def payment_details(driver: WebDriver, text: ScrolledText):
    is_ok = False
    payment = None
    trans_no = None
    payment_for = None
    total_amount = None
    if has_element(driver, By.XPATH, "//*[contains(text(),'Payment Details')]"):
        elements = driver.find_elements(By.CLASS_NAME, "payment-sub")
        payment_for = elements[0].text
        trans_no = elements[1].text
        total_amount = elements[2].text
        database.record_order(trans_no, payment_for, total_amount)
    while not is_ok:
        if has_element(driver, By.XPATH, "//div[contains(text(),'Pay By Credit Card')]"):
            log(driver, "当前动作：付款详情信息，用信用卡支付Pay By Credit Card", text)
            next_step = driver.find_element(By.XPATH, "//div[contains(text(),'Pay By Credit Card')]")
            # 先执行javaScript,否则无法点击
            driver.execute_script("arguments[0].click();", next_step)
        if has_element(driver, By.XPATH, "//font[contains(text(),'Secure Payment Page')]"):
            log(driver, "当前界面：安全付款页面 Secure Payment Page", text)
            is_ok = True
            payment = "Secure Payment Page"
    return payment


def update(driver, REC_CREATOR, opens, name_1, name_2, facility_cells_time):
    # 先清空
    database.clear_time_slot(facility_cells_time)
    # 初始化当前节点信息
    for o in opens:
        checkbox_name = o.get_attribute("name")
        time = str(driver.find_element(By.XPATH, "//input[@name='" + checkbox_name + "']/../../td[1]")
                   .get_attribute("textContent"))
        database.update_time_slot(REC_CREATOR, name_1, name_2, time, facility_cells_time, checkbox_name)
