import contextlib
import os
import platform
from math import ceil

import ttkbootstrap
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import inspect
import ctypes
import time
import tkinter
import tkinter.messagebox
import tkinter as tk
from ttkbootstrap.scrolled import ScrolledFrame
from selenium import webdriver
from selenium.common import TimeoutException
from ttkbootstrap.tableview import Tableview

from NewException import AcceptableException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from tkinter import *

import dataBaseSqlite
from utils import log

from login import login
from book import facilities_booking, time_slot_selection, booking_confirmation, booking_details, payment_details

accountsPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'account\\accounts.ini')

chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_exe = None
if platform.system() == 'Windows':
    chrome_exe = str(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'driver\\chromedriver.exe'))

url_login = "https://gateway.csc.sg/webclub/facilities/"


def run():
    # TODO 测试用
    # init()
    with contextlib.closing(
            webdriver.Chrome(service=Service(chrome_exe.replace("\\", "/")), options=chrome_options)) as driver:
        driver.minimize_window()
        # 设置超时时间
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        if mu.acquire():  ##加锁
            # 取号
            account = list(dataBaseSqlite.get_account_temp())
            i = 0
            while len(account) < 1:
                i = i + 1
                # 取号
                account = list(dataBaseSqlite.get_account_temp())
                log(driver, "第" + str(i) + "次提示(仅提示3次)，账号库存不足，请添加账号！", text)
                time.sleep(10)
                if i > 2:
                    exit()
            user_name = account[0][0]
            password = account[0][1]
            # 时间点1
            p_time1 = account[0][2]
            # 时间点2
            p_time2 = account[0][3]
            print(user_name + "--------" + password)
            # 更新号状态
            dataBaseSqlite.update_account(user_name)
            # 删除临时表中已取出的账号
            dataBaseSqlite.delete_account_temp_by_user_name(user_name)
            mu.release()  ##释放锁
        # delay_date = accounts.get("delay", "delayDate")
        print(param.get("p_delay_day"))
        delay_date = int(param.get("p_delay_day"))
        while True:
            try:
                # 登录
                login(driver, user_name, password, text)
                # 选择大分类
                p_date = facilities_booking(driver, int(delay_date), text)
                # 选择预定时间段
                time_slot_selection(driver, text, p_time1, p_time2, param)
                # 过确认页面
                booking_details(driver, text)
                # 确定订单详情
                booking_confirmation(driver, "1453069556@qq.com", text)
                # 跳转付款界面
                payment = str(payment_details(driver, text))
                if payment == "Secure Payment Page":
                    log(driver, "到达付款界面，请及时付款，页面将停留5分钟后关闭", text)
                    driver.maximize_window()
                    # TODO 暂时以等待5分钟处理
                    time.sleep(5 * 60)
            except TimeoutException:
                driver.execute_script('window.stop()')
                print("加载超时，重新启动")
            except AcceptableException:
                log(driver, "触发重试机制", text)
                print("触发重试机制")
            else:
                break


def test_thread(i):
    num = range(5)
    while True:
        for t in num:
            print(i + t)


# 总的线程池
threads = []

mu = threading.Lock()  ###通过工厂方法获取一个新的锁对象


def init():
    # 清空临时表
    dataBaseSqlite.clear_account_temp()
    useAccounts = list(dataBaseSqlite.get_use_account())
    # 运行计划
    run_step = []
    # 可运行账号数量
    account_count = len(useAccounts)
    # 定义时间区间长度
    time_interval = int(param.get("p_max_time")) - int(param.get("p_min_time"))
    average = int(time_interval / account_count)
    remainder = time_interval % account_count
    if average > 2:
        for i in range(account_count - 1):
            run_step.append(2)
        run_step.append(time_interval - (account_count - 1) * 2)
    elif average == 0:
        for i in range(time_interval):
            run_step.append(1)
        for i in range(account_count - time_interval):
            run_step.append(0)
    elif remainder != 0:
        for i in range(account_count - 1):
            run_step.append(average)
        run_step.append(remainder)
    else:
        for i in range(account_count):
            run_step.append(average)
    hours = 0
    for account in useAccounts:
        p_time1 = int(param.get("p_min_time")) + hours
        hours = hours + 1
        p_time2 = int(param.get("p_min_time")) + hours
        hours = hours + 1
        if p_time1 > 9:
            p_time1 = str(p_time1) + ":00"
        else:
            p_time1 = "0" + str(p_time1) + ":00"
        if p_time2 > 9:
            p_time2 = str(p_time2) + ":00"
        else:
            p_time2 = "0" + str(p_time2) + ":00"
        dataBaseSqlite.int_account_temp(account[0], account[1], p_time1, p_time2)


