-- 初始化脚本：仅用于新建的演示数据库。执行时会删除下列同名表及其数据。
-- 表结构对应 backend/app/models 中的模型；已有数据库的增量变更请使用迁移脚本。
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `schedules`;
DROP TABLE IF EXISTS `study_plans`;
DROP TABLE IF EXISTS `kb_documents`;
DROP TABLE IF EXISTS `courses`;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `role` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色：student-学生，admin-管理员',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '手机号',
  `avatar` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '头像',
  `status` int NOT NULL COMMENT '状态：0-禁用，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` (`id`, `username`, `password`, `name`, `role`, `email`, `phone`, `avatar`, `status`, `create_time`, `update_time`) VALUES (1, 'admin', '$2b$12$ypJClLKejFCsyn2eltOco.YAmXory0HFjh7E/oHu9MBzDZZ6wYSSi', '管理员', 'admin', 'admin@system.cn', '13988776699', '/uploads/1790046856623_dc4830aa.jpg', 1, '2026-09-11 15:30:07', '2026-09-22 11:14:34');
INSERT INTO `users` (`id`, `username`, `password`, `name`, `role`, `email`, `phone`, `avatar`, `status`, `create_time`, `update_time`) VALUES (2, 'aaa', '$2a$10$phJ2k4sP5.c7T/LuXwzyTu/AlbbOFXblsAZEW6mIfh3koVxQ3Hhny', '小白', 'student', 'xiaobai@qq.com', '13899776688', '/uploads/1790046891012_452a9884.png', 1, '2026-09-09 16:56:41', '2026-09-22 11:14:52');
INSERT INTO `users` (`id`, `username`, `password`, `name`, `role`, `email`, `phone`, `avatar`, `status`, `create_time`, `update_time`) VALUES (3, 'bbb', '$2a$10$blJ4Qgbaqxm5jmUAWvuiRuKy/FiqbmFv.n1i0noM3pxUZrYhd2HNK', '小黑', 'student', 'xiaohei@163.com', '13799886699', '/uploads/1790046917012_b9ee534a.png', 1, '2026-09-22 11:15:00', '2026-09-22 11:15:30');

CREATE TABLE `courses` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) NOT NULL COMMENT '课程名称',
  `code` varchar(50) NULL DEFAULT NULL COMMENT '课程代码',
  `description` text NULL COMMENT '课程简介',
  `status` int NOT NULL COMMENT '状态：0-停用，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程信息';

CREATE TABLE `schedules` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '学生ID',
  `class_date` date NOT NULL COMMENT '上课日期',
  `period` varchar(50) NOT NULL COMMENT '节次',
  `course_id` int NOT NULL COMMENT '课程ID',
  `location` varchar(100) NULL DEFAULT NULL COMMENT '地点',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_schedules_user_id` (`user_id`),
  KEY `ix_schedules_course_id` (`course_id`),
  CONSTRAINT `fk_schedules_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_schedules_course_id` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课表信息';

CREATE TABLE `study_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `content` text NOT NULL COMMENT '计划内容',
  `turn_id` varchar(32) NULL DEFAULT NULL COMMENT 'MCP对话轮次ID',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_study_plan_user_turn` (`user_id`, `turn_id`),
  CONSTRAINT `fk_study_plans_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习计划';

CREATE TABLE `kb_documents` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `original_name` varchar(255) NOT NULL COMMENT '原始文件名',
  `disk_name` varchar(255) NOT NULL COMMENT '磁盘文件名',
  `rel_path` varchar(512) NOT NULL COMMENT '相对 data/kb 的路径',
  `size` int NOT NULL COMMENT '字节数',
  `ext` varchar(20) NOT NULL COMMENT '扩展名',
  `ingested` tinyint(1) NOT NULL COMMENT '是否已写入共享向量库',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `original_name` (`original_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档';

SET FOREIGN_KEY_CHECKS = 1;
