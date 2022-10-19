from tkinter import *
from tkinter.scrolledtext import ScrolledText

from selenium.common import NoSuchElementException


def log(driver, pageInfo, text: ScrolledText):
    print(pageInfo + " ---sessionId:" + driver.session_id)
    text.insert(END, pageInfo + " ---sessionId:" + driver.session_id + "\n")
    text.update()


def has_element(driver, by, value):
    try:
        element = driver.find_element(by=by, value=value)
    except NoSuchElementException as e:
        return False
    return True


# 无需commit类sql
def sql_select(db, sql):
    # 创建游标对象
    cursor = db.cursor()
    try:
        print(sql)
        cursor.execute(sql)
        return cursor.fetchall()
    # 发生错误时，打印报错原因
    except Exception as e:
        print(e)
    # 无论是否报错都执行
    finally:
        cursor.close()


# 需commit类sql
def sql_commit(db, sql):
    # 创建游标对象
    cursor = db.cursor()
    try:
        print(sql)
        cursor.execute(sql)
        # 将数据提交给数据库（加入数据，修改数据要先提交）
        db.commit()
    # 发生错误时，打印报错原因
    except Exception as e:
        print(e)
    # 无论是否报错都执行
    finally:
        cursor.close()
