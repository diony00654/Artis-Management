from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import uuid
import bcrypt
import secrets
from functools import wraps
import calendar
import calendar

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# 生成安全密钥
app.secret_key = secrets.token_hex(32)

# 配置会话
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 会话过期时间：1小时

# 上传目录配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建上传目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 数据库配置
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'artist_user'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'artist_system'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# ========== 工具函数 ==========

# 数据库连接管理
def get_db_connection():
    try:
        # 打印连接参数，用于调试
        print(f"[{datetime.now()}] 尝试连接数据库: {DB_CONFIG}")
        conn = mysql.connector.connect(**DB_CONFIG)
        print(f"[{datetime.now()}] 数据库连接成功！")
        return conn
    except Error as e:
        error_msg = f"数据库连接错误: {e}"
        print(f"[{datetime.now()}] {error_msg}")
        # 将错误信息写入日志文件
        with open('/root/artist-system/db_error.log', 'a') as f:
            f.write(f"{datetime.now()}: {error_msg}\n")
        return None

# 数据库操作装饰器
def db_operation(func):
    """数据库操作装饰器，处理连接和事务"""
    @wraps(func)
    def decorated(*args, **kwargs):
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': '数据库连接失败'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            result = func(conn, cursor, *args, **kwargs)
            conn.commit()
            return result
        except Error as e:
            conn.rollback()
            print(f"数据库操作失败: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    return decorated

# 记录操作日志
def log_operation(operator, operation_type, artist_id, artist_name, operation_content):
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        query = '''
            INSERT INTO operation_logs (operator, operation_type, artist_id, artist_name, operation_content)
            VALUES (%s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (operator, operation_type, artist_id, artist_name, operation_content))
        conn.commit()
    except Error as e:
        print(f"记录操作日志失败: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ========== 工具函数 ==========

# 数据库操作装饰器
def db_operation(func):
    """数据库操作装饰器，处理连接和事务"""
    @wraps(func)
    def decorated(*args, **kwargs):
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': '数据库连接失败'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            result = func(conn, cursor, *args, **kwargs)
            conn.commit()
            return result
        except Error as e:
            conn.rollback()
            print(f"数据库操作失败: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    return decorated

# 记录工单操作日志
def log_ticket_action(conn, cursor, ticket_id, operator_id, operator_name, action, field_changed=None, old_value=None, new_value=None):
    """记录工单操作日志"""
    query = '''
        INSERT INTO ticket_logs (ticket_id, operator_id, operator_name, action, field_changed, old_value, new_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(query, (ticket_id, operator_id, operator_name, action, field_changed, old_value, new_value))

# 生成工单编号函数
def generate_ticket_no():
    """生成工单编号，格式：WT + 日期 + 4位序号"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)  # 设置cursor返回字典
        # 获取当前日期
        today = datetime.now().strftime('%Y%m%d')
        # 生成工单前缀
        prefix = f"WT{today}"
        
        # 查询今天的最大工单编号
        query = "SELECT MAX(ticket_no) AS max_no FROM work_tickets WHERE ticket_no LIKE %s"
        cursor.execute(query, (f"{prefix}%",))
        result = cursor.fetchone()
        
        if result and result['max_no']:
            # 提取序号部分并加1
            seq = int(result['max_no'][-4:]) + 1
        else:
            # 今天没有工单，从0001开始
            seq = 1
        
        # 生成完整工单编号
        ticket_no = f"{prefix}{seq:04d}"
        return ticket_no
    except Error as e:
        print(f"生成工单编号失败: {e}")
        return None
    finally:
        conn.close()

# ========== 认证中间件 ==========

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # 检查是否为管理员
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('login'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT is_admin FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
            if not user or not user['is_admin']:
                return redirect(url_for('index'))
        except Error as e:
            print(f"检查管理员权限失败: {e}")
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        
        return f(*args, **kwargs)
    return decorated_function

# ========== 用户认证 API ==========

@app.route('/schedule')
def schedule_page():
    return render_template('schedule.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            return render_template('login.html', error='数据库连接失败')
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            
            if user:
                # 检查用户是否被禁用
                if user['disabled']:
                    return render_template('login.html', error='账号已被禁用')
                
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    # 登录成功，设置会话
                    session.permanent = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['nickname'] = user['nickname']
                    session['is_admin'] = user['is_admin']
                    
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error='用户名或密码错误')
            else:
                return render_template('login.html', error='用户名或密码错误')
        except Error as e:
            print(f"登录失败: {e}")
            return render_template('login.html', error='登录失败，请重试')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/current-user')
@login_required
def get_current_user():
    """获取当前登录用户信息"""
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'nickname': session['nickname'],
        'is_admin': session['is_admin']
    })

@app.route('/users', methods=['GET', 'POST'])
@admin_required
def user_management():
    """用户管理页面"""
    conn = get_db_connection()
    if not conn:
        return render_template('user_management.html', users=[], alert={'type': 'error', 'message': '数据库连接失败'})
    
    alert = None
    
    if request.method == 'POST':
        # 创建新用户
        username = request.form['username']
        password = request.form['password']
        nickname = request.form['nickname']
        
        try:
            # 检查用户名是否已存在
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                alert = {'type': 'error', 'message': '用户名已存在'}
            else:
                # 加密密码
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # 插入新用户
                cursor.execute(
                    'INSERT INTO users (username, password, nickname, is_admin) VALUES (%s, %s, %s, FALSE)',
                    (username, hashed_password.decode('utf-8'), nickname)
                )
                conn.commit()
                alert = {'type': 'success', 'message': '用户创建成功'}
        except Error as e:
            print(f"创建用户失败: {e}")
            alert = {'type': 'error', 'message': '创建用户失败，请重试'}
        finally:
            cursor.close()
    
    # 获取所有用户
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, username, nickname, is_admin, created_at FROM users ORDER BY id DESC')
        users = cursor.fetchall()
    except Error as e:
        print(f"获取用户列表失败: {e}")
        users = []
        alert = {'type': 'error', 'message': '获取用户列表失败'}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return render_template('user_management.html', users=users, alert=alert, current_user={
        'username': session['username'],
        'nickname': session['nickname'],
        'is_admin': session['is_admin']
    })

@app.route('/api/users/<int:user_id>/admin', methods=['PUT'])
@admin_required
def update_user_admin_status(user_id):
    """更新用户的管理员权限状态"""
    data = request.json
    is_admin = data.get('is_admin', False)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET is_admin = %s WHERE id = %s',
            (is_admin, user_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({'success': True})
    except Error as e:
        print(f"更新用户管理员权限失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>/password', methods=['PUT'])
@admin_required
def reset_user_password(user_id):
    """强制修改用户密码"""
    data = request.json
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'error': '密码不能为空'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        # 加密新密码
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET password = %s WHERE id = %s',
            (hashed_password.decode('utf-8'), user_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({'success': True})
    except Error as e:
        print(f"修改用户密码失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    """禁用/启用用户"""
    data = request.json
    disabled = data.get('disabled', False)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET disabled = %s WHERE id = %s',
            (disabled, user_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({'success': True})
    except Error as e:
        print(f"更新用户状态失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor()
        # 不允许删除admin用户
        cursor.execute('SELECT username FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if user and user[0] == 'admin':
            return jsonify({'error': '不允许删除管理员账号'}), 400
        
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({'success': True})
    except Error as e:
        print(f"删除用户失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users', methods=['GET'])
@login_required
def get_all_users():
    """获取所有用户列表"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, username, nickname FROM users ORDER BY id ASC')
        users = cursor.fetchall()
        return jsonify({'success': True, 'data': users})
    except Error as e:
        print(f"获取用户列表失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/users/change-password', methods=['PUT'])
@login_required
def change_password():
    """修改当前用户密码"""
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': '密码不能为空'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 验证旧密码
        if not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': '旧密码错误'}), 400
        
        # 加密新密码
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute(
            'UPDATE users SET password = %s WHERE id = %s',
            (hashed_password.decode('utf-8'), session['user_id'])
        )
        conn.commit()
        
        return jsonify({'success': True})
    except Error as e:
        print(f"修改密码失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 文件上传 API ==========

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    files = request.files.getlist('file')
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # 保存文件
        file.save(file_path)
        uploaded_files.append(unique_filename)
    
    return jsonify({'success': True, 'files': uploaded_files})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ========== 艺人管理 API ==========

@app.route('/api/artists', methods=['GET'])
def get_artists():
    """获取所有艺人列表"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        # 获取所有艺人基本信息
        cursor.execute('SELECT * FROM artists ORDER BY id DESC')
        artists = cursor.fetchall()
        
        # 为每个艺人获取关联的项目和活动数量
        for artist in artists:
            # 获取项目数量
            cursor.execute('SELECT COUNT(*) as project_count FROM artist_projects WHERE artist_id = %s', (artist['id'],))
            project_count = cursor.fetchone()
            artist['project_count'] = project_count['project_count'] if project_count else 0
            
            # 获取活动数量
            cursor.execute('SELECT COUNT(*) as activity_count FROM artist_activities WHERE artist_id = %s', (artist['id'],))
            activity_count = cursor.fetchone()
            artist['activity_count'] = activity_count['activity_count'] if activity_count else 0
        
        return jsonify({'success': True, 'data': artists})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists/<int:artist_id>', methods=['GET'])
def get_artist(artist_id):
    """获取单个艺人详情"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM artists WHERE id = %s', (artist_id,))
        artist = cursor.fetchone()
        if not artist:
            return jsonify({'error': '艺人不存在'}), 404

        # 获取艺人参与的项目
        cursor.execute('''
            SELECT p.*, ap.role, ap.role_type
            FROM projects p
            JOIN artist_projects ap ON p.id = ap.project_id
            WHERE ap.artist_id = %s
            ORDER BY p.release_date DESC
        ''', (artist_id,))
        projects = cursor.fetchall()
        artist['projects'] = projects

        # 获取艺人参与的活动
        cursor.execute('''
            SELECT a.*, aa.role, aa.performance_notes
            FROM activities a
            JOIN artist_activities aa ON a.id = aa.activity_id
            WHERE aa.artist_id = %s
            ORDER BY a.activity_date DESC
        ''', (artist_id,))
        activities = cursor.fetchall()
        artist['activities'] = activities

        return jsonify({'success': True, 'data': artist})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists', methods=['POST'])
def create_artist():
    """创建新艺人"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO artists (
                name, real_name, douyin_account, phone, wechat, recruiter, recruitment_status,
                vocal_skill, live_effect_level,
                total_revenue, current_status, singer_attachment, address, household_address,
                willing_offline, exposure_parts, contract_type, remarks, join_date,
                height, weight, birth_date, relationship_status, personality, mbti,
                occupation, skills, fan_name, music_style, expectation, bond,
                ethnicity, art_major, gender
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (
            data.get('name'),
            data.get('real_name'),
            data.get('douyin_account'),
            data.get('phone'),
            data.get('wechat'),
            data.get('recruiter'),
            data.get('recruitment_status'),
            data.get('vocal_skill'),
            data.get('live_effect_level'),
            float(data.get('total_revenue', 0)),
            data.get('current_status'),
            data.get('singer_attachment'),
            data.get('address'),
            data.get('household_address'),
            data.get('willing_offline'),
            data.get('exposure_parts'),
            data.get('contract_type'),
            data.get('remarks'),
            data.get('join_date'),
            float(data.get('height', 0)) if data.get('height') else None,
            float(data.get('weight', 0)) if data.get('weight') else None,
            data.get('birth_date'),
            data.get('relationship_status'),
            data.get('personality'),
            data.get('mbti'),
            data.get('occupation'),
            data.get('skills'),
            data.get('fan_name'),
            data.get('music_style'),
            data.get('expectation'),
            data.get('bond'),
            data.get('ethnicity'),
            data.get('art_major'),
            data.get('gender')
        ))
        conn.commit()
        
        # 记录操作日志
        artist_id = cursor.lastrowid
        operator = data.get('operator', '未知')
        artist_name = data.get('name', '未知')
        operation_content = f"新增艺人：{artist_name} (ID: {artist_id})"
        log_operation(operator, '新增', artist_id, artist_name, operation_content)
        
        return jsonify({'success': True, 'data': {'id': artist_id}})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists/<int:artist_id>', methods=['PUT'])
def update_artist(artist_id):
    """更新艺人信息"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        
        # 获取原始艺人信息用于比较
        cursor.execute('SELECT * FROM artists WHERE id = %s', (artist_id,))
        original_artist = cursor.fetchone()
        if not original_artist:
            return jsonify({'error': '艺人不存在'}), 404
        
        original_name = original_artist[1]  # name字段在第2列
        
        # 更新艺人信息
        query = '''
            UPDATE artists SET
                name = %s, real_name = %s, douyin_account = %s, phone = %s, wechat = %s, recruiter = %s, recruitment_status = %s,
                vocal_skill = %s, live_effect_level = %s, total_revenue = %s, current_status = %s,
                singer_attachment = %s, address = %s, household_address = %s,
                willing_offline = %s, exposure_parts = %s, contract_type = %s,
                remarks = %s, join_date = %s, height = %s, weight = %s,
                birth_date = %s, relationship_status = %s, personality = %s,
                mbti = %s, occupation = %s, skills = %s, fan_name = %s,
                music_style = %s, expectation = %s, bond = %s,
                ethnicity = %s, art_major = %s, gender = %s
            WHERE id = %s
        '''
        cursor.execute(query, (
            data.get('name'),
            data.get('real_name'),
            data.get('douyin_account'),
            data.get('phone'),
            data.get('wechat'),
            data.get('recruiter'),
            data.get('recruitment_status'),
            data.get('vocal_skill'),
            data.get('live_effect_level'),
            float(data.get('total_revenue', 0)),
            data.get('current_status'),
            data.get('singer_attachment'),
            data.get('address'),
            data.get('household_address'),
            data.get('willing_offline'),
            data.get('exposure_parts'),
            data.get('contract_type'),
            data.get('remarks'),
            data.get('join_date'),
            float(data.get('height', 0)) if data.get('height') else None,
            float(data.get('weight', 0)) if data.get('weight') else None,
            data.get('birth_date'),
            data.get('relationship_status'),
            data.get('personality'),
            data.get('mbti'),
            data.get('occupation'),
            data.get('skills'),
            data.get('fan_name'),
            data.get('music_style'),
            data.get('expectation'),
            data.get('bond'),
            data.get('ethnicity'),
            data.get('art_major'),
            data.get('gender'),
            artist_id
        ))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '艺人不存在'}), 404
        
        # 记录操作日志
        operator = data.get('operator', '未知')
        artist_name = data.get('name', original_name)
        operation_content = f"修改艺人：{artist_name} (ID: {artist_id})"
        log_operation(operator, '修改', artist_id, artist_name, operation_content)
        
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    """删除艺人"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        
        # 获取艺人名称和操作人信息
        cursor.execute('SELECT name FROM artists WHERE id = %s', (artist_id,))
        artist = cursor.fetchone()
        if not artist:
            return jsonify({'error': '艺人不存在'}), 404
        
        artist_name = artist[0]
        data = request.json
        operator = data.get('operator', '未知') if data else '未知'
        
        # 删除关联的艺人活动
        cursor.execute('DELETE FROM artist_activities WHERE artist_id = %s', (artist_id,))
        
        # 删除关联的艺人项目
        cursor.execute('DELETE FROM artist_projects WHERE artist_id = %s', (artist_id,))
        
        # 删除艺人
        cursor.execute('DELETE FROM artists WHERE id = %s', (artist_id,))
        
        conn.commit()
        
        # 记录操作日志
        operation_content = f"删除艺人：{artist_name} (ID: {artist_id})"
        log_operation(operator, '删除', artist_id, artist_name, operation_content)
        
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists/<int:artist_id>/logs', methods=['GET'])
def get_artist_logs(artist_id):
    """获取艺人操作日志"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, operation_time, operator, operation_type, operation_content
            FROM operation_logs
            WHERE artist_id = %s
            ORDER BY operation_time DESC
        ''', (artist_id,))
        logs = cursor.fetchall()
        return jsonify({'success': True, 'data': logs})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists/<int:artist_id>/follow-ups', methods=['GET'])
def get_artist_follow_ups(artist_id):
    """获取艺人跟进记录"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, content, operator, created_at
            FROM artist_follow_ups
            WHERE artist_id = %s
            ORDER BY created_at DESC
        ''', (artist_id,))
        follow_ups = cursor.fetchall()
        return jsonify({'success': True, 'data': follow_ups})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artists/<int:artist_id>/follow-ups', methods=['POST'])
def add_artist_follow_up(artist_id):
    """添加艺人跟进记录"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO artist_follow_ups (artist_id, content, operator)
            VALUES (%s, %s, %s)
        '''
        cursor.execute(query, (
            artist_id,
            data.get('content'),
            data.get('operator', '未知')
        ))
        conn.commit()
        return jsonify({'success': True, 'data': {'id': cursor.lastrowid}})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/follow-ups/<int:id>', methods=['DELETE'])
def delete_follow_up(id):
    """删除跟进记录"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM artist_follow_ups WHERE id = %s', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '记录不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/follow-ups/<int:id>', methods=['PUT'])
def update_follow_up(id):
    """更新跟进记录"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE artist_follow_ups 
            SET content = %s 
            WHERE id = %s
        ''', (data.get('content'), id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '记录不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 批量上传 API ==========

import csv
from io import StringIO
import urllib.parse

@app.route('/api/artists/template', methods=['GET'])
def get_artist_template():
    """下载艺人信息模板"""
    # 创建CSV文件内容
    fields = [
        '艺名', '真名', '抖音号', '性别', '民族', '艺术专业', '唱功', '直播效果等级',
        '总流水(元)上月', '当前状态', '住址', '户籍地', '是否愿意线下', '可露出部分',
        '签约类型', '备注信息', '入会时间', '身高(cm)', '体重(kg)', '生日',
        '感情情况', '性格', 'MBTI', '职业', '技能', '粉丝名', '曲风', '期望', '羁绊'
    ]
    
    # 创建内存文件对象
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(fields)
    
    # 写入示例数据
    writer.writerow([
        '示例艺人', '张三', 'example_douyin', '男', '汉族', '音乐表演', '专业', 'S级',
        '10000.00', '活跃', '北京市朝阳区', '北京市朝阳区', '是', '面部,上半身',
        '独家签约', '示例备注', '2023-01-01', '175.5', '65.8', '1995-01-01',
        '单身', '开朗', 'INTJ', '歌手', '钢琴,吉他', '粉丝团', '流行', '成为知名歌手', '与粉丝的羁绊'
    ])
    
    # 设置响应头
    output.seek(0)
    filename = '艺人信息模板.csv'
    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={urllib.parse.quote(filename)}'
        }
    )
    return response

@app.route('/api/artists/bulk', methods=['POST'])
def bulk_upload_artists():
    """批量上传艺人信息"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    operator = request.form.get('operator', '未知')
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    try:
        # 读取CSV文件
        stream = StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        
        # 字段映射：模板字段 -> 数据库字段
        field_mapping = {
            '艺名': 'name',
            '真名': 'real_name',
            '抖音号': 'douyin_account',
            '性别': 'gender',
            '民族': 'ethnicity',
            '艺术专业': 'art_major',
            '唱功': 'vocal_skill',
            '直播效果等级': 'live_effect_level',
            '总流水(元)上月': 'total_revenue',
            '当前状态': 'current_status',
            '住址': 'address',
            '户籍地': 'household_address',
            '是否愿意线下': 'willing_offline',
            '可露出部分': 'exposure_parts',
            '签约类型': 'contract_type',
            '备注信息': 'remarks',
            '入会时间': 'join_date',
            '身高(cm)': 'height',
            '体重(kg)': 'weight',
            '生日': 'birth_date',
            '感情情况': 'relationship_status',
            '性格': 'personality',
            'MBTI': 'mbti',
            '职业': 'occupation',
            '技能': 'skills',
            '粉丝名': 'fan_name',
            '曲风': 'music_style',
            '期望': 'expectation',
            '羁绊': 'bond'
        }
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        success_count = 0
        error_count = 0
        
        for row in reader:
            try:
                # 转换字段名
                data = {}
                for template_field, db_field in field_mapping.items():
                    if template_field in row:
                        data[db_field] = row[template_field] or None
                
                # 确保必填字段存在
                if not data.get('name'):
                    error_count += 1
                    continue
                
                # 转换数值类型
                if data.get('total_revenue'):
                    data['total_revenue'] = float(data['total_revenue'])
                if data.get('height'):
                    data['height'] = float(data['height'])
                if data.get('weight'):
                    data['weight'] = float(data['weight'])
                
                # 插入或更新艺人信息
                query = '''
                    INSERT INTO artists (
                        name, real_name, douyin_account, gender, ethnicity, art_major, 
                        vocal_skill, live_effect_level, total_revenue, current_status, 
                        address, household_address, willing_offline, exposure_parts, 
                        contract_type, remarks, join_date, height, weight, birth_date, 
                        relationship_status, personality, mbti, occupation, skills, 
                        fan_name, music_style, expectation, bond
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON DUPLICATE KEY UPDATE
                        real_name = VALUES(real_name),
                        douyin_account = VALUES(douyin_account),
                        gender = VALUES(gender),
                        ethnicity = VALUES(ethnicity),
                        art_major = VALUES(art_major),
                        vocal_skill = VALUES(vocal_skill),
                        live_effect_level = VALUES(live_effect_level),
                        total_revenue = VALUES(total_revenue),
                        current_status = VALUES(current_status),
                        address = VALUES(address),
                        household_address = VALUES(household_address),
                        willing_offline = VALUES(willing_offline),
                        exposure_parts = VALUES(exposure_parts),
                        contract_type = VALUES(contract_type),
                        remarks = VALUES(remarks),
                        join_date = VALUES(join_date),
                        height = VALUES(height),
                        weight = VALUES(weight),
                        birth_date = VALUES(birth_date),
                        relationship_status = VALUES(relationship_status),
                        personality = VALUES(personality),
                        mbti = VALUES(mbti),
                        occupation = VALUES(occupation),
                        skills = VALUES(skills),
                        fan_name = VALUES(fan_name),
                        music_style = VALUES(music_style),
                        expectation = VALUES(expectation),
                        bond = VALUES(bond)
                '''
                
                cursor.execute(query, (
                    data.get('name'),
                    data.get('real_name'),
                    data.get('douyin_account'),
                    data.get('gender'),
                    data.get('ethnicity'),
                    data.get('art_major'),
                    data.get('vocal_skill'),
                    data.get('live_effect_level'),
                    data.get('total_revenue'),
                    data.get('current_status'),
                    data.get('address'),
                    data.get('household_address'),
                    data.get('willing_offline'),
                    data.get('exposure_parts'),
                    data.get('contract_type'),
                    data.get('remarks'),
                    data.get('join_date'),
                    data.get('height'),
                    data.get('weight'),
                    data.get('birth_date'),
                    data.get('relationship_status'),
                    data.get('personality'),
                    data.get('mbti'),
                    data.get('occupation'),
                    data.get('skills'),
                    data.get('fan_name'),
                    data.get('music_style'),
                    data.get('expectation'),
                    data.get('bond')
                ))
                
                success_count += 1
                
                # 记录操作日志
                if cursor.lastrowid > 0:
                    log_operation(operator, '新增', cursor.lastrowid, data.get('name'), f'批量新增艺人：{data.get("name")}')
                else:
                    # 获取更新的艺人ID
                    cursor.execute('SELECT id FROM artists WHERE name = %s', (data.get('name'),))
                    updated_artist = cursor.fetchone()
                    if updated_artist:
                        log_operation(operator, '修改', updated_artist[0], data.get('name'), f'批量修改艺人：{data.get("name")}')
            except Exception as e:
                error_count += 1
                print(f"处理行失败: {e}")
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'success_count': success_count,
            'error_count': error_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ========== 项目管理 API ==========

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有项目列表"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        search = request.args.get('search', '')
        
        if search:
            # 带搜索条件的查询
            query = '''
                SELECT p.*, COUNT(ap.artist_id) as artist_count
                FROM projects p
                LEFT JOIN artist_projects ap ON p.id = ap.project_id
                WHERE p.title LIKE %s OR p.description LIKE %s
                GROUP BY p.id
                ORDER BY p.id DESC
            '''
            search_param = f"%{search}%"
            cursor.execute(query, (search_param, search_param))
        else:
            # 获取所有项目信息和对应的艺人数量
            query = '''
                SELECT p.*, COUNT(ap.artist_id) as artist_count
                FROM projects p
                LEFT JOIN artist_projects ap ON p.id = ap.project_id
                GROUP BY p.id
                ORDER BY p.id DESC
            '''
            cursor.execute(query)
        
        projects = cursor.fetchall()
        return jsonify({'success': True, 'data': projects})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """获取单个项目详情"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
        project = cursor.fetchone()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 获取参与该项目的艺人
        cursor.execute('''
            SELECT a.*, ap.role, ap.role_type
            FROM artists a
            JOIN artist_projects ap ON a.id = ap.artist_id
            WHERE ap.project_id = %s
        ''', (project_id,))
        artists = cursor.fetchall()
        project['artists'] = artists

        return jsonify({'success': True, 'data': project})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO projects (title, type, release_date, description, director, project_leader, project_attachment, expected_start_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (
            data.get('title'),
            data.get('type'),
            data.get('release_date'),
            data.get('description'),
            data.get('director'),
            data.get('project_leader'),
            data.get('project_attachment'),
            data.get('expected_start_date')
        ))
        conn.commit()
        return jsonify({'success': True, 'data': {'id': cursor.lastrowid}})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目信息"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            UPDATE projects
            SET title = %s, type = %s, release_date = %s, description = %s, director = %s, 
                project_leader = %s, project_attachment = %s, expected_start_date = %s
            WHERE id = %s
        '''
        cursor.execute(query, (
            data.get('title'),
            data.get('type'),
            data.get('release_date'),
            data.get('description'),
            data.get('director'),
            data.get('project_leader'),
            data.get('project_attachment'),
            data.get('expected_start_date'),
            project_id
        ))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '项目不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '项目不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 活动管理 API ==========

@app.route('/api/activities', methods=['GET'])
def get_activities():
    """获取所有活动列表"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        search = request.args.get('search', '')
        
        if search:
            # 带搜索条件的查询
            query = '''
                SELECT a.*, COUNT(aa.artist_id) as artist_count
                FROM activities a
                LEFT JOIN artist_activities aa ON a.id = aa.activity_id
                WHERE a.title LIKE %s OR a.description LIKE %s OR a.location LIKE %s
                GROUP BY a.id
                ORDER BY a.activity_date DESC
            '''
            search_param = f"%{search}%"
            cursor.execute(query, (search_param, search_param, search_param))
        else:
            # 获取所有活动信息和对应的艺人数量
            query = '''
                SELECT a.*, COUNT(aa.artist_id) as artist_count
                FROM activities a
                LEFT JOIN artist_activities aa ON a.id = aa.activity_id
                GROUP BY a.id
                ORDER BY a.activity_date DESC
            '''
            cursor.execute(query)
        
        activities = cursor.fetchall()
        return jsonify({'success': True, 'data': activities})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/activities/<int:activity_id>', methods=['GET'])
def get_activity(activity_id):
    """获取单个活动详情"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM activities WHERE id = %s', (activity_id,))
        activity = cursor.fetchone()
        if not activity:
            return jsonify({'error': '活动不存在'}), 404

        # 获取参与该活动的艺人
        cursor.execute('''
            SELECT a.*, aa.role, aa.performance_notes
            FROM artists a
            JOIN artist_activities aa ON a.id = aa.artist_id
            WHERE aa.activity_id = %s
        ''', (activity_id,))
        artists = cursor.fetchall()
        activity['artists'] = artists

        return jsonify({'success': True, 'data': activity})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/activities', methods=['POST'])
def create_activity():
    """创建新活动"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO activities (title, type, activity_date, location, description, organizer, activity_leader, activity_attachment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (
            data.get('title'),
            data.get('type'),
            data.get('activity_date'),
            data.get('location'),
            data.get('description'),
            data.get('organizer'),
            data.get('activity_leader'),
            data.get('activity_attachment')
        ))
        conn.commit()
        return jsonify({'success': True, 'data': {'id': cursor.lastrowid}})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/activities/<int:activity_id>', methods=['PUT'])
