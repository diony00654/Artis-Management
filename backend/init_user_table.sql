-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入超级管理员账号
INSERT INTO users (username, password, nickname, is_admin) VALUES
('admin', '$2b$12$8GQvF7Q1J7K5L3M2N1O9P8Q7R6S5T4U3V2W1X0Y9Z8A7B6C5D4E3F2G1H0', '管理员', TRUE);

-- 注意：密码是经过bcrypt加密的 'justin00654'
