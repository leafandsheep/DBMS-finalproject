SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `warehouse_management`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `warehouse_management`;

DROP TABLE IF EXISTS `search_logs`;
DROP TABLE IF EXISTS `gate_logs`;
DROP TABLE IF EXISTS `counter_logs`;
DROP TABLE IF EXISTS `inventory_items`;
DROP TABLE IF EXISTS `customers`;
DROP TABLE IF EXISTS `employees`;

CREATE TABLE `employees` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customers` (
  `customer_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `preferred_size` varchar(20) NOT NULL,
  `phone` varchar(40) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `inventory_items` (
  `serial_number` varchar(64) NOT NULL,
  `item_name` varchar(120) NOT NULL,
  `color` varchar(60) NOT NULL,
  `size` varchar(20) DEFAULT NULL,
  `status_code` int NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`serial_number`),
  KEY `idx_inventory_items_item_name` (`item_name`),
  KEY `idx_inventory_items_color` (`color`),
  KEY `idx_inventory_items_size` (`size`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `counter_logs` (
  `counter_log_id` int NOT NULL AUTO_INCREMENT,
  `serial_number` varchar(64) NOT NULL,
  `employee_id` int NOT NULL,
  `customer_id` int NOT NULL,
  `previous_status` int NOT NULL,
  `new_status` int NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`counter_log_id`),
  KEY `idx_counter_logs_serial_number` (`serial_number`),
  KEY `idx_counter_logs_employee_id` (`employee_id`),
  KEY `idx_counter_logs_customer_id` (`customer_id`),
  CONSTRAINT `fk_counter_logs_item`
    FOREIGN KEY (`serial_number`) REFERENCES `inventory_items` (`serial_number`),
  CONSTRAINT `fk_counter_logs_employee`
    FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `fk_counter_logs_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`)
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

CREATE TABLE `search_logs` (
  `search_log_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `customer_id` int NOT NULL,
  `queried_size` varchar(20) DEFAULT NULL,
  `queried_item_name` varchar(120) DEFAULT NULL,
  `result_count` int NOT NULL DEFAULT 0,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`search_log_id`),
  KEY `idx_search_logs_employee_id` (`employee_id`),
  KEY `idx_search_logs_customer_id` (`customer_id`),
  CONSTRAINT `fk_search_logs_employee`
    FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `fk_search_logs_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `employees` (`name`) VALUES
  ('小美'),
  ('阿傑'),
  ('老闆');

INSERT INTO `customers` (`name`, `preferred_size`, `phone`) VALUES
  ('阿明', 'M', '0912-345-678'),
  ('小花', 'S', '0922-111-222'),
  ('大雄', 'L', NULL);

INSERT INTO `inventory_items`
  (`serial_number`, `item_name`, `color`, `size`, `status_code`)
VALUES
  ('SN-000001', '馬克杯', '白色', 'M', 0),
  ('SN-000002', '馬克杯', '白色', 'M', 1),
  ('SN-000003', '馬克杯', '黑色', 'L', 2),
  ('SN-000004', '閱讀燈', '藍色', 'M', 0),
  ('SN-000005', '閱讀燈', '藍色', 'L', 0),
  ('SN-000006', '鑰匙圈', '銀色', NULL, 0),
  ('SN-000007', '貼紙', '彩色', NULL, 0);

INSERT INTO `counter_logs`
  (`serial_number`, `employee_id`, `customer_id`, `previous_status`, `new_status`, `note`, `timestamp`)
VALUES
  ('SN-000002', 1, 1, 0, 1, '櫃檯完成正常出貨設定', NOW());

INSERT INTO `gate_logs`
  (`serial_number`, `result`, `previous_status`, `new_status`, `note`, `is_unread`, `timestamp`)
VALUES
  ('SN-000002', 'authorized', 1, 1, '閘門確認商品已正常售出', 0, NOW()),
  ('SN-000003', 'unauthorized', 0, 2, '商品未經櫃檯正常出貨，閘門判定為未授權', 1, NOW());

INSERT INTO `search_logs`
  (`employee_id`, `customer_id`, `queried_size`, `queried_item_name`, `result_count`, `timestamp`)
VALUES
  (1, 1, 'M', NULL, 4, NOW());
