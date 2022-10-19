import sqlite3
import datetime
import os.path
# 连接数据库
import uuid

import utils

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "civilserviceclub.db")
db = sqlite3.connect(db_path, check_same_thread=False)


def clear_time_slot(facility_cells_time):
    delete_sql = "delete from time_slot_selection_info where facility_cells_time = '" + facility_cells_time + "'"
    utils.sql_commit(db, delete_sql)


def update_time_slot(REC_CREATOR, NAME_1, NAME_2, time, facility_cells_time, checkbox_name):
    now = datetime.datetime.now()
    # 当前时间
    p_date = now.strftime('%Y%m%d%H%M')
    # 随机ID
    rec_id = str(uuid.uuid1())
    insert_sql = "insert into time_slot_selection_info values ('" + REC_CREATOR + "','" + p_date + "','','','" + \
                 rec_id + "','" + NAME_1 + "','" + NAME_2 + "','" + time + "','" + \
                 facility_cells_time + "','" + checkbox_name + "') "
    utils.sql_commit(db, insert_sql)


def update_time_slot_is_order(REC_CREATOR, NAME_1, NAME_2, facility_cells_time, checkbox_name):
    now = datetime.datetime.now()
    # 当前时间
    p_date = now.strftime('%Y%m%d%H%M')
    # 随机ID
    rec_id = str(uuid.uuid1())
    insert_sql = "insert into time_slot_selection_is_order values ('" + REC_CREATOR + "','" + p_date + "','','','" + rec_id + "','" + NAME_1 + "','" + NAME_2 + "','" + facility_cells_time + "','" + checkbox_name + "') "
    utils.sql_commit(db, insert_sql)


def get_time_slot(facility_cells_time, count: int, time1, time2):
    select_sql = "SELECT a.* FROM time_slot_selection_info A LEFT JOIN " \
                 " time_slot_selection_is_order B " \
                 "ON A.facility_cells_time = B.facility_cells_time AND A.NAME_1 = B.NAME_1 AND A.NAME_2 = " \
                 "B.NAME_2 " \
                 "AND A.checkbox_name = B.checkbox_name WHERE a.facility_cells_time = '" + facility_cells_time + \
                 "' param1 AND" \
                 " B.rec_id IS NULL GROUP BY SUBSTR( a.checkbox_name, 1, 9 ) LIMIT " + str(count)
    if time2 != '' and time1 != '':
        select_sql = select_sql.replace("param1", "AND (a.time = '" + time1 + "'or a.time = '" + time2 + "')")
    elif time1 != '':
        select_sql = select_sql.replace("param1", "AND a.time = '" + time1 + "'")
    elif time1 == '':
        select_sql = select_sql.replace("param1", "")
    return utils.sql_select(db, select_sql)


def record_order(trans_no, payment_for, total_amount):
    now = datetime.datetime.now()
    # 当前时间
    p_date = now.strftime('%Y%m%d%H%M')
    insert_sql = "insert into  t_payment_details values ('" + p_date + "','','" + trans_no + \
                 "','" + payment_for + "','" + total_amount + "')"
    utils.sql_commit(db, insert_sql)


# 获取账号临时分配表一条数据
def get_account_temp():
    select_sql = "SELECT * FROM account_library_temp LIMIT 1"
    return utils.sql_select(db, select_sql)


# 初始化插入账号临时分配表
def int_account_temp(user_name, password, p_time1, p_time2):
    insert_sql = "INSERT INTO account_library_temp VALUES ('" + user_name + "', '" + password + "'where_param)"
    if p_time1 != '' and p_time2 != '':
        insert_sql = insert_sql.replace("where_param", ",'" + p_time1 + "','" + p_time2 + "'")
    elif p_time1 != '':
        insert_sql = insert_sql.replace("where_param", ",'" + p_time1 + "'")
    elif p_time1 == '':
        insert_sql = insert_sql.replace("where_param", ",'',''")
    utils.sql_commit(db, insert_sql)


# 清空账号临时分配表
def clear_account_temp():
    delete_sql = "delete from account_library_temp"
    utils.sql_commit(db, delete_sql)


# 根据用户名删除账号临时分配表
def delete_account_temp_by_user_name(user_name):
    delete_sql = "delete from account_library_temp where user_name = '" + user_name + "'"
    utils.sql_commit(db, delete_sql)


def get_all_account():
    select_sql = "SELECT * FROM account_library"
    return utils.sql_select(db, select_sql)


def delete_all_account():
    delete_sql = "delete from account_library"
    utils.sql_commit(db, delete_sql)


def add_account(user_name, password):
    insert_sql = "INSERT INTO account_library VALUES ('" + user_name + "', '" + password + "', -1, 1)"
    utils.sql_commit(db, insert_sql)


# 获取可用账号数量
def count_use_account():
    count_sql = "SELECT COUNT(*) AS ALL_COUNT FROM account_library WHERE in_use = '-1' AND healthy = '1'"
    return utils.sql_select(db, count_sql)


# 获取可用账号列表
def get_use_account():
    select_sql = "SELECT * FROM account_library WHERE in_use = '-1' AND healthy = '1'"
    return utils.sql_select(db, select_sql)


# 获取当前可选时间列表
def get_optional_time():
    select_sql = ""
    return utils.sql_select(db, select_sql)


def update_account(user_name):
    update_sql = "UPDATE account_library SET in_use = '1' WHERE user_name = '" + user_name + "'"
    utils.sql_commit(db, update_sql)


def init_account_status():
    update_sql = "UPDATE account_library SET in_use = '-1' "
    utils.sql_commit(db, update_sql)


if __name__ == '__main__':
    pass