def update_activity(activity_id):
    """更新活动信息"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            UPDATE activities
            SET title = %s, type = %s, activity_date = %s, location = %s, description = %s, organizer = %s, 
                activity_leader = %s, activity_attachment = %s
            WHERE id = %s
        '''
        cursor.execute(query, (
            data.get('title'),
            data.get('type'),
            data.get('activity_date'),
            data.get('location'),
            data.get('description'),
            data.get('organizer'),
            data.get('activity_leader'),
            data.get('activity_attachment'),
            activity_id
        ))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '活动不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/activities/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    """删除活动"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM activities WHERE id = %s', (activity_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '活动不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 行程管理 API ==========

@app.route('/api/projects/<int:project_id>/time-range', methods=['PUT'])
@login_required
@db_operation
def update_project_time_range(conn, cursor, project_id):
    """更新项目时间范围"""
    data = request.json
    
    query = '''
        UPDATE projects
        SET start_date = %s, end_date = %s
        WHERE id = %s
    '''
    cursor.execute(query, (data.get('start_date'), data.get('end_date'), project_id))
    
    if cursor.rowcount == 0:
        return jsonify({'error': '项目不存在'}), 404
    
    return jsonify({'success': True})

@app.route('/api/activities/<int:activity_id>/time-range', methods=['PUT'])
@login_required
@db_operation
def update_activity_time_range(conn, cursor, activity_id):
    """更新活动时间范围"""
    data = request.json
    
    query = '''
        UPDATE activities
        SET start_date = %s, end_date = %s
        WHERE id = %s
    '''
    cursor.execute(query, (data.get('start_date'), data.get('end_date'), activity_id))
    
    if cursor.rowcount == 0:
        return jsonify({'error': '活动不存在'}), 404
    
    return jsonify({'success': True})

