-- 创建数据库
CREATE DATABASE IF NOT EXISTS smart_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_interview;

-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    target_position VARCHAR(100) COMMENT '目标岗位',
    current_level INT DEFAULT 1 COMMENT '当前等级',
    experience_points INT DEFAULT 0 COMMENT '经验值',
    title VARCHAR(50) DEFAULT '新手' COMMENT '头衔',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_email (email),
    INDEX idx_level (current_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 任务表
CREATE TABLE tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID',
    task_type ENUM('custom', 'remedial', 'position_based') NOT NULL COMMENT '任务类型',
    title VARCHAR(200) NOT NULL COMMENT '任务标题',
    description TEXT COMMENT '任务描述',
    position_category VARCHAR(100) COMMENT '岗位类别',
    difficulty_level INT DEFAULT 1 COMMENT '难度等级1-5',
    experience_reward INT DEFAULT 10 COMMENT '经验奖励',
    status ENUM('pending', 'in_progress', 'completed', 'expired') DEFAULT 'pending' COMMENT '状态',
    related_interview_id INT COMMENT '关联面试ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_position (position_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务表';

-- 面试表
CREATE TABLE interviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID',
    interview_type ENUM('task_based', 'stage_based', 'remedial') NOT NULL COMMENT '面试类型',
    related_task_id INT COMMENT '关联任务ID',
    stage_number INT COMMENT '阶段编号',
    questions JSON COMMENT '问题列表',
    answers JSON COMMENT '用户答案',
    ai_feedback JSON COMMENT 'AI反馈',
    scores JSON COMMENT '各项分数',
    weaknesses JSON COMMENT '识别出的弱点',
    total_score DECIMAL(5,2) COMMENT '总分',
    status ENUM('pending', 'completed', 'reviewed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_task (related_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='面试表';

-- 头衔权益表
CREATE TABLE title_benefits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title_name VARCHAR(50) UNIQUE NOT NULL COMMENT '头衔名称',
    min_level INT NOT NULL COMMENT '最低等级',
    max_level INT COMMENT '最高等级',
    benefits JSON NOT NULL COMMENT '权益JSON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (min_level, max_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='头衔权益表';

-- 面试题库表
CREATE TABLE interview_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    position_category VARCHAR(100) NOT NULL COMMENT '岗位类别',
    question_type ENUM('behavioral', 'technical', 'case', 'product') NOT NULL COMMENT '问题类型',
    question TEXT NOT NULL COMMENT '问题内容',
    reference_answer TEXT COMMENT '参考答案',
    difficulty INT DEFAULT 3 COMMENT '难度1-5',
    tags JSON COMMENT '标签',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_position_type (position_category, question_type),
    INDEX idx_difficulty (difficulty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='面试题库表';

-- 知识库表（RAG）
CREATE TABLE knowledge_base (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    category VARCHAR(100) COMMENT '类别',
    position_category VARCHAR(100) COMMENT '岗位类别',
    embedding_vector JSON COMMENT '向量 embedding',
    metadata JSON COMMENT '元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FULLTEXT idx_content (title, content),
    INDEX idx_category (category, position_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

-- 训练数据表（RLHF）
CREATE TABLE training_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    prompt TEXT NOT NULL COMMENT '提示词',
    response TEXT NOT NULL COMMENT '回复',
    reference_response TEXT COMMENT '参考回复',
    preference_score DECIMAL(3,2) COMMENT '偏好分数',
    position_category VARCHAR(100) COMMENT '岗位类别',
    task_type VARCHAR(50) COMMENT '任务类型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (position_category, task_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='训练数据表';

-- 用户任务进度表
CREATE TABLE user_task_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    task_id INT NOT NULL,
    progress_data JSON COMMENT '进度数据',
    current_step INT DEFAULT 0 COMMENT '当前步骤',
    is_completed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_task (user_id, task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户任务进度表';

-- 初始化头衔权益数据
INSERT INTO title_benefits (title_name, min_level, max_level, benefits) VALUES
('新手', 1, 3, '{"unlocked_features": ["basic_interview", "basic_tasks"], "description": "基础功能"}'),
('面试新秀', 1, 3, '{"unlocked_features": ["interview_question_bank", "resume_templates", "basic_interview", "basic_tasks"], "description": "解锁行业通用面试题库和简历模板库"}'),
('面经达人', 4, 6, '{"unlocked_features": ["interview_question_bank", "resume_templates", "ai_interview_review", "word_by_word_optimization", "basic_interview", "basic_tasks"], "description": "获得AI模拟面试逐字稿优化服务"}'),
('面霸', 7, 999, '{"unlocked_features": ["interview_question_bank", "resume_templates", "ai_interview_review", "word_by_word_optimization", "real_company_interviews", "internal_referral", "basic_interview", "basic_tasks"], "description": "解锁企业真实面试真题和内推机会"}');