-- MySQL 容器首次启动初始化：A/B/C/D 四区各一个库（utf8mb4 支持中文）
CREATE DATABASE IF NOT EXISTS `tzb_user_chat` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `tzb_student_data` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `tzb_learning_content` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `tzb_ai_integration` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
