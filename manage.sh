#!/bin/bash

# Artist System 统一管理脚本
# 功能：应用管理、数据库管理、部署、开机自启动配置

# 项目目录
PROJECT_DIR="/root/artist-system"
# 日志目录
LOG_DIR="${PROJECT_DIR}/logs"
# 应用PID文件
APP_PID_FILE="${PROJECT_DIR}/app.pid"
# 应用日志
APP_LOG="${LOG_DIR}/app.log"
APP_ERR_LOG="${LOG_DIR}/app.err.log"
# 管理日志
MANAGE_LOG="${LOG_DIR}/manage.log"
# MariaDB管理日志
MARIADB_LOG="${LOG_DIR}/mariadb.log"

# 创建日志目录
mkdir -p ${LOG_DIR}

# 日志函数
log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${msg}" >> ${MANAGE_LOG}
    echo "${msg}"
}

# 应用管理函数
app_start() {
    log "启动艺人信息系统..."
    
    # 检查是否已运行
    if [ -f ${APP_PID_FILE} ]; then
        local OLD_PID=$(cat ${APP_PID_FILE})
        if ps -p ${OLD_PID} > /dev/null 2>&1; then
            log "✅ 应用已在运行 (PID: ${OLD_PID})"
            return 0
        fi
        rm -f ${APP_PID_FILE}
    fi
    
    # 启动应用
    cd ${PROJECT_DIR}/backend
    nohup python3 app.py > ${APP_LOG} 2> ${APP_ERR_LOG} &
    
    local NEW_PID=$!
    echo ${NEW_PID} > ${APP_PID_FILE}
    
    sleep 2
    
    if ps -p ${NEW_PID} > /dev/null 2>&1; then
        log "✅ 应用启动成功！PID: ${NEW_PID}"
        log "日志文件: ${APP_LOG}"
        log "访问地址: http://localhost:15500"
        return 0
    else
        log "❌ 应用启动失败！"
        return 1
    fi
}

app_stop() {
    log "停止艺人信息系统..."
    
    if [ -f ${APP_PID_FILE} ]; then
        local OLD_PID=$(cat ${APP_PID_FILE})
        if ps -p ${OLD_PID} > /dev/null 2>&1; then
            kill ${OLD_PID} 2>/dev/null
            sleep 2
            kill -9 ${OLD_PID} 2>/dev/null
            log "✅ 应用已停止 (PID: ${OLD_PID})"
        fi
        rm -f ${APP_PID_FILE}
    else
        log "✅ 应用未运行"
    fi
}

app_restart() {
    log "重启艺人信息系统..."
    app_stop
    sleep 1
    app_start
}

app_status() {
    if [ -f ${APP_PID_FILE} ]; then
        local PID=$(cat ${APP_PID_FILE})
        if ps -p ${PID} > /dev/null 2>&1; then
            log "✅ 应用运行中 (PID: ${PID})"
            return 0
        fi
    fi
    log "❌ 应用未运行"
    return 1
}

# 数据库管理函数
db_start() {
    log "启动 MariaDB 服务..."
    
    if systemctl is-active --quiet mariadb; then
        log "✅ MariaDB 已在运行"
        return 0
    fi
    
    systemctl start mariadb
    sleep 2
    
    if systemctl is-active --quiet mariadb; then
        log "✅ MariaDB 启动成功！"
        return 0
    else
        log "❌ MariaDB 启动失败！"
        return 1
    fi
}

db_stop() {
    log "停止 MariaDB 服务..."
    systemctl stop mariadb
    log "✅ MariaDB 已停止"
}

db_restart() {
    log "重启 MariaDB 服务..."
    systemctl restart mariadb
    sleep 2
    
    if systemctl is-active --quiet mariadb; then
        log "✅ MariaDB 重启成功！"
        return 0
    else
        log "❌ MariaDB 重启失败！"
        return 1
    fi
}

db_status() {
    if systemctl is-active --quiet mariadb; then
        log "✅ MariaDB 运行中"
        return 0
    else
        log "❌ MariaDB 未运行"
        return 1
    fi
}