# 通用行程获取函数
def get_artist_schedule_list(conn, cursor, artist_id, start_date=None, end_date=None, order_by='DESC'):
    """获取艺人行程列表，支持时间范围过滤和排序"""
    # 构建时间范围条件
    time_condition = ""
    params = [artist_id]
    
    if start_date and end_date:
        time_condition = "AND ((start_date BETWEEN %s AND %s) OR (end_date BETWEEN %s AND %s) OR (start_date <= %s AND end_date >= %s))"
        params.extend([start_date, end_date, start_date, end_date, start_date, end_date])
    
    # 获取艺人参与的项目行程
    project_schedule_query = f'''
        SELECT 
            'project' as type,
            p.id as related_id,
            p.title as title,
            p.start_date,
            p.end_date,
            p.description,
            p.schedule_info
        FROM projects p
        JOIN artist_projects ap ON p.id = ap.project_id
        WHERE ap.artist_id = %s
        {time_condition}
        ORDER BY p.start_date {order_by}
    '''
    cursor.execute(project_schedule_query, params)
    project_schedule = cursor.fetchall()
    
    # 获取艺人参与的活动行程
    activity_schedule_query = f'''
        SELECT 
            'activity' as type,
            a.id as related_id,
            a.title as title,
            a.start_date,
            a.end_date,
            a.description,
            a.schedule_info
        FROM activities a
        JOIN artist_activities aa ON a.id = aa.activity_id
        WHERE aa.artist_id = %s
        {time_condition}
        ORDER BY a.start_date {order_by}
    '''
    cursor.execute(activity_schedule_query, params)
    activity_schedule = cursor.fetchall()
    
    # 合并行程数据
    schedule = project_schedule + activity_schedule
    # 按开始时间排序
    schedule.sort(key=lambda x: x['start_date'] if x['start_date'] else datetime.max)
    
    return schedule