def start_run():
    global mu
    try:
        # 初始化运行计划
        init()
        # 按钮不可点击
        button.config(state=tk.DISABLED)
        run_num = range(int(param.get("p_thread_num")))
        for i in run_num:
            # 创建线程
            t = threading.Thread(target=run)
            threads.append(t)
        for thread in threads:
            # 守护线程
            thread.setDaemon(True)
            # 开始线程
            thread.start()
            # time.sleep(3)
            # 阻塞--卡死界面！
            # thread.join()
    except Exception as e:
        text.insert(END, e)
        text.insert(END, "\n")
        text.update()
        threads.clear()


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""

    tid = ctypes.c_long(tid)

    if not inspect.isclass(exctype):
        exctype = type(exctype)

    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))

    if res == 0:

        raise ValueError("invalid thread id")

    elif res != 1:

        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)

        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def stop_all():
    for thread in threads:
        stop_thread(thread)
        text.insert(END, "停止线程" + str(thread.ident) + "\n")
        text.update()
    threads.clear()
    # 按钮恢复点击
    button.config(state=tk.ACTIVE)
    # 账号恢复
    dataBaseSqlite.init_account_status()


def parameter_window_destroy(parameter_wind: Toplevel):
    parameter_wind.destroy()
    root.attributes('-disabled', False)
    root.wm_attributes('-topmost', 1)
    root.wm_attributes('-topmost', 0)


def TableCanvasStr():
    global result1
    all_account = dataBaseSqlite.get_all_account()
    i = 0
    result = []
    for account in all_account:
        i = i + 1
        use_state = "未使用"
        if account[2] == 1:
            use_state = "使用中"
        account_heathy = "正常"
        if account[3] == -1:
            account_heathy = "异常"
        result1 = (account[0], account[1], use_state, account_heathy)
        result.append(result1)
    return result


def account_window():
    for wind in windowList:
        wind.destroy()
    coldata = [
        {"text": "账号", "stretch": True},
        {"text": "密码", "stretch": True},
        {"text": "使用状态", "stretch": True},
        {"text": "账号状况", "stretch": True},
    ]
    dt = Tableview(
        master=root,
        coldata=coldata,
        rowdata=TableCanvasStr(),
        paginated=True,
        searchable=True,
        bootstyle=PRIMARY,
    )
    windowList.append(dt)
    dt.pack(fill=BOTH, expand=YES, padx=10, pady=10)
    button_add_aacount = ttk.Button(root, text='添加账号', bootstyle=INFO, command=lambda: insert_account_window(dt))
    button_add_aacount.pack(side="left", padx="20", pady="20")
    windowList.append(button_add_aacount)
    save_aacount = ttk.Button(root, text='保存', bootstyle=SUCCESS, command=lambda: save_all_account(dt))
    save_aacount.pack(side="left", padx="20", pady="20")
    windowList.append(save_aacount)
    close_aacount = ttk.Button(root, text='关闭', bootstyle=WARNING,
                               command=lambda: destroy_child_window(windowList))
    close_aacount.pack(side="left", padx="20", pady="20")
    windowList.append(close_aacount)


def save_all_account(dt):
    try:
        if dt.get_rows()[0].values:
            dataBaseSqlite.delete_all_account()
        for row in dt.get_rows():
            dataBaseSqlite.add_account(row.values[0], row.values[1])
        param.update({"p_thread_num": list(dataBaseSqlite.count_use_account())[0][0]})
    except Exception as e:
        print(e)
    tkinter.messagebox.showinfo("保存成功", "账号保存成功")


