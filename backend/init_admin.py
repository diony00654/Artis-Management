#!/usr/bin/env python3
import bcrypt
import mysql.connector

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 15111,
    'user': 'artist_user',
    'password': 'password',
    'database': 'artist_system',
    'charset': 'utf8mb4'
}

# 创建数据库连接
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# 超级管理员信息
username = 'admin'
password = 'justin00654'
nickname = '管理员'
is_admin = True

# 生成bcrypt哈希密码
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
hashed_password_str = hashed_password.decode('utf-8')

# 插入超级管理员账号
try:
    query = '''
        INSERT INTO users (username, password, nickname, is_admin)
        VALUES (%s, %s, %s, %s)
    '''
    cursor.execute(query, (username, hashed_password_str, nickname, is_admin))
    conn.commit()
    print(f"超级管理员账号已创建成功！")
    print(f"用户名: {username}")
    print(f"密码: {password}")
    print(f"昵称: {nickname}")
except Exception as e:
    print(f"创建账号失败: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
