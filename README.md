# 艺人信息系统部署指南

## 项目结构
```
artist-system/
├── backend/             # 后端代码
│   ├── app.py           # Flask应用主文件
│   ├── init_admin.py    # 初始化管理员账号
│   ├── init_user_table.sql  # 用户表初始化SQL
│   ├── schema.sql       # 数据库表结构SQL
│   └── uploads/         # 文件上传目录
├── frontend/            # 前端代码
│   └── templates/       # HTML模板文件
├── requirements.txt     # Python依赖列表
├── supervisor.conf      # Supervisor配置文件
├── start.sh             # 启动脚本
├── restart_service.sh   # 重启服务脚本
├── manage_mariadb.sh    # 数据库管理脚本
├── artis-syste.service  # Systemd服务配置
├── non_docker_deploy.sh # 非Docker部署脚本
└── README.md            # 部署指南
```

## 部署方式

### 非Docker部署

1. **连接到服务器**
   ```bash
   ssh root@your-server-ip
   ```

2. **创建项目目录**
   ```bash
   mkdir -p /root/artist-system
   cd /root/artist-system
   ```

3. **上传项目文件**
   从本地终端执行以下命令：
   ```bash
   scp -r /path/to/artist-system/* root@your-server-ip:/root/artist-system/
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **初始化数据库**
   ```bash
   # 执行数据库初始化脚本
   mysql -u root -p < backend/init_user_table.sql
   mysql -u root -p < backend/schema.sql
   ```

6. **启动服务**
   ```bash
   # 使用启动脚本
   ./start.sh
   
   # 或者使用systemd服务
   systemctl start artist-system
   ```

7. **访问应用**
   - 应用地址：http://your-server-ip:5000
   - 登录账号：admin
   - 登录密码：justin00654

## 服务管理

### 启动服务
```bash
./start.sh
```

### 停止服务
```bash
# 找到进程ID并终止
pkill -f "python.*app.py"
```

### 重启服务
```bash
./start.sh restart
```

### 查看服务状态
```bash
./start.sh status
```

## 数据库管理

### 连接到数据库
```bash
mysql -u artist_user -ppassword -h 127.0.0.1 artist_system
```

### 查看数据库表结构
```sql
SHOW TABLES;
DESCRIBE table_name;
```

### 查看数据
```sql
SELECT * FROM table_name;
```

## 常见问题

1. **无法连接到服务器**
   - 检查IP地址和端口号是否正确
   - 检查服务器防火墙是否开放了相关端口
   - 检查服务器的SSH服务是否运行

2. **应用无法访问**
   - 检查服务是否正在运行
   - 检查服务器防火墙是否开放了5000端口
   - 检查应用日志：`cat logs/app.log`

3. **数据库连接失败**
   - 检查数据库配置是否正确
   - 检查数据库是否正在运行
   - 检查数据库用户权限

## 技术栈

- **后端框架**：Flask 3.0.0
- **数据库**：MySQL 8.0
- **ORM**：MySQL Connector/Python
- **前端**：HTML + JavaScript + CSS
- **认证**：Flask Session + bcrypt

## 功能特性

1. **艺人管理**：添加、编辑、删除艺人信息
2. **项目管理**：添加、编辑、删除项目信息
3. **活动管理**：添加、编辑、删除活动信息
4. **关联管理**：管理艺人与项目、活动的关联
5. **用户管理**：管理系统用户和权限
6. **操作日志**：记录所有操作历史
7. **批量上传**：支持批量上传艺人信息
8. **搜索功能**：支持按多种条件搜索艺人

## 联系方式

如有问题，请联系系统管理员。
