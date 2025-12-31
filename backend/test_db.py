#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

# 数据库配置
DB_CONFIG = {
    'user': 'root',
    'password': '',
    'database': 'artist_system',
    'unix_socket': '/run/mysqld/mysqld.sock',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def test_db_connection():
    try:
        print("正在尝试连接数据库...")
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("数据库连接成功！")
            # 查看当前数据库
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db = cursor.fetchone()
            print(f"当前数据库: {db[0]}")
            # 查看数据库中的表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"数据库中的表: {[table[0] for table in tables]}")
            cursor.close()
            conn.close()
    except Error as e:
        print(f"数据库连接错误: {e}")

if __name__ == "__main__":
    test_db_connection()
