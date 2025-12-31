# 艺人信息系统

一个用于管理艺人、项目和活动信息的综合管理系统，支持行程管理、关联查询和数据统计等功能。

## 🌟 功能特性

### 核心功能
- **艺人管理**：添加、编辑、删除艺人详细信息
- **项目管理**：管理艺人参与的项目信息
- **活动管理**：管理艺人参与的活动信息
- **行程管理**：查看艺人行程日历，检测行程冲突
- **关联管理**：管理艺人与项目、活动的关联关系
- **用户管理**：管理系统用户和权限
- **操作日志**：记录所有操作历史
- **批量上传**：支持批量上传艺人信息
- **搜索功能**：支持按多种条件搜索艺人、项目和活动

### 行程管理增强
- 月度行程日历视图
- 行程冲突检测
- 行程数据统计与分析

## 🛠️ 技术栈

- **后端框架**：Flask 3.0.0
- **数据库**：MySQL 8.0 / MariaDB
- **ORM**：MySQL Connector/Python
- **前端**：HTML + JavaScript + CSS
- **认证**：Flask Session + bcrypt
- **部署**：统一管理脚本

## 📁 项目结构

```
artist-system/
├── backend/             # 后端代码
│   ├── app.py           # Flask应用主文件
│   ├── init_admin.py    # 初始化管理员账号
│   ├── init_user_table.sql  # 用户表初始化SQL
│   ├── schema.sql       # 数据库表结构SQL
│   └── uploads/         # 文件上传目录
├── frontend/            # 前端代码
│   ├── static/          # 静态资源
│   └── templates/       # HTML模板文件
├── logs/                # 日志目录
├── requirements.txt     # Python依赖列表
├── manage.sh            # 统一管理脚本
├── LICENSE              # 许可证文件
└── README.md            # 项目说明文档
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MySQL 8.0 / MariaDB
- Linux 系统

### 部署步骤

1. **克隆项目**
   ```bash
   git clone <your-repository-url>
   cd artist-system
   ```

2. **部署应用**
   ```bash
   # 使用统一管理脚本进行部署
   ./manage.sh deploy
   ```

3. **启动服务**
   ```bash
   # 启动应用和数据库
   ./manage.sh start all
   
   # 仅启动应用
   ./manage.sh start
   ```

4. **访问应用**
   - 应用地址：http://your-server-ip:15500
   - 登录账号：admin
   - 登录密码：justin00654

## 📋 管理命令

### 应用管理
```bash
# 启动应用
./manage.sh start

# 停止应用
./manage.sh stop

# 重启应用
./manage.sh restart

# 查看应用状态
./manage.sh status
```

### 数据库管理
```bash
# 启动数据库
./manage.sh db:start

# 停止数据库
./manage.sh db:stop

# 重启数据库
./manage.sh db:restart

# 查看数据库状态
./manage.sh db:status
```

### 全服务管理
```bash
# 启动所有服务（应用+数据库）
./manage.sh start all

# 停止所有服务（应用+数据库）
./manage.sh stop all

# 重启所有服务（应用+数据库）
./manage.sh restart all

# 查看所有服务状态
./manage.sh status all
```

### 开机自启动
```bash
# 配置开机自启动
./manage.sh setup:boot
```

## 🔧 配置说明

### 数据库配置
- 数据库名称：`artist_system`
- 数据库用户：`artist_user`
- 数据库密码：`password`

### 端口配置
- 默认端口：15500
- 可通过环境变量 `DEPLOY_RUN_PORT` 修改

## 📊 数据统计

- 艺人工作量统计
- 项目进度分析
- 活动效果评估
- 行程数据可视化

## 📝 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目！

## 📧 联系方式

如有问题，请联系项目维护者。

## 💖 打赏支持

如果您觉得这个项目对您有所帮助，欢迎通过以下方式打赏支持项目开发：

### 微信支付

![微信支付](https://user-images.githubusercontent.com/xxx/xxx/wechat-pay.png)

### 支付宝

![支付宝](https://user-images.githubusercontent.com/xxx/xxx/alipay.png)

您的支持是我们持续改进和更新的动力！感谢您的理解与支持！

---

**项目开发**: Dog&Clip
**联系方式**: [微信] imdc9475 | [邮箱] justin00654@163.com
**版本**: 0.1.4
**最后更新**: 2026-01-01
