# 艺人管理系统 - 项目文档

## 1. 项目依赖环境

### 1.1 Python依赖库
| 库名称 | 版本 | 用途 |
|--------|------|------|
| Flask | 3.0.0 | Web框架 |
| Flask-CORS | 4.0.0 | 跨域资源共享支持 |
| mysql-connector-python | 8.2.0 | MySQL数据库连接驱动 |
| bcrypt | 4.1.2 | 密码加密与验证 |

### 1.2 系统环境
- **操作系统**：Linux（推荐CentOS/RHEL 7+或Ubuntu 18.04+）
- **数据库**：MySQL 5.7+ 或 MariaDB 10.3+
- **Web服务器**：Flask内置开发服务器（生产环境建议使用Gunicorn+Nginx）
- **Python版本**：Python 3.8+（推荐3.10）
- **外部存储**：SMB/CIFS共享（用于自动备份）

### 1.3 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装系统依赖（用于SMB挂载）
dnf install -y cifs-utils
```

## 2. 系统架构

### 2.1 架构概述
该项目采用**前后端分离**的架构设计，前端使用HTML+JavaScript+CSS，后端使用Python Flask框架，数据库使用MySQL。

### 2.2 目录结构
```
/root/artist-system/
├── backend/                 # 后端代码目录
│   ├── app.py              # 主应用文件，包含所有API端点
│   ├── init_admin.py       # 初始化管理员账号脚本
│   ├── test_db.py          # 数据库连接测试脚本
│   └── test_db_tcp.py      # TCP数据库连接测试脚本
├── frontend/               # 前端代码目录
│   └── templates/          # HTML模板文件
│       ├── activities.html # 活动管理页面
│       ├── artists.html    # 艺人管理页面
│       ├── index.html      # 首页
│       ├── login.html      # 登录页面
│       ├── projects.html   # 项目管理页面
│       ├── search.html     # 搜索页面
│       └── user_management.html # 用户管理页面
├── 备份/                   # SMB挂载的备份目录
├── auto_backup.sh          # 自动备份脚本
├── backup.log              # 备份日志文件
├── db_error.log            # 数据库错误日志
├── MAINTENANCE_LOG.md      # 维护日志
├── requirements.txt        # Python依赖文件
└── schema.sql              # 数据库初始化脚本
```

### 2.3 核心组件
1. **前端组件**：
   - HTML模板：负责页面渲染
   - JavaScript：处理前端交互和API调用
   - CSS：样式设计

2. **后端组件**：
   - Flask应用：处理HTTP请求和响应
   - 数据库连接：管理与MySQL的连接
   - 业务逻辑：实现艺人、项目、活动的CRUD操作
   - 身份验证：用户登录和权限管理

3. **数据库组件**：
   - 艺人表：存储艺人基本信息
   - 项目表：存储项目信息
   - 活动表：存储活动信息
   - 关联表：建立艺人与项目、活动的多对多关系
   - 操作日志表：记录系统操作日志

4. **备份组件**：
   - 自动备份脚本：定期备份数据库和项目文件
   - SMB挂载：将备份存储到远程共享目录

### 2.4 数据流程图
```
用户 → 浏览器 → Flask应用 → 数据库
     ↓         ↓
  HTML模板   API响应
     ↓         ↓
  页面渲染   数据处理
