CREATE DATABASE IF NOT EXISTS `warehouse_management`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `warehouse_management`;

DROP TABLE IF EXISTS `gate_records`;
DROP TABLE IF EXISTS `inventory_operations`;
DROP TABLE IF EXISTS `products`;

CREATE TABLE `products` (
  `tag_id` varchar(64) NOT NULL,
  `product_name` varchar(120) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `status_code` int NOT NULL DEFAULT 0,
  `last_action` varchar(64) NOT NULL DEFAULT 'created',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`tag_id`),
  KEY `idx_products_status_code` (`status_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `inventory_operations` (
  `operation_id` int NOT NULL AUTO_INCREMENT,
  `tag_id` varchar(64) NOT NULL,
  `action` varchar(20) NOT NULL,
  `operator` varchar(80) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`operation_id`),
  KEY `idx_inventory_operations_tag_id` (`tag_id`),
  CONSTRAINT `fk_inventory_operations_product`
    FOREIGN KEY (`tag_id`) REFERENCES `products` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `gate_records` (
  `gate_record_id` int NOT NULL AUTO_INCREMENT,
  `tag_id` varchar(64) NOT NULL,
  `gate_id` varchar(40) NOT NULL,
  `result` varchar(20) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`gate_record_id`),
  KEY `idx_gate_records_tag_id` (`tag_id`),
  CONSTRAINT `fk_gate_records_product`
    FOREIGN KEY (`tag_id`) REFERENCES `products` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `products` (`tag_id`, `product_name`, `price`, `status_code`, `last_action`)
VALUES
  ('TAG-1001', '無線條碼掃描器', 3490.00, 0, 'seed_stock_in'),
  ('TAG-1002', '倉儲貨架模組', 12800.00, 1, 'seed_stock_out'),
  ('TAG-1003', '藍牙標籤讀取器', 2590.00, 2, 'seed_unauthorized_exit');

INSERT INTO `inventory_operations` (`tag_id`, `action`, `operator`, `timestamp`)
VALUES
  ('TAG-1001', 'stock_in', 'Admin', NOW()),
  ('TAG-1002', 'stock_out', 'Cashier-A', NOW());

INSERT INTO `gate_records` (`tag_id`, `gate_id`, `result`, `timestamp`)
VALUES
  ('TAG-1002', 'Gate-A', 'authorized', NOW()),
  ('TAG-1003', 'Gate-B', 'unauthorized', NOW());