@app.route('/api/artists/<int:artist_id>/schedule', methods=['GET'])
@login_required
@db_operation
def get_artist_schedule(conn, cursor, artist_id):
    """获取艺人行程列表"""
    schedule = get_artist_schedule_list(conn, cursor, artist_id)
    return jsonify({'success': True, 'data': schedule})

@app.route('/api/artists/<int:artist_id>/schedule/month', methods=['GET'])
@login_required
@db_operation
def get_artist_monthly_schedule(conn, cursor, artist_id):
    """获取艺人月度行程"""
    month = request.args.get('month')
    
    if not month:
        # 默认使用当前月份
        month = datetime.now().strftime('%Y-%m')
    
    # 构建月份的开始和结束时间
    start_of_month = f"{month}-01"
    end_of_month = datetime.strptime(month, '%Y-%m').strftime('%Y-%m-%d')
    end_of_month = datetime.strptime(end_of_month, '%Y-%m-%d').replace(day=calendar.monthrange(int(month.split('-')[0]), int(month.split('-')[1]))[1])
    end_of_month = end_of_month.strftime('%Y-%m-%d')
    
    # 使用通用行程获取函数
    schedule = get_artist_schedule_list(conn, cursor, artist_id, start_of_month, end_of_month, 'ASC')
    
    return jsonify({'success': True, 'data': schedule})