```

## 3. API接口

### 3.1 用户认证API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /login | GET/POST | 用户登录 | 无 |
| /logout | GET | 用户登出 | 登录用户 |
| /api/current-user | GET | 获取当前用户信息 | 登录用户 |
| /users | GET/POST | 用户管理页面 | 管理员 |
| /api/users/<int:user_id>/admin | PUT | 更新用户管理员权限 | 管理员 |
| /api/users/<int:user_id>/password | PUT | 重置用户密码 | 管理员 |
| /api/users/<int:user_id>/status | PUT | 禁用/启用用户 | 管理员 |
| /api/users/<int:user_id> | DELETE | 删除用户 | 管理员 |
| /api/users/change-password | PUT | 修改当前用户密码 | 登录用户 |

### 3.2 文件上传API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /api/upload | POST | 处理文件上传 | 登录用户 |
| /uploads/<filename> | GET | 提供上传文件访问 | 无 |

### 3.3 艺人管理API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /api/artists | GET | 获取所有艺人列表 | 登录用户 |
| /api/artists/<int:artist_id> | GET | 获取单个艺人详情 | 登录用户 |
| /api/artists | POST | 创建新艺人 | 登录用户 |
| /api/artists/<int:artist_id> | PUT | 更新艺人信息 | 登录用户 |
| /api/artists/<int:artist_id> | DELETE | 删除艺人 | 登录用户 |
| /api/artists/<int:artist_id>/logs | GET | 获取艺人操作日志 | 登录用户 |
| /api/artists/<int:artist_id>/follow-ups | GET | 获取艺人跟进记录 | 登录用户 |
| /api/artists/<int:artist_id>/follow-ups | POST | 添加艺人跟进记录 | 登录用户 |
| /api/follow-ups/<int:id> | DELETE | 删除跟进记录 | 登录用户 |
| /api/follow-ups/<int:id> | PUT | 更新跟进记录 | 登录用户 |
| /api/artists/template | GET | 下载艺人信息模板 | 登录用户 |
| /api/artists/bulk | POST | 批量上传艺人信息 | 登录用户 |

### 3.4 项目管理API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /api/projects | GET | 获取所有项目列表 | 登录用户 |
| /api/projects/<int:project_id> | GET | 获取单个项目详情 | 登录用户 |
| /api/projects | POST | 创建新项目 | 登录用户 |
| /api/projects/<int:project_id> | PUT | 更新项目信息 | 登录用户 |
| /api/projects/<int:project_id> | DELETE | 删除项目 | 登录用户 |

### 3.5 活动管理API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /api/activities | GET | 获取所有活动列表 | 登录用户 |
| /api/activities/<int:activity_id> | GET | 获取单个活动详情 | 登录用户 |
| /api/activities | POST | 创建新活动 | 登录用户 |
| /api/activities/<int:activity_id> | PUT | 更新活动信息 | 登录用户 |
| /api/activities/<int:activity_id> | DELETE | 删除活动 | 登录用户 |

### 3.6 关联管理API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /api/artist-projects | POST | 添加艺人与项目的关联 | 登录用户 |
| /api/artist-projects/<int:id> | DELETE | 删除艺人与项目的关联 | 登录用户 |
| /api/artist-activities | POST | 添加艺人与活动的关联 | 登录用户 |
| /api/artist-activities/<int:id> | PUT | 更新艺人与活动的关联信息 | 登录用户 |
| /api/artist-activities/<int:id> | DELETE | 删除艺人与活动的关联 | 登录用户 |

### 3.7 备份API
| 接口路径 | 方法 | 描述 | 权限要求 |
|----------|------|------|----------|
| /api/backups/<filename> | GET | 提供备份文件下载 | 登录用户 |

## 4. 数据库接口

### 4.1 数据库表结构

#### 4.1.1 艺人表（artists）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 艺人ID |
| name | VARCHAR(100) | NOT NULL | 艺名 |
| real_name | VARCHAR(100) | | 真名 |
| douyin_account | VARCHAR(100) | | 抖音号 |
| vocal_skill | VARCHAR(20) | | 唱功 |
| live_effect_level | VARCHAR(20) | | 直播效果等级 |
| total_revenue | DECIMAL(15,2) | | 总流水(元)上月 |
| current_status | VARCHAR(50) | | 当前状态 |
| singer_attachment | VARCHAR(500) | | 歌手信息附件路径 |
| address | VARCHAR(200) | | 住址 |
| household_address | VARCHAR(200) | | 户籍地 |
| willing_offline | ENUM('是', '否') | | 是否愿意线下 |
| exposure_parts | VARCHAR(500) | | 可露出部分 |
| contract_type | VARCHAR(50) | | 签约类型 |
| remarks | TEXT | | 备注信息 |
| join_date | DATE | | 入会时间 |
| height | DECIMAL(10,2) | | 身高(cm) |
| weight | DECIMAL(10,2) | | 体重(kg) |
| birth_date | DATE | | 生日 |
| relationship_status | VARCHAR(50) | | 感情情况 |
| personality | VARCHAR(200) | | 性格 |
| mbti | VARCHAR(4) | | MBTI |
| occupation | VARCHAR(100) | | 职业 |
| skills | VARCHAR(500) | | 技能 |
| fan_name | VARCHAR(100) | | 粉丝名 |
| music_style | VARCHAR(100) | | 曲风 |
| expectation | TEXT | | 期望 |
| bond | VARCHAR(500) | | 羁绊 |
| ethnicity | VARCHAR(50) | | 民族 |
| art_major | VARCHAR(100) | | 艺术专业 |
| gender | VARCHAR(10) | | 性别 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.2 项目表（projects）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 项目ID |
| title | VARCHAR(200) | NOT NULL | 项目标题 |
| type | ENUM('电影', '电视剧', '音乐专辑', '综艺', '舞台剧', '其他') | | 项目类型 |
| release_date | DATE | | 发布日期 |
| description | TEXT | | 项目描述 |
| director | VARCHAR(100) | | 导演 |
| project_leader | VARCHAR(100) | | 项目负责人 |
| project_attachment | VARCHAR(500) | | 项目附件路径 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.3 艺人项目关联表（artist_projects）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 关联ID |
| artist_id | INT | NOT NULL, FOREIGN KEY | 艺人ID |
| project_id | INT | NOT NULL, FOREIGN KEY | 项目ID |
| role | VARCHAR(100) | | 角色名称 |
| role_type | ENUM('主演', '配角', '导演', '制作人', '歌手', '主持人', '其他') | | 角色类型 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| UNIQUE KEY | (artist_id, project_id, role) | | 唯一约束 |

#### 4.1.4 活动表（activities）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 活动ID |
| title | VARCHAR(200) | NOT NULL | 活动标题 |
| type | VARCHAR(50) | | 活动类型 |
| activity_date | DATE | | 活动日期 |
| location | VARCHAR(200) | | 活动地点 |
| description | TEXT | | 活动描述 |
| organizer | VARCHAR(100) | | 主办方 |
| activity_leader | VARCHAR(100) | | 活动负责人 |
| activity_attachment | VARCHAR(500) | | 活动附件路径 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.5 艺人活动关联表（artist_activities）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 关联ID |
| artist_id | INT | NOT NULL, FOREIGN KEY | 艺人ID |
| activity_id | INT | NOT NULL, FOREIGN KEY | 活动ID |
| role | VARCHAR(100) | | 参与角色 |
| performance_notes | TEXT | | 表现备注 |
| schedule_progress | VARCHAR(100) | | 行程进度 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| UNIQUE KEY | (artist_id, activity_id) | | 唯一约束 |

#### 4.1.6 操作日志表（operation_logs）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 日志ID |
| operation_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 操作时间 |
| operator | VARCHAR(50) | NOT NULL | 操作人 |
| operation_type | ENUM('新增', '修改', '删除') | NOT NULL | 操作类型 |
| artist_id | INT | FOREIGN KEY | 艺人ID |
| artist_name | VARCHAR(100) | | 艺人姓名 |
| operation_content | TEXT | | 操作内容 |

#### 4.1.7 用户表（users）
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| password | VARCHAR(255) | NOT NULL | 密码（加密存储） |
| nickname | VARCHAR(50) | NOT NULL | 昵称 |
| is_admin | BOOLEAN | DEFAULT FALSE | 是否为管理员 |
| disabled | BOOLEAN | DEFAULT FALSE | 是否禁用 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.2 数据库索引
| 表名 | 索引字段 | 类型 | 用途 |
|------|----------|------|------|
| artists | name | INDEX | 加速艺人名称查询 |
| artists | douyin_account | INDEX | 加速抖音号查询 |
| artists | contract_type | INDEX | 加速签约类型查询 |
| artists | current_status | INDEX | 加速状态查询 |
| projects | title | INDEX | 加速项目标题查询 |
| projects | type | INDEX | 加速项目类型查询 |
| artist_projects | project_id | INDEX | 加速项目关联查询 |
| activities | title | INDEX | 加速活动标题查询 |
| activities | activity_date | INDEX | 加速活动日期查询 |
| artist_activities | activity_id | INDEX | 加速活动关联查询 |
| artist_activities | artist_id | INDEX | 加速艺人活动查询 |
| operation_logs | operation_time | INDEX | 加速日志时间查询 |
| operation_logs | artist_id | INDEX | 加速艺人日志查询 |
| operation_logs | operator | INDEX | 加速操作人日志查询 |

### 4.3 数据库关系
```
artists 1:n artist_projects n:1 projects
artists 1:n artist_activities n:1 activities
artists 1:n operation_logs
users 1:n operation_logs
```

## 5. 部署与配置

### 5.1 数据库初始化
```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE artist_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 创建用户并授权
mysql -u root -p -e "CREATE USER 'artist_user'@'localhost' IDENTIFIED BY 'password';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON artist_system.* TO 'artist_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"