# 部署函数
deploy() {
    log "开始部署艺人信息系统..."
    
    # 1. 安装系统依赖
    log "1. 安装系统依赖..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip mariadb-server
    
    # 2. 配置数据库
    log "2. 配置数据库..."
    sudo service mariadb start
    sleep 5
    
    # 设置数据库用户和密码
    log "   创建数据库和用户..."
    sudo mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS artist_system;
CREATE USER IF NOT EXISTS 'artist_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON artist_system.* TO 'artist_user'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # 导入数据库结构
    log "   导入数据库结构..."
    sudo mysql -u root artist_system < ${PROJECT_DIR}/backend/schema.sql
    
    # 3. 安装Python依赖
    log "3. 安装Python依赖..."
    pip3 install --no-cache-dir -r ${PROJECT_DIR}/requirements.txt
    
    # 4. 初始化管理员账号
    log "4. 初始化管理员账号..."
    python3 ${PROJECT_DIR}/backend/init_admin.py
    
    log "✅ 部署完成！"
    log "应用访问地址: http://localhost:15500"
    log "登录账号: admin"
    log "登录密码: justin00654"
}

# 开机自启动配置
setup_boot() {
    log "配置开机自启动..."
    
    # 创建系统服务文件
    sudo cat > /etc/systemd/system/artist-system.service << 'EOF'
[Unit]
Description=Artist Information System
After=network.target mariadb.service

[Service]
Type=forking
User=root
WorkingDirectory=/root/artist-system
ExecStart=/root/artist-system/manage.sh start all
ExecStop=/root/artist-system/manage.sh stop all
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    
    # 启用服务
    sudo systemctl daemon-reload
    sudo systemctl enable artist-system
    
    log "✅ 开机自启动配置完成！"
}

# 主逻辑
case "$1" in
    # 应用管理
    start)
        if [ "$2" = "all" ]; then
            db_start
            app_start
        else
            app_start
        fi
        ;;
    stop)
        if [ "$2" = "all" ]; then
            app_stop
            db_stop
        else
            app_stop
        fi
        ;;
    restart)
        if [ "$2" = "all" ]; then
            db_restart
            app_restart
        else
            app_restart
        fi
        ;;
    status)
        if [ "$2" = "all" ]; then
            db_status
            app_status
        else
            app_status
        fi
        ;;
    
    # 数据库管理
    db:start)
        db_start
        ;;
    db:stop)
        db_stop
        ;;
    db:restart)
        db_restart
        ;;
    db:status)
        db_status
        ;;
    
    # 部署和配置
    deploy)
        deploy
        ;;
    setup:boot)
        setup_boot
        ;;
    
    # 帮助信息
    help)
        echo "艺人信息系统管理脚本"
        echo ""
        echo "用法: $0 COMMAND [OPTIONS]"
        echo ""
        echo "应用管理命令:"
        echo "  start [all]         启动应用 (添加 all 同时启动数据库)"
        echo "  stop [all]          停止应用 (添加 all 同时停止数据库)"
        echo "  restart [all]       重启应用 (添加 all 同时重启数据库)"
        echo "  status [all]        查看应用状态 (添加 all 同时查看数据库状态)"
        echo ""
        echo "数据库管理命令:"
        echo "  db:start           启动数据库"
        echo "  db:stop            停止数据库"
        echo "  db:restart         重启数据库"
        echo "  db:status          查看数据库状态"
        echo ""
        echo "部署和配置命令:"
        echo "  deploy             部署应用"
        echo "  setup:boot         配置开机自启动"
        echo "  help               显示帮助信息"
        echo ""
        echo "示例:"
        echo "  $0 start all       # 启动应用和数据库"
        echo "  $0 restart         # 只重启应用"
        echo "  $0 db:status       # 查看数据库状态"
        echo "  $0 deploy          # 部署应用"
        ;;
    
    *)
        echo "未知命令: $1"
        echo "使用 '$0 help' 查看帮助信息"
        exit 1
        ;;
esac
