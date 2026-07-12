-- V4__sprint2_dummy_data.sql
-- user_goals için örnek veri

INSERT INTO user_goals (user_id, category_id, target_amount, period_start, period_end, status) VALUES
-- Ahmet Yılmaz (test1) - Gıda kategorisinde aylık bütçe hedefi
('509208d9-2788-45ca-8aac-095349718029', 1, 3000.00, '2026-07-01', '2026-07-31', 'active'),

-- Ayşe Kaya (test2) - Genel tasarruf hedefi (category_id NULL = kategori bağımsız)
('06b875d5-08d2-4044-97a8-622a0e1e08b6', NULL, 5000.00, '2026-07-01', '2026-07-31', 'active'),

-- Mehmet Demir (test3) - Kozmetik kategorisinde harcama sınırı, geçen ay tamamlanmış
('08e1eb70-c8bf-4bb7-9ebe-db39cfb075b4', 3, 500.00, '2026-06-01', '2026-06-30', 'completed'),

-- Ahmet Yılmaz (test1) - İçecek kategorisinde ikinci hedef, aynı kullanıcı birden fazla hedef koyabilir
('509208d9-2788-45ca-8aac-095349718029', 4, 400.00, '2026-07-01', '2026-07-31', 'active');