def insert_account_window(dt):
    # THE CLUE
    root.wm_attributes("-disabled", True)
    # Creating the toplevel dialog
    insertWind = tk.Toplevel(root)
    insertWind.title = "添加账号"
    insertWind.minsize(800, 400)
    ttk.Label(insertWind, bootstyle=INFO, text="账号").pack(side="left", padx="20", pady="20")
    userName = ttk.Entry(insertWind, bootstyle=INFO)
    userName.pack(side="left", padx="20", pady="20")
    ttk.Label(insertWind, bootstyle=INFO, text="密码").pack(side="left", padx="20", pady="20")
    password = ttk.Entry(insertWind, bootstyle=INFO)
    password.pack(side="left", padx="20", pady="20")
    button_add_aacount = ttk.Button(insertWind, text='保存并关闭', bootstyle=INFO,
                                    command=lambda: save_account(insertWind, dt, userName.get(), password.get()))
    button_add_aacount.pack(side="left", padx="20", pady="20")
    insertWind.protocol('WM_DELETE_WINDOW',
                        lambda arg=insertWind: close_insert_account_window(arg))


dataBaseSqlite.init_account_status()
param = {"p_thread_num": list(dataBaseSqlite.count_use_account())[0][0], "p_delay_day": 7, "p_min_time": 15,
         "p_max_time": 18}


def parameter_window():
    global param
    root.attributes('-disabled', True)
    parameter_wind = tkinter.Toplevel(root)
    parameter_wind.title = '运行'
    parameter_wind.minsize(1280, 1080)
    DataEntryForm(parameter_wind)
    parameter_wind.protocol('WM_DELETE_WINDOW', lambda: parameter_window_destroy(parameter_wind))


def save_account(insertWind, dt, userName, password):
    dt.insert_row('end', [userName, password, 0, 0])
    close_insert_account_window(insertWind)
    dt.goto_first_page()


def close_insert_account_window(insertWind):
    insertWind.destroy()
    root.wm_attributes("-disabled", False)
    root.wm_attributes('-topmost', 1)
    root.wm_attributes('-topmost', 0)


def destroy_child_window(windowList: list):
    # 关闭
    for wind in windowList:
        wind.destroy()
    windowList.clear()


def order_window():
    for wind in windowList:
        wind.destroy()
    colors = root.style.colors
    coldata = [
        {"text": "订单创建时间", "stretch": True},
        {"text": "订单处理时间", "stretch": True},
        {"text": "订单号", "stretch": True},
        {"text": "预定账户", "stretch": True},
        {"text": "预定场景", "stretch": True},
        {"text": "预定日期", "stretch": True},
        {"text": "预定时间段", "stretch": True},
        {"text": "金额", "stretch": True},
        {"text": "状态", "stretch": True},
    ]

    rowdata = [
        ('20221018', ' ', '01FACY20221000000545', 'A174585W1', 'BADMINTON COURTS BOOKING',
         '25-Oct-2022 Tuesday', '15:00', '$12.00', '代付款'),
        ('20221018', ' ', '01FACY20221000000545', 'A174585W1', 'BADMINTON COURTS BOOKING',
         '25-Oct-2022 Tuesday', '16:00', '$13.00', '代付款'),
        ('20221018', ' ', '01FACY20221000000545', 'A174585', 'BADMINTON COURTS BOOKING',
         '25-Oct-2022 Tuesday', '17:00', '$14.00', '代付款'),
    ]

    dt = Tableview(
        master=root,
        coldata=coldata,
        rowdata=rowdata,
        paginated=True,
        searchable=True,
        bootstyle=PRIMARY,
    )
    dt.pack(fill=BOTH, expand=YES, padx=10, pady=10)
    windowList.append(dt)
    go_to_pay = ttk.Button(root, text='点击前往选中行付款页', bootstyle=DANGER, command=None)
    go_to_pay.pack(side="left", padx="20", pady="20")
    windowList.append(go_to_pay)
    close_go_to_pay = ttk.Button(root, text='关闭', bootstyle=WARNING,
                                 command=lambda: destroy_child_window(windowList))
    close_go_to_pay.pack(side="left", padx="20", pady="20")
    windowList.append(close_go_to_pay)