# 导入数据库结构
mysql -u artist_user -p artist_system < /root/artist-system/schema.sql
```

### 5.2 初始化管理员账号
```bash
cd /root/artist-system/backend
python init_admin.py
```

### 5.3 启动Flask应用
```bash
# 开发环境启动
cd /root/artist-system/backend
python -m flask run --host=0.0.0.0 --port=15500

# 生产环境建议使用Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:15500 app:app
```

### 5.4 配置自动备份
1. **挂载SMB共享**：
   ```bash
   mkdir -p /root/artist-system/备份
   mount.cifs -o username=<username>,password=<password>,vers=3.0,uid=0,gid=0,dir_mode=0755,file_mode=0644 "//10.0.0.2/justin/艺人管理系统备份" /root/artist-system/备份
   ```

2. **设置自动备份任务**：
   ```bash
   # 添加到crontab
   crontab -e
   # 添加以下行，每12小时执行一次备份
   0 */12 * * * /root/artist-system/auto_backup.sh
   ```

## 6. 系统功能

### 6.1 艺人管理
- 新增、修改、删除艺人信息
- 批量导入艺人信息
- 查看艺人详情和关联项目/活动
- 记录艺人跟进情况

### 6.2 项目管理
- 新增、修改、删除项目
- 为项目添加艺人
- 查看项目详情和参与艺人

### 6.3 活动管理
- 新增、修改、删除活动
- 为活动添加艺人
- 查看活动详情和参与艺人
- 记录艺人行程进度

### 6.4 用户管理
- 新增、修改、删除用户
- 设置管理员权限
- 禁用/启用用户
- 重置用户密码

### 6.5 搜索功能
- 支持艺人、项目、活动的搜索

### 6.6 备份功能
- 自动备份数据库和项目文件
- 保留最近5个备份文件
- 备份到远程SMB共享

## 7. 安全配置

### 7.1 密码安全
- 使用bcrypt加密存储用户密码
- 定期更换数据库密码
- 避免使用弱密码

### 7.2 权限控制
- 基于角色的访问控制
- 管理员和普通用户权限分离
- 敏感操作需要管理员权限

### 7.3 数据安全
- 定期备份数据库和文件
- 使用HTTPS协议（生产环境）
- 限制数据库访问IP

### 7.4 日志管理
- 记录系统操作日志
- 记录数据库错误日志
- 定期清理日志文件

## 8. 维护与故障排除

### 8.1 常见问题
1. **数据库连接失败**：
   - 检查数据库服务是否运行
   - 检查数据库连接参数
   - 检查防火墙设置

2. **备份失败**：
   - 检查SMB挂载是否正常
   - 检查备份脚本权限
   - 查看backup.log日志

3. **API请求失败**：
   - 检查Flask应用是否运行
   - 检查请求参数格式
   - 查看db_error.log日志

### 8.2 维护计划
1. **每日维护**：
   - 检查系统运行状态
   - 查看日志文件
   - 确认备份成功

2. **每周维护**：
   - 清理临时文件
   - 更新系统和依赖
   - 测试备份恢复

3. **每月维护**：
   - 数据库优化
   - 性能监控和调优
   - 安全审计

## 9. 更新日志

### 9.1 版本 0.1.1
- 新增自动备份功能
- 优化数据库结构
- 修复前端页面链接问题
- 添加项目负责人和活动负责人字段
- 实现艺人与项目、活动的双向关联

### 9.2 版本 0.1.0
- 初始版本发布
- 实现艺人、项目、活动的基本CRUD功能
- 实现用户登录和权限管理
- 实现文件上传功能

## 10. 联系方式

如有问题或建议，请联系系统管理员。

---

**文档生成日期**：2025-12-30
**文档版本**：1.0.0