@app.route('/api/schedule/stats/<int:artist_id>', methods=['GET'])
@login_required
@db_operation
def get_schedule_stats(conn, cursor, artist_id):
    """获取艺人行程统计"""
    # 统计艺人参与的项目数量
    cursor.execute('SELECT COUNT(*) as project_count FROM artist_projects WHERE artist_id = %s', (artist_id,))
    project_count = cursor.fetchone()['project_count']
    
    # 统计艺人参与的活动数量
    cursor.execute('SELECT COUNT(*) as activity_count FROM artist_activities WHERE artist_id = %s', (artist_id,))
    activity_count = cursor.fetchone()['activity_count']
    
    # 统计本月行程数量
    current_month = datetime.now().strftime('%Y-%m')
    start_of_month = f"{current_month}-01"
    end_of_month = datetime.strptime(current_month, '%Y-%m').strftime('%Y-%m-%d')
    end_of_month = datetime.strptime(end_of_month, '%Y-%m-%d').replace(day=calendar.monthrange(int(current_month.split('-')[0]), int(current_month.split('-')[1]))[1])
    end_of_month = end_of_month.strftime('%Y-%m-%d')
    
    # 本月项目数量
    cursor.execute('''
        SELECT COUNT(*) as month_project_count
        FROM projects p
        JOIN artist_projects ap ON p.id = ap.project_id
        WHERE ap.artist_id = %s
        AND ((p.start_date BETWEEN %s AND %s) OR (p.end_date BETWEEN %s AND %s) OR (p.start_date <= %s AND p.end_date >= %s))
    ''', (artist_id, start_of_month, end_of_month, start_of_month, end_of_month, start_of_month, end_of_month))
    month_project_count = cursor.fetchone()['month_project_count']
    
    # 本月活动数量
    cursor.execute('''
        SELECT COUNT(*) as month_activity_count
        FROM activities a
        JOIN artist_activities aa ON a.id = aa.activity_id
        WHERE aa.artist_id = %s
        AND ((a.start_date BETWEEN %s AND %s) OR (a.end_date BETWEEN %s AND %s) OR (a.start_date <= %s AND a.end_date >= %s))
    ''', (artist_id, start_of_month, end_of_month, start_of_month, end_of_month, start_of_month, end_of_month))
    month_activity_count = cursor.fetchone()['month_activity_count']
    
    stats = {
        'total_projects': project_count,
        'total_activities': activity_count,
        'total_schedule': project_count + activity_count,
        'month_projects': month_project_count,
        'month_activities': month_activity_count,
        'month_schedule': month_project_count + month_activity_count
    }
    
    return jsonify({'success': True, 'data': stats})

