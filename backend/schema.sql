-- 艺人信息系统数据库初始化脚本

-- 创建艺人表
CREATE TABLE IF NOT EXISTS artists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '艺名',
    real_name VARCHAR(100) COMMENT '真名',
    douyin_account VARCHAR(100) COMMENT '抖音号',
    vocal_skill VARCHAR(20) COMMENT '唱功',
    live_effect_level VARCHAR(20) COMMENT '直播效果等级',
    total_revenue DECIMAL(15,2) COMMENT '总流水(元)上月',
    current_status VARCHAR(50) COMMENT '当前状态',
    singer_attachment VARCHAR(500) COMMENT '歌手信息附件路径',
    address VARCHAR(200) COMMENT '住址',
    household_address VARCHAR(200) COMMENT '户籍地',
    willing_offline ENUM('是', '否') COMMENT '是否愿意线下',
    exposure_parts VARCHAR(500) COMMENT '可露出部分',
    contract_type VARCHAR(50) COMMENT '签约类型',
    remarks TEXT COMMENT '备注信息',
    join_date DATE COMMENT '入会时间',
    height DECIMAL(10,2) COMMENT '身高(cm)',
    weight DECIMAL(10,2) COMMENT '体重(kg)',
    birth_date DATE COMMENT '生日',
    relationship_status VARCHAR(50) COMMENT '感情情况',
    personality VARCHAR(200) COMMENT '性格',
    mbti VARCHAR(4) COMMENT 'MBTI',
    occupation VARCHAR(100) COMMENT '职业',
    skills VARCHAR(500) COMMENT '技能',
    fan_name VARCHAR(100) COMMENT '粉丝名',
    music_style VARCHAR(100) COMMENT '曲风',
    expectation TEXT COMMENT '期望',
    bond VARCHAR(500) COMMENT '羁绊',
    ethnicity VARCHAR(50) COMMENT '民族',
    art_major VARCHAR(100) COMMENT '艺术专业',
    gender VARCHAR(10) COMMENT '性别',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_douyin (douyin_account),
    INDEX idx_contract (contract_type),
    INDEX idx_status (current_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='艺人信息表';

-- 创建项目表
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '项目标题',
    type ENUM('电影', '电视剧', '音乐专辑', '综艺', '舞台剧', '其他') COMMENT '项目类型',
    release_date DATE COMMENT '发布日期',
    description TEXT COMMENT '项目描述',
    director VARCHAR(100) COMMENT '导演',
    project_leader VARCHAR(100) COMMENT '项目负责人',
    project_attachment VARCHAR(500) COMMENT '项目附件路径',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目信息表';

-- 创建艺人项目关联表
CREATE TABLE IF NOT EXISTS artist_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artist_id INT NOT NULL,
    project_id INT NOT NULL,
    role VARCHAR(100) COMMENT '角色名称',
    role_type ENUM('主演', '配角', '导演', '制作人', '歌手', '主持人', '其他') COMMENT '角色类型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY uk_artist_project (artist_id, project_id, role),
    INDEX idx_project_id (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='艺人项目关联表';

-- 创建活动表
CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '活动标题',
    type VARCHAR(50) COMMENT '活动类型',
    activity_date DATE COMMENT '活动日期',
    location VARCHAR(200) COMMENT '活动地点',
    description TEXT COMMENT '活动描述',
    organizer VARCHAR(100) COMMENT '主办方',
    activity_leader VARCHAR(100) COMMENT '活动负责人',
    activity_attachment VARCHAR(500) COMMENT '活动附件路径',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_date (activity_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动信息表';

-- 创建艺人活动关联表（支持多选活动，且可关联其他艺人）
CREATE TABLE IF NOT EXISTS artist_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artist_id INT NOT NULL,
    activity_id INT NOT NULL,
    role VARCHAR(100) COMMENT '参与角色',
    performance_notes TEXT COMMENT '表现备注',
    schedule_progress VARCHAR(100) COMMENT '行程进度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    UNIQUE KEY uk_artist_activity (artist_id, activity_id),
    INDEX idx_activity_id (activity_id),
    INDEX idx_artist_id (artist_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='艺人活动关联表';

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    operator VARCHAR(50) NOT NULL COMMENT '操作人',
    operation_type ENUM('新增', '修改', '删除') NOT NULL COMMENT '操作类型',
    artist_id INT COMMENT '艺人ID',
    artist_name VARCHAR(100) COMMENT '艺人姓名',
    operation_content TEXT COMMENT '操作内容',
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    INDEX idx_operation_time (operation_time),
    INDEX idx_artist_id (artist_id),
    INDEX idx_operator (operator)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 创建艺人跟进记录表
CREATE TABLE IF NOT EXISTS artist_follow_ups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artist_id INT NOT NULL COMMENT '艺人ID',
    content TEXT NOT NULL COMMENT '跟进内容',
    operator VARCHAR(50) NOT NULL COMMENT '操作人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    INDEX idx_artist_id (artist_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='艺人跟进记录表';

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    nickname VARCHAR(50) NOT NULL COMMENT '昵称',
    is_admin BOOLEAN DEFAULT FALSE COMMENT '是否为管理员',
    disabled BOOLEAN DEFAULT FALSE COMMENT '是否禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 创建工单主表
CREATE TABLE IF NOT EXISTS work_tickets (
    id INT(11) NOT NULL AUTO_INCREMENT,
    ticket_no VARCHAR(20) NOT NULL COMMENT '工单编号: WT202512310001',
    artist_id INT(11) NOT NULL COMMENT '关联艺人',
    title VARCHAR(200) NOT NULL COMMENT '工单标题',
    description TEXT COMMENT '工单描述',
    ticket_type ENUM('沟通', '对接', '投诉', '需求', '问题', '其他') DEFAULT '沟通',
    priority ENUM('低', '中', '高', '紧急') DEFAULT '中',
    status ENUM('待处理', '处理中', '已完成', '已关闭', '已取消') DEFAULT '待处理',
    creator_id INT(11) NOT NULL COMMENT '创建人ID',
    assigned_to VARCHAR(50) DEFAULT NULL COMMENT '指派人',
    due_date DATETIME DEFAULT NULL COMMENT '截止日期',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    attachment_path VARCHAR(500) DEFAULT NULL COMMENT '附件路径',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_ticket_no (ticket_no),
    KEY idx_artist_id (artist_id),
    KEY idx_status (status),
    KEY idx_priority (priority),
    KEY idx_type (ticket_type),
    KEY idx_assigned_to (assigned_to),
    KEY idx_created_at (created_at),
    CONSTRAINT fk_ticket_artist FOREIGN KEY (artist_id) REFERENCES artists (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单主表';

-- 创建工单评论表
CREATE TABLE IF NOT EXISTS ticket_comments (
    id INT(11) NOT NULL AUTO_INCREMENT,
    ticket_id INT(11) NOT NULL COMMENT '工单ID',
    commenter_id INT(11) NOT NULL COMMENT '评论人ID',
    commenter_name VARCHAR(50) NOT NULL COMMENT '评论人姓名',
    content TEXT NOT NULL COMMENT '评论内容',
    attachment_path VARCHAR(500) DEFAULT NULL COMMENT '附件路径',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_ticket_id (ticket_id),
    KEY idx_created_at (created_at),
    CONSTRAINT fk_comment_ticket FOREIGN KEY (ticket_id) REFERENCES work_tickets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单评论表';

-- 创建工单操作日志表
CREATE TABLE IF NOT EXISTS ticket_logs (
    id INT(11) NOT NULL AUTO_INCREMENT,
    ticket_id INT(11) NOT NULL COMMENT '工单ID',
    operator_id INT(11) NOT NULL COMMENT '操作人ID',
    operator_name VARCHAR(50) NOT NULL COMMENT '操作人姓名',
    action VARCHAR(50) NOT NULL COMMENT '操作类型: created/updated/assigned/commented/completed/closed',
    field_changed VARCHAR(50) DEFAULT NULL COMMENT '变更字段',
    old_value VARCHAR(500) DEFAULT NULL COMMENT '旧值',
    new_value VARCHAR(500) DEFAULT NULL COMMENT '新值',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_ticket_id (ticket_id),
    KEY idx_created_at (created_at),
    CONSTRAINT fk_log_ticket FOREIGN KEY (ticket_id) REFERENCES work_tickets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单操作日志表';
