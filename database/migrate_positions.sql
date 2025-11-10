-- 数据库迁移脚本：添加 target_positions 列
USE smart_interview;

-- 检查并添加列
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smart_interview'
    AND TABLE_NAME = 'users'
    AND COLUMN_NAME = 'target_positions'
);

SET @old_column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smart_interview'
    AND TABLE_NAME = 'users'
    AND COLUMN_NAME = 'target_position'
);

-- 如果新列不存在，添加它
SET @sql = IF(@column_exists = 0,
    IF(@old_column_exists = 1,
        -- 如果旧列存在，在新列后添加
        'ALTER TABLE users ADD COLUMN target_positions JSON NULL COMMENT ''目标岗位列表(JSON数组)'' AFTER target_position',
        -- 如果旧列不存在，在 password_hash 后添加
        'ALTER TABLE users ADD COLUMN target_positions JSON NULL COMMENT ''目标岗位列表(JSON数组)'' AFTER password_hash'
    ),
    'SELECT ''Column target_positions already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 如果旧列存在，迁移数据
SET @migrate_sql = IF(@old_column_exists = 1 AND @column_exists = 0,
    'UPDATE users SET target_positions = CASE WHEN target_position IS NOT NULL AND target_position != '''' THEN JSON_ARRAY(target_position) ELSE JSON_ARRAY() END WHERE target_positions IS NULL',
    'SELECT ''No migration needed'' AS message'
);

PREPARE migrate_stmt FROM @migrate_sql;
EXECUTE migrate_stmt;
DEALLOCATE PREPARE migrate_stmt;

-- 显示结果
SELECT 'Migration completed' AS status;