@app.route('/api/schedule/conflict-check', methods=['POST'])
@login_required
@db_operation
def check_schedule_conflict(conn, cursor):
    """检测行程冲突"""
    data = request.json
    
    artist_id = data.get('artist_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    related_id = data.get('related_id')
    related_type = data.get('related_type')  # project或activity
    
    if not artist_id or not start_date or not end_date:
        return jsonify({'error': '缺少必要参数'}), 400
    
    conflicts = []
    
    # 检查项目冲突
    project_conflict_query = '''
        SELECT 
            'project' as type,
            p.id as related_id,
            p.title as title,
            p.start_date,
            p.end_date
        FROM projects p
        JOIN artist_projects ap ON p.id = ap.project_id
        WHERE ap.artist_id = %s
        AND ((p.start_date BETWEEN %s AND %s) OR (p.end_date BETWEEN %s AND %s) OR (p.start_date <= %s AND p.end_date >= %s))
        '''
    
    # 如果是更新现有项目，排除自身
    if related_type == 'project' and related_id:
        project_conflict_query += ' AND p.id != %s'
        cursor.execute(project_conflict_query, (artist_id, start_date, end_date, start_date, end_date, start_date, end_date, related_id))
    else:
        cursor.execute(project_conflict_query, (artist_id, start_date, end_date, start_date, end_date, start_date, end_date))
    
    project_conflicts = cursor.fetchall()
    conflicts.extend(project_conflicts)
    
    # 检查活动冲突
    activity_conflict_query = '''
        SELECT 
            'activity' as type,
            a.id as related_id,
            a.title as title,
            a.start_date,
            a.end_date
        FROM activities a
        JOIN artist_activities aa ON a.id = aa.activity_id
        WHERE aa.artist_id = %s
        AND ((a.start_date BETWEEN %s AND %s) OR (a.end_date BETWEEN %s AND %s) OR (a.start_date <= %s AND a.end_date >= %s))
        '''
    
    # 如果是更新现有活动，排除自身
    if related_type == 'activity' and related_id:
        activity_conflict_query += ' AND a.id != %s'
        cursor.execute(activity_conflict_query, (artist_id, start_date, end_date, start_date, end_date, start_date, end_date, related_id))
    else:
        cursor.execute(activity_conflict_query, (artist_id, start_date, end_date, start_date, end_date, start_date, end_date))
    
    activity_conflicts = cursor.fetchall()
    conflicts.extend(activity_conflicts)
    
    return jsonify({
        'success': True,
        'has_conflict': len(conflicts) > 0,
        'conflicts': conflicts
    })

@app.route('/api/schedule/export/<int:artist_id>', methods=['GET'])
@login_required
def export_artist_schedule(artist_id):
    """导出艺人行程"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        # 这里简化实现，实际应该使用Excel库生成Excel文件
        # 为了演示，返回JSON格式的行程数据
        return get_artist_schedule(artist_id)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/schedule/monthly', methods=['GET'])
@login_required
def get_monthly_schedule():
    """获取所有艺人月度行程"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        month = request.args.get('month')
        
        if not month:
            # 默认使用当前月份
            month = datetime.now().strftime('%Y-%m')
        
        start_of_month = f"{month}-01"
        end_of_month = datetime.strptime(month, '%Y-%m').strftime('%Y-%m-%d')
        end_of_month = datetime.strptime(end_of_month, '%Y-%m-%d').replace(day=calendar.monthrange(int(month.split('-')[0]), int(month.split('-')[1]))[1])
        end_of_month = end_of_month.strftime('%Y-%m-%d')
        
        # 获取所有艺人的项目行程，使用release_date作为默认时间
        project_schedule_query = '''
            SELECT 
                a.id as artist_id,
                a.name as artist_name,
                'project' as type,
                p.id as related_id,
                p.title as title,
                COALESCE(p.start_date, p.release_date) as start_date,
                COALESCE(p.end_date, p.release_date) as end_date,
                p.description
            FROM artists a
            JOIN artist_projects ap ON a.id = ap.artist_id
            JOIN projects p ON ap.project_id = p.id
            WHERE ((COALESCE(p.start_date, p.release_date) BETWEEN %s AND %s) OR 
                   (COALESCE(p.end_date, p.release_date) BETWEEN %s AND %s) OR 
                   (COALESCE(p.start_date, p.release_date) <= %s AND COALESCE(p.end_date, p.release_date) >= %s))
            ORDER BY COALESCE(p.start_date, p.release_date) ASC
        '''
        cursor.execute(project_schedule_query, (start_of_month, end_of_month, start_of_month, end_of_month, start_of_month, end_of_month))
        project_schedule = cursor.fetchall()
        
        # 获取所有艺人的活动行程，使用activity_date作为默认时间
        activity_schedule_query = '''
            SELECT 
                a.id as artist_id,
                a.name as artist_name,
                'activity' as type,
                act.id as related_id,
                act.title as title,
                COALESCE(act.start_date, act.activity_date) as start_date,
                COALESCE(act.end_date, act.activity_date) as end_date,
                act.description
            FROM artists a
            JOIN artist_activities aa ON a.id = aa.artist_id
            JOIN activities act ON aa.activity_id = act.id
            WHERE ((COALESCE(act.start_date, act.activity_date) BETWEEN %s AND %s) OR 
                   (COALESCE(act.end_date, act.activity_date) BETWEEN %s AND %s) OR 
                   (COALESCE(act.start_date, act.activity_date) <= %s AND COALESCE(act.end_date, act.activity_date) >= %s))
            ORDER BY COALESCE(act.start_date, act.activity_date) ASC
        '''
        cursor.execute(activity_schedule_query, (start_of_month, end_of_month, start_of_month, end_of_month, start_of_month, end_of_month))
        activity_schedule = cursor.fetchall()
        
        # 合并行程数据
        schedule = project_schedule + activity_schedule
        
        # 处理行程数据，添加has_conflict字段和格式化时间
        processed_schedule = []
        for item in schedule:
            # 格式化日期时间
            start_date = item['start_date']
            end_date = item['end_date']
            
            # 处理日期时间格式
            if isinstance(start_date, datetime):
                start_time = start_date.strftime('%Y-%m-%d %H:%M')
            else:
                start_time = start_date
            
            if isinstance(end_date, datetime):
                end_time = end_date.strftime('%Y-%m-%d %H:%M')
            else:
                end_time = end_date
            
            # 添加has_conflict字段，这里暂时设为False，实际需要根据冲突检测结果设置
            processed_item = {
                **item,
                'start_time': start_time,
                'end_time': end_time,
                'has_conflict': False
            }
            
            processed_schedule.append(processed_item)
        
        return jsonify({'success': True, 'data': processed_schedule})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 艺人项目关联管理 API ==========

@app.route('/api/artist-projects', methods=['POST'])
def add_artist_project():
    """添加艺人与项目的关联"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO artist_projects (artist_id, project_id, role, role_type)
            VALUES (%s, %s, %s, %s)
        '''
        cursor.execute(query, (
            data.get('artist_id'),
            data.get('project_id'),
            data.get('role'),
            data.get('role_type')
        ))
        conn.commit()
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artist-projects/<int:id>', methods=['DELETE'])
def remove_artist_project(id):
    """删除艺人与项目的关联"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM artist_projects WHERE id = %s', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '关联不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 艺人活动关联管理 API ==========

@app.route('/api/artist-activities', methods=['POST'])
def add_artist_activity():
    """添加艺人与活动的关联"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO artist_activities (artist_id, activity_id, role, performance_notes, schedule_progress)
            VALUES (%s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (
            data.get('artist_id'),
            data.get('activity_id'),
            data.get('role'),
            data.get('performance_notes'),
            data.get('schedule_progress')
        ))
        conn.commit()
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/artist-activities/<int:id>', methods=['PUT'])
def update_artist_activity(id):
    """更新艺人与活动的关联信息"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        query = '''
            UPDATE artist_activities
            SET role = %s, performance_notes = %s, schedule_progress = %s
            WHERE id = %s
        '''
        cursor.execute(query, (
            data.get('role'),
            data.get('performance_notes'),
            data.get('schedule_progress'),
            id
        ))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '关联不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/backups/<filename>', methods=['GET'])
def download_backup(filename):
    """提供备份文件下载"""
    backup_dir = '/root/artist-system/备份'
    return send_from_directory(backup_dir, filename, as_attachment=True)

@app.route('/api/artist-activities/<int:id>', methods=['DELETE'])
def remove_artist_activity(id):
    """删除艺人与活动的关联"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM artist_activities WHERE id = %s', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': '关联不存在'}), 404
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 查询 API ==========

@app.route('/api/search/artists-by-project', methods=['GET'])
def search_artists_by_project():
    """通过项目查找参与的艺人"""
    project_title = request.args.get('title', '')
    project_type = request.args.get('type', '')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT DISTINCT a.*
            FROM artists a
            JOIN artist_projects ap ON a.id = ap.artist_id
            JOIN projects p ON ap.project_id = p.id
            WHERE p.title LIKE %s
        '''
        params = [f'%{project_title}%']

        if project_type:
            query += ' AND p.type = %s'
            params.append(project_type)

        cursor.execute(query, params)
        artists = cursor.fetchall()
        return jsonify({'success': True, 'data': artists})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/search/projects-by-artist', methods=['GET'])
def search_projects_by_artist():
    """通过艺人查找参与的项目"""
    artist_name = request.args.get('name', '')
    project_type = request.args.get('type', '')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT DISTINCT p.*, ap.role, ap.role_type
            FROM projects p
            JOIN artist_projects ap ON p.id = ap.project_id
            JOIN artists a ON ap.artist_id = a.id
            WHERE a.name LIKE %s
        '''
        params = [f'%{artist_name}%']

        if project_type:
            query += ' AND p.type = %s'
            params.append(project_type)

        cursor.execute(query, params)
        projects = cursor.fetchall()
        return jsonify({'success': True, 'data': projects})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/search/artists-by-activity', methods=['GET'])
def search_artists_by_activity():
    """通过活动查找参与的艺人"""
    activity_title = request.args.get('title', '')
    activity_type = request.args.get('type', '')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT DISTINCT a.*
            FROM artists a
            JOIN artist_activities aa ON a.id = aa.artist_id
            JOIN activities act ON aa.activity_id = act.id
            WHERE act.title LIKE %s
        '''
        params = [f'%{activity_title}%']

        if activity_type:
            query += ' AND act.type = %s'
            params.append(activity_type)

        cursor.execute(query, params)
        artists = cursor.fetchall()
        return jsonify({'success': True, 'data': artists})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ========== 前端页面路由 ==========

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/artists')
@login_required
def artists_page():
    return render_template('artists.html')

@app.route('/projects')
@login_required
def projects_page():
    return render_template('projects.html')

@app.route('/activities')
@login_required
def activities_page():
    return render_template('activities.html')

@app.route('/search')
@login_required
def search_page():
    return render_template('search.html')

@app.route('/tickets')
@login_required
def tickets_page():
    return render_template('tickets.html')

# ========== 工单系统 API ==========

# 工单编号生成函数
def generate_ticket_no():
    """生成工单编号，格式：WT + 日期 + 4位序号"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)  # 设置cursor返回字典
        # 获取当前日期
        today = datetime.now().strftime('%Y%m%d')
        # 生成工单前缀
        prefix = f"WT{today}"
        
        # 查询今天的最大工单编号
        query = "SELECT MAX(ticket_no) AS max_no FROM work_tickets WHERE ticket_no LIKE %s"
        cursor.execute(query, (f"{prefix}%",))
        result = cursor.fetchone()
        
        if result and result['max_no']:
            # 提取序号部分并加1
            seq = int(result['max_no'][-4:]) + 1
        else:
            # 今天没有工单，从0001开始
            seq = 1
        
        # 生成完整工单编号
        ticket_no = f"{prefix}{seq:04d}"
        return ticket_no
    except Error as e:
        print(f"生成工单编号失败: {e}")
        return None
    finally:
        conn.close()

@app.route('/api/tickets', methods=['POST'])
@login_required
@db_operation
def create_ticket(conn, cursor):
    """创建工单"""
    data = request.json
    
    # 生成工单编号
    ticket_no = generate_ticket_no()
    if not ticket_no:
        return jsonify({'error': '生成工单编号失败'}), 500
    
    # 插入工单数据
    query = '''
        INSERT INTO work_tickets (
            ticket_no, artist_id, title, description, ticket_type, priority, 
            status, creator_id, assigned_to, due_date, attachment_path
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(query, (
        ticket_no,
        data.get('artist_id'),
        data.get('title'),
        data.get('description'),
        data.get('ticket_type', '沟通'),
        data.get('priority', '中'),
        data.get('status', '待处理'),
        data.get('creator_id'),
        data.get('assigned_to'),
        data.get('due_date'),
        data.get('attachment_path')
    ))
    
    ticket_id = cursor.lastrowid
    
    # 记录操作日志
    log_ticket_action(conn, cursor, ticket_id, data.get('creator_id'), session.get('nickname', '未知'), 'created')
    
    return jsonify({'success': True, 'data': {'id': ticket_id, 'ticket_no': ticket_no}})

@app.route('/api/tickets', methods=['GET'])
@login_required
@db_operation
def get_tickets(conn, cursor):
    """获取工单列表（支持筛选）"""
    # 构建查询条件
    filters = []
    params = []
    
    # 获取当前登录用户信息
    current_user_id = session.get('user_id')
    current_user_nickname = session.get('nickname')
    
    # 检查是否为管理员
    is_admin = session.get('is_admin', False)
    
    # 权限控制：非管理员只能看到自己创建的工单和被指派的工单
    if not is_admin:
        filters.append("(creator_id = %s OR assigned_to = %s)")
        params.append(current_user_id)
        params.append(current_user_nickname)
    
    # 艺人筛选
    artist_id = request.args.get('artist_id')
    if artist_id:
        filters.append("artist_id = %s")
        params.append(artist_id)
    
    # 类型筛选
    ticket_type = request.args.get('type')
    if ticket_type:
        filters.append("ticket_type = %s")
        params.append(ticket_type)
    
    # 状态筛选
    status = request.args.get('status')
    if status:
        filters.append("status = %s")
        params.append(status)
    
    # 优先级筛选
    priority = request.args.get('priority')
    if priority:
        filters.append("priority = %s")
        params.append(priority)
    
    # 指派人筛选
    assigned_to = request.args.get('assigned_to')
    if assigned_to:
        filters.append("assigned_to = %s")
        params.append(assigned_to)
    
    # 时间范围筛选
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        filters.append("created_at >= %s")
        params.append(start_date)
    if end_date:
        filters.append("created_at <= %s")
        params.append(f"{end_date} 23:59:59")
    
    # 构建完整查询
    base_query = "SELECT * FROM work_tickets"
    if filters:
        where_clause = " WHERE " + " AND ".join(filters)
    else:
        where_clause = ""
    
    query = f"{base_query}{where_clause} ORDER BY created_at DESC"
    cursor.execute(query, params)
    tickets = cursor.fetchall()
    
    return jsonify({'success': True, 'data': tickets})

@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
@login_required
@db_operation
def get_ticket(conn, cursor, ticket_id):
    """获取工单详情"""
    # 获取工单基本信息
    query = "SELECT * FROM work_tickets WHERE id = %s"
    cursor.execute(query, (ticket_id,))
    ticket = cursor.fetchone()
    
    if not ticket:
        return jsonify({'error': '工单不存在'}), 404
    
    # 获取关联的艺人信息
    cursor.execute("SELECT id, name, real_name FROM artists WHERE id = %s", (ticket['artist_id'],))
    artist = cursor.fetchone()
    ticket['artist'] = artist
    
    return jsonify({'success': True, 'data': ticket})

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
@login_required
@db_operation
def update_ticket(conn, cursor, ticket_id):
    """更新工单信息"""
    data = request.json
    
    # 获取原始工单信息
    cursor.execute("SELECT * FROM work_tickets WHERE id = %s", (ticket_id,))
    original_ticket = cursor.fetchone()
    if not original_ticket:
        return jsonify({'error': '工单不存在'}), 404
    
    # 更新工单信息
    query = '''
        UPDATE work_tickets SET 
            title = %s, description = %s, ticket_type = %s, priority = %s, 
            due_date = %s, attachment_path = %s
        WHERE id = %s
    '''
    cursor.execute(query, (
        data.get('title', original_ticket[3]),  # title在第4列
        data.get('description', original_ticket[4]),  # description在第5列
        data.get('ticket_type', original_ticket[5]),  # ticket_type在第6列
        data.get('priority', original_ticket[6]),  # priority在第7列
        data.get('due_date', original_ticket[11]),  # due_date在第12列
        data.get('attachment_path', original_ticket[13]),  # attachment_path在第14列
        ticket_id
    ))
    
    # 记录操作日志
    log_ticket_action(conn, cursor, ticket_id, session.get('user_id'), session.get('nickname', '未知'), 'updated')
    
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
@login_required
@db_operation
def update_ticket_status(conn, cursor, ticket_id):
    """更新工单状态"""
    data = request.json
    new_status = data.get('status')
    
    # 获取原始工单状态
    cursor.execute("SELECT status FROM work_tickets WHERE id = %s", (ticket_id,))
    original_ticket = cursor.fetchone()
    if not original_ticket:
        return jsonify({'error': '工单不存在'}), 404
    
    old_status = original_ticket[0]
    
    # 更新状态
    query = "UPDATE work_tickets SET status = %s"
    params = [new_status, ticket_id]
    
    # 如果状态变为已完成，记录完成时间
    if new_status == '已完成':
        query += ", completed_at = CURRENT_TIMESTAMP"
    
    query += " WHERE id = %s"
    cursor.execute(query, params)
    
    # 记录操作日志
    log_ticket_action(conn, cursor, ticket_id, session.get('user_id'), session.get('nickname', '未知'), 'updated', 'status', old_status, new_status)
    
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/assign', methods=['PUT'])
@login_required
@db_operation
def assign_ticket(conn, cursor, ticket_id):
    """指派工单"""
    data = request.json
    assigned_to = data.get('assigned_to')
    
    # 获取原始指派人
    cursor.execute("SELECT assigned_to FROM work_tickets WHERE id = %s", (ticket_id,))
    original_ticket = cursor.fetchone()
    if not original_ticket:
        return jsonify({'error': '工单不存在'}), 404
    
    old_assigned_to = original_ticket[0]
    
    # 更新指派人
    query = "UPDATE work_tickets SET assigned_to = %s WHERE id = %s"
    cursor.execute(query, (assigned_to, ticket_id))
    
    # 记录操作日志
    log_ticket_action(conn, cursor, ticket_id, session.get('user_id'), session.get('nickname', '未知'), 'assigned', 'assigned_to', old_assigned_to, assigned_to)
    
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/comments', methods=['POST'])
@login_required
@db_operation
def add_ticket_comment(conn, cursor, ticket_id):
    """添加工单评论"""
    data = request.json
    
    # 添加工单评论
    query = '''
        INSERT INTO ticket_comments (ticket_id, commenter_id, commenter_name, content, attachment_path)
        VALUES (%s, %s, %s, %s, %s)
    '''
    cursor.execute(query, (
        ticket_id,
        session.get('user_id'),
        session.get('nickname', '未知'),
        data.get('content'),
        data.get('attachment_path')
    ))
    
    comment_id = cursor.lastrowid
    
    # 记录操作日志
    log_ticket_action(conn, cursor, ticket_id, session.get('user_id'), session.get('nickname', '未知'), 'commented')
    
    return jsonify({'success': True, 'data': {'id': comment_id}})

@app.route('/api/tickets/<int:ticket_id>/comments', methods=['GET'])
@login_required
@db_operation
def get_ticket_comments(conn, cursor, ticket_id):
    """获取工单评论"""
    # 获取工单评论
    query = "SELECT * FROM ticket_comments WHERE ticket_id = %s ORDER BY created_at DESC"
    cursor.execute(query, (ticket_id,))
    comments = cursor.fetchall()
    
    return jsonify({'success': True, 'data': comments})

@app.route('/api/tickets/<int:ticket_id>/logs', methods=['GET'])
@login_required
@db_operation
def get_ticket_logs(conn, cursor, ticket_id):
    """获取工单操作日志"""
    # 获取工单操作日志
    query = "SELECT * FROM ticket_logs WHERE ticket_id = %s ORDER BY created_at DESC"
    cursor.execute(query, (ticket_id,))
    logs = cursor.fetchall()
    
    return jsonify({'success': True, 'data': logs})

@app.route('/api/tickets/stats', methods=['GET'])
@login_required
@db_operation
def get_ticket_stats(conn, cursor):
    """获取工单统计数据"""
    # 统计总数
    cursor.execute("SELECT COUNT(*) as total FROM work_tickets")
    total = cursor.fetchone()['total']
    
    # 按状态统计
    cursor.execute("SELECT status, COUNT(*) as count FROM work_tickets GROUP BY status")
    status_stats = cursor.fetchall()
    
    # 按类型统计
    cursor.execute("SELECT ticket_type, COUNT(*) as count FROM work_tickets GROUP BY ticket_type")
    type_stats = cursor.fetchall()
    
    # 按优先级统计
    cursor.execute("SELECT priority, COUNT(*) as count FROM work_tickets GROUP BY priority")
    priority_stats = cursor.fetchall()
    
    return jsonify({
        'success': True, 
        'data': {
            'total': total,
            'status': status_stats,
            'type': type_stats,
            'priority': priority_stats
        }
    })

@app.route('/api/tickets/stats/my', methods=['GET'])
@login_required
@db_operation
def get_my_ticket_stats(conn, cursor):
    """获取我的工单统计"""
    # 获取当前用户的工单统计
    user_nickname = session.get('nickname')
    
    # 统计我的工单总数
    cursor.execute("SELECT COUNT(*) as total FROM work_tickets WHERE assigned_to = %s", (user_nickname,))
    total = cursor.fetchone()['total']
    
    # 统计我的工单按状态分布
    cursor.execute("SELECT status, COUNT(*) as count FROM work_tickets WHERE assigned_to = %s GROUP BY status", (user_nickname,))
    status_stats = cursor.fetchall()
    
    return jsonify({
        'success': True, 
        'data': {
            'total': total,
            'status': status_stats
        }
    })

if __name__ == '__main__':
    app.run(host='::', port=int(os.getenv("DEPLOY_RUN_PORT", 15500)), debug=False)
