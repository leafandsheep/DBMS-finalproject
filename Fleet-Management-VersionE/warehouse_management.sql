SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `warehouse_management`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `warehouse_management`;

DROP TABLE IF EXISTS `gate_logs`;
DROP TABLE IF EXISTS `counter_logs`;
DROP TABLE IF EXISTS `inventory_items`;

CREATE TABLE `inventory_items` (
  `serial_number` varchar(64) NOT NULL,
  `item_name` varchar(120) NOT NULL,
  `color` varchar(60) NOT NULL,
  `status_code` int NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`serial_number`),
  KEY `idx_inventory_items_item_name` (`item_name`),
  KEY `idx_inventory_items_color` (`color`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `counter_logs` (
  `counter_log_id` int NOT NULL AUTO_INCREMENT,
  `serial_number` varchar(64) NOT NULL,
  `previous_status` int NOT NULL,
  `new_status` int NOT NULL,
  `operator` varchar(80) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`counter_log_id`),
  KEY `idx_counter_logs_serial_number` (`serial_number`),
  CONSTRAINT `fk_counter_logs_item`
    FOREIGN KEY (`serial_number`) REFERENCES `inventory_items` (`serial_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `gate_logs` (
  `gate_log_id` int NOT NULL AUTO_INCREMENT,
  `serial_number` varchar(64) NOT NULL,
  `result` varchar(20) NOT NULL,
  `previous_status` int NOT NULL,
  `new_status` int NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `is_unread` tinyint(1) NOT NULL DEFAULT 0,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`gate_log_id`),
  KEY `idx_gate_logs_serial_number` (`serial_number`),
  CONSTRAINT `fk_gate_logs_item`
    FOREIGN KEY (`serial_number`) REFERENCES `inventory_items` (`serial_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `inventory_items`
  (`serial_number`, `item_name`, `color`, `status_code`)
VALUES
  ('SN-000001', '馬克杯', '白色', 0),
  ('SN-000002', '馬克杯', '白色', 1),
  ('SN-000003', '馬克杯', '黑色', 2),
  ('SN-000004', '閱讀燈', '藍色', 0),
  ('SN-000005', '閱讀燈', '藍色', 0);

INSERT INTO `counter_logs`
  (`serial_number`, `previous_status`, `new_status`, `operator`, `note`, `timestamp`)
VALUES
  ('SN-000002', 0, 1, 'Admin', '櫃檯完成正常出貨設定', NOW());

INSERT INTO `gate_logs`
  (`serial_number`, `result`, `previous_status`, `new_status`, `note`, `is_unread`, `timestamp`)
VALUES
  ('SN-000002', 'authorized', 1, 1, '閘門確認商品已正常售出', 0, NOW()),
  ('SN-000003', 'unauthorized', 0, 2, '商品未經櫃檯正常出貨，閘門判定為未授權', 1, NOW());
