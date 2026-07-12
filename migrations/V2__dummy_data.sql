-- Migration V2: Dummy Data
-- Tarih: 2026-07-12
-- Açıklama: Test verileri

-- Kategoriler
INSERT INTO categories (name, tuik_code) VALUES
('Gıda', 'G01'),
('Temizlik', 'T01'),
('Kozmetik', 'K01'),
('İçecek', 'I01'),
('Sağlık', 'S01'),
('Ev', 'E01'),
('Bebek', 'B01');

-- Marketler
INSERT INTO stores (name, chain) VALUES
('Migros', 'Migros'),
('BİM', 'BİM'),
('A101', 'A101'),
('Carrefour', 'Carrefour'),
('Şok', 'Şok');

-- Ürünler
INSERT INTO products (name, category_id) VALUES
('Pınar Süt 1L', 1),
('Omo Toz Deterjan 1kg', 2),
('Dove Şampuan 400ml', 3),
('Coca Cola 1L', 4),
('Parol 500mg', 5),
('Fairy Bulaşık Deterjanı', 2),
('Bebelac Devam Sütü', 7);

-- TÜİK Enflasyon Verileri
INSERT INTO official_inflation (month, category_id, rate, source) VALUES
('2026-05-01', 1, 67.500, 'TUIK'),
('2026-05-01', 2, 58.200, 'TUIK'),
('2026-05-01', 3, 52.100, 'TUIK'),
('2026-05-01', 4, 61.300, 'TUIK'),
('2026-05-01', 5, 48.900, 'TUIK'),
('2026-06-01', 1, 69.200, 'TUIK'),
('2026-06-01', 2, 59.800, 'TUIK'),
('2026-06-01', 3, 53.400, 'TUIK'),
('2026-06-01', 4, 63.100, 'TUIK'),
('2026-06-01', 5, 50.200, 'TUIK');

-- Test Kullanıcıları
INSERT INTO users (email, full_name, monthly_budget, savings_goal) VALUES
('test1@gmail.com', 'Ahmet Yılmaz', 8000.00, 1500.00),
('test2@gmail.com', 'Ayşe Kaya', 12000.00, 2000.00),
('test3@gmail.com', 'Mehmet Demir', 6000.00, 800.00);

-- Fişler
INSERT INTO receipts (user_id, store_id, total_amount, receipt_date, status)
SELECT id, 1, 523.50, '2026-06-15', 'processed'
FROM users WHERE email = 'test1@gmail.com';

INSERT INTO receipts (user_id, store_id, total_amount, receipt_date, status)
SELECT id, 2, 312.75, '2026-06-22', 'processed'
FROM users WHERE email = 'test1@gmail.com';

INSERT INTO receipts (user_id, store_id, total_amount, receipt_date, status)
SELECT id, 3, 189.90, '2026-07-05', 'processed'
FROM users WHERE email = 'test1@gmail.com';

INSERT INTO receipts (user_id, store_id, total_amount, receipt_date, status)
SELECT id, 1, 876.40, '2026-07-10', 'processed'
FROM users WHERE email = 'test2@gmail.com';

-- Fiş Kalemleri
INSERT INTO receipt_items (receipt_id, product_id, category_id, raw_name, normalized_name, price, quantity, unit, confidence)
VALUES
(1, 1, 1, 'PINAR SUT 1LT', 'Pınar Süt 1L', 47.90, 2, 'adet', 0.97),
(1, 2, 2, 'OMO TOZ 1KG', 'Omo Toz Deterjan 1kg', 189.90, 1, 'adet', 0.95),
(1, 4, 4, 'COCA COLA 1L', 'Coca Cola 1L', 49.90, 3, 'adet', 0.98),
(1, 6, 2, 'FAIRY 500ML', 'Fairy Bulaşık Deterjanı', 89.90, 1, 'adet', 0.96),
(2, 1, 1, 'P.SUT', 'Pınar Süt 1L', 52.90, 2, 'adet', 0.91),
(2, 5, 5, 'PAROL 500MG', 'Parol 500mg', 87.50, 1, 'adet', 0.99),
(2, 3, 3, 'DOVE SAMP', 'Dove Şampuan 400ml', 119.45, 1, 'adet', 0.93),
(3, 1, 1, 'PINAR 1LT', 'Pınar Süt 1L', 54.90, 1, 'adet', 0.94),
(3, 4, 4, 'KOLA 1L', 'Coca Cola 1L', 52.90, 2, 'adet', 0.89),
(4, 2, 2, 'OMO 1KG', 'Omo Toz Deterjan 1kg', 199.90, 2, 'adet', 0.96),
(4, 7, 7, 'BEBELAC', 'Bebelac Devam Sütü', 476.60, 1, 'adet', 0.98);