class DataEntryForm(ttk.Frame):

    def __init__(self, master):
        super().__init__(master, padding=(20, 10))
        self.pack(fill=BOTH, expand=YES)
        self.frame = master
        # form variables
        self.entry_thread_num = ttk.IntVar(value=param.get("p_thread_num"))
        self.entry_delay_day = ttk.IntVar(value=param.get("p_delay_day"))
        self.min_time = ttk.IntVar(value=param.get("p_min_time"))
        self.max_time = ttk.IntVar(value=param.get("p_max_time"))

        # form header
        hdr_txt = "配置参数"
        hdr = ttk.Label(master=self, text=hdr_txt, width=50)
        hdr.pack(fill=X, pady=10)

        # form entries
        self.create_form_entry("线程数量", self.entry_thread_num)
        self.create_form_entry("推后天数", self.entry_delay_day)
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=5)
        lbl = ttk.Label(master=container, text="时间区间(24小时制)", width=17)
        lbl.pack(side=LEFT, padx=5)
        ent = ttk.Entry(master=container, textvariable=self.min_time)
        ent.pack(side=LEFT, fill=X, expand=YES)
        lbl2 = ttk.Label(master=container, text="------", width=5)
        lbl2.pack(side=LEFT)
        ent2 = ttk.Entry(master=container, textvariable=self.max_time)
        ent2.pack(side=LEFT, fill=X, expand=YES)
        self.create_buttonbox()

    def create_form_entry(self, label, variable):
        """Create a single form entry"""
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=5)

        lbl = ttk.Label(master=container, text=label.title(), width=10)
        lbl.pack(side=LEFT, padx=5)

        ent = ttk.Entry(master=container, textvariable=variable)
        ent.pack(side=LEFT, padx=5, fill=X, expand=YES)

    def create_buttonbox(self):
        """Create the application buttonbox"""
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=(15, 10))

        cnl_btn = ttk.Button(
            master=container,
            text="退出",
            command=self.on_cancel,
            bootstyle=DANGER,
            width=6,
        )
        cnl_btn.pack(side=RIGHT, padx=5)
        cnl_btn.focus_set()

        sub_btn = ttk.Button(
            master=container,
            text="提交",
            command=self.on_submit,
            bootstyle=SUCCESS,
            width=6,
        )
        sub_btn.pack(side=RIGHT, padx=5)

    def on_submit(self):
        param.update({"p_thread_num": self.entry_thread_num.get(), "p_delay_day": self.entry_delay_day.get(),
                      "p_min_time": self.min_time.get(), "p_max_time": self.max_time.get()})
        self.on_cancel()
        tkinter.messagebox.showinfo("保存成功", "参数保存成功")

    def on_cancel(self):
        self.frame.destroy()
        root.attributes('-disabled', False)
        root.wm_attributes('-topmost', 1)
        root.wm_attributes('-topmost', 0)


windowList = []
root = ttk.Window(title="TEST", themename="superhero")
menu_bar = tk.Menu(root)
menu = tk.Menu(menu_bar, tearoff=0)  # menu加入菜单栏menu_bar下（tearoff=0 不可分割）
tkinter.Frame(root, height=20, relief="sunken", background="black").pack(fill=BOTH, padx=5, pady=5)
# menu菜单加入标签和相应执行命令
menu_bar.add_command(label='账号管理', command=account_window)
menu_bar.add_command(label='运行配置', command=parameter_window)
menu_bar.add_command(label='订单管理', command=order_window)
menu_bar.add_command(label='退出', command=root.quit)
root.config(menu=menu_bar)

# 得到屏幕宽度
sw = root.winfo_screenwidth()
# 得到屏幕高度
sh = root.winfo_screenheight()
ww = 1920
wh = 1080
x = (sw - ww) / 2
y = (sh - wh) / 2
root.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
text = ttkbootstrap.scrolled.ScrolledText(root, autohide=True)
text.pack(fill=BOTH, expand=YES, padx=10, pady=10)
# button = ttk.Button(root, text='开始', bootstyle=DEFAULT, command=lambda: start_run())
button = ttk.Button(root, text='开始', bootstyle=DEFAULT, command=lambda: start_run())
button.pack(side="left", padx="20", pady="20", anchor='sw')
button1 = ttk.Button(root, text='结束', bootstyle=DEFAULT, command=lambda: stop_all())
button1.pack(side="right", padx="20", pady="20", anchor='se')
root.state("zoomed")
root.mainloop()
