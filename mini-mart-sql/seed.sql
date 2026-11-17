-- 便利商店商品與庫存分析：教學用模擬資料，基準日 2026-11-18。
-- 共 100 筆：6 分類、4 供應商、18 商品、18 進貨、16 訂單、38 銷售明細。
-- 金額為新臺幣整數；日期以 ISO 8601 文字儲存。庫存不是儲存欄位。
-- 庫存 = opening_stock + 全部進貨數量 - completed 訂單的銷售數量。
PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

CREATE TABLE categories (
  category_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE suppliers (
  supplier_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL
);

CREATE TABLE products (
  product_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category_id INTEGER NOT NULL REFERENCES categories(category_id),
  supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
  unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
  opening_stock INTEGER NOT NULL CHECK (opening_stock >= 0),
  reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0)
);

CREATE TABLE stock_receipts (
  receipt_id INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES products(product_id),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_cost INTEGER NOT NULL CHECK (unit_cost >= 0),
  received_at TEXT NOT NULL
);

CREATE TABLE sales (
  sale_id INTEGER PRIMARY KEY,
  sold_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('completed', 'cancelled'))
);

CREATE TABLE sale_items (
  sale_item_id INTEGER PRIMARY KEY,
  sale_id INTEGER NOT NULL REFERENCES sales(sale_id),
  product_id INTEGER NOT NULL REFERENCES products(product_id),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price INTEGER NOT NULL CHECK (unit_price >= 0)
);

INSERT INTO categories (category_id, name) VALUES
  (1, '飲品'), (2, '鮮食'), (3, '零食'),
  (4, '日用品'), (5, '冷凍食品'), (6, '甜點');

INSERT INTO suppliers (supplier_id, name, phone) VALUES
  (1, '晨光食品', '02-0000-1001'),
  (2, '好食配銷', '02-0000-1002'),
  (3, '安心生活', '02-0000-1003'),
  (4, '新合作供應商', '02-0000-1004');

INSERT INTO products
  (product_id, name, category_id, supplier_id, unit_price, opening_stock, reorder_level)
VALUES
  (1, '原味鮮乳', 1, 1, 35, 12, 8),
  (2, '無糖綠茶', 1, 1, 25, 20, 10),
  (3, '黑咖啡', 1, 1, 45, 8, 6),
  (4, '鮪魚飯糰', 2, 1, 32, 8, 5),
  (5, '雞肉三明治', 2, 1, 49, 6, 4),
  (6, '蔬菜沙拉', 2, 1, 59, 5, 3),
  (7, '海苔洋芋片', 3, 2, 30, 15, 6),
  (8, '巧克力餅乾', 3, 2, 25, 12, 5),
  (9, '堅果隨手包', 3, 2, 39, 10, 5),
  (10, '抽取式面紙', 4, 3, 49, 10, 4),
  (11, '濕紙巾', 4, 3, 29, 8, 3),
  (12, '旅行牙刷組', 4, 3, 59, 4, 2),
  (13, '冷凍水餃', 5, 2, 99, 6, 3),
  (14, '冷凍炒飯', 5, 2, 79, 8, 4),
  (15, '冰淇淋', 5, 2, 45, 10, 5),
  (16, '布丁', 6, 1, 35, 8, 4),
  (17, '乳酪蛋糕', 6, 2, 65, 4, 3),
  (18, '季節限定果凍', 6, 2, 39, 5, 2);

INSERT INTO stock_receipts
  (receipt_id, product_id, quantity, unit_cost, received_at)
VALUES
  (1, 1, 20, 22, '2026-11-10 06:00:00'),
  (2, 1, 10, 23, '2026-11-16 06:00:00'),
  (3, 2, 24, 15, '2026-11-11 06:00:00'),
  (4, 3, 12, 28, '2026-11-12 06:00:00'),
  (5, 4, 12, 19, '2026-11-10 06:00:00'),
  (6, 4, 6, 19, '2026-11-17 06:00:00'),
  (7, 5, 10, 30, '2026-11-13 06:00:00'),
  (8, 7, 18, 18, '2026-11-11 06:00:00'),
  (9, 7, 6, 19, '2026-11-17 06:00:00'),
  (10, 8, 12, 14, '2026-11-12 06:00:00'),
  (11, 9, 10, 24, '2026-11-15 06:00:00'),
  (12, 10, 8, 30, '2026-11-10 06:00:00'),
  (13, 11, 12, 17, '2026-11-12 06:00:00'),
  (14, 13, 6, 65, '2026-11-13 06:00:00'),
  (15, 14, 8, 48, '2026-11-11 06:00:00'),
  (16, 14, 4, 49, '2026-11-17 06:00:00'),
  (17, 16, 10, 20, '2026-11-14 06:00:00'),
  (18, 18, 5, 22, '2026-11-17 06:00:00');

INSERT INTO sales (sale_id, sold_at, status) VALUES
  (1, '2026-11-10 08:30:00', 'completed'),
  (2, '2026-11-10 12:05:00', 'completed'),
  (3, '2026-11-11 09:10:00', 'completed'),
  (4, '2026-11-11 18:20:00', 'cancelled'),
  (5, '2026-11-12 07:50:00', 'completed'),
  (6, '2026-11-12 19:30:00', 'completed'),
  (7, '2026-11-13 12:10:00', 'completed'),
  (8, '2026-11-14 15:40:00', 'completed'),
  (9, '2026-11-14 20:00:00', 'cancelled'),
  (10, '2026-11-15 08:15:00', 'completed'),
  (11, '2026-11-15 17:55:00', 'completed'),
  (12, '2026-11-16 12:35:00', 'completed'),
  (13, '2026-11-16 21:10:00', 'completed'),
  (14, '2026-11-17 08:45:00', 'completed'),
  (15, '2026-11-17 18:05:00', 'completed'),
  (16, '2026-11-18 11:30:00', 'completed');

INSERT INTO sale_items
  (sale_item_id, sale_id, product_id, quantity, unit_price)
VALUES
  (1, 1, 1, 3, 35), (2, 1, 4, 4, 32), (3, 1, 16, 2, 35),
  (4, 2, 5, 3, 49), (5, 2, 2, 4, 25),
  (6, 3, 3, 2, 45), (7, 3, 7, 3, 30), (8, 3, 8, 2, 25),
  (9, 4, 1, 10, 35), (10, 4, 6, 2, 59),
  (11, 5, 4, 8, 32), (12, 5, 1, 5, 35), (13, 5, 10, 2, 49),
  (14, 6, 14, 4, 79), (15, 6, 9, 3, 39),
  (16, 7, 6, 6, 59), (17, 7, 2, 5, 25), (18, 7, 17, 3, 65),
  (19, 8, 15, 5, 45), (20, 8, 16, 6, 35),
  (21, 9, 13, 4, 99), (22, 9, 7, 8, 30),
  (23, 10, 1, 8, 33), (24, 10, 4, 9, 30),
  (25, 11, 7, 10, 30), (26, 11, 8, 7, 25), (27, 11, 11, 4, 29),
  (28, 12, 13, 5, 99), (29, 12, 14, 9, 79),
  (30, 13, 3, 9, 45), (31, 13, 9, 4, 39),
  (32, 14, 5, 10, 49), (33, 14, 2, 12, 25), (34, 14, 10, 5, 49),
  (35, 15, 1, 10, 35), (36, 15, 16, 9, 35),
  (37, 16, 15, 3, 45), (38, 16, 11, 5, 29);

COMMIT;
