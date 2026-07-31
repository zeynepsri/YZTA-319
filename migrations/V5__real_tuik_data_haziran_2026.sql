-- V5__real_tuik_data_haziran_2026.sql
-- Sprint 1/2: Gerçek TÜİK enflasyon verisi (Haziran 2026)
-- Açıklama: V2'deki test amaçlı sahte official_inflation verisinin yerine
--           TÜİK'ten çekilen GERÇEK yıllık enflasyon oranları yazılır.
-- Kaynak: TÜİK, Tüketici Fiyat Endeksi, Haziran 2026
--         "Ana harcama gruplarına göre ağırlıklar, TÜFE ve değişim oranları"
-- Oranlar: bir önceki yılın aynı ayına göre (yıllık) değişim (%)
--
-- ÖNEMLİ: category_id 1-7 = projenin kendi kategorileri (TÜİK'in 13 grubu değil).
-- Eşleştirme TASLAK. Aşağıdaki iki nokta ekiple netleştirilmeli:
--   * İçecek (4): TÜİK içeceği gıdayla aynı grupta veriyor, o yüzden Gıda ile aynı oran kullanıldı.
--   * Bebek (7): TÜİK'te ayrı grup yok; şimdilik "Kişisel bakım" grubuna bağlandı.

INSERT INTO official_inflation (month, category_id, rate, source) VALUES
    ('2026-06-01', 1, 35.450, 'TUIK'),  -- Gıda  <- TÜİK: Gıda ve alkolsüz içecekler
    ('2026-06-01', 2, 22.320, 'TUIK'),  -- Temizlik  <- TÜİK: Mobilya, mefruşat ve evde kullanılan ekipmanlar ile rutin ev bakım ve onarımı
    ('2026-06-01', 3, 22.710, 'TUIK'),  -- Kozmetik  <- TÜİK: Kişisel bakım, sosyal koruma ve çeşitli mal ve hizmetler
    ('2026-06-01', 4, 35.450, 'TUIK'),  -- İçecek  <- TÜİK: Gıda ve alkolsüz içecekler
    ('2026-06-01', 5, 33.620, 'TUIK'),  -- Sağlık  <- TÜİK: Sağlık
    ('2026-06-01', 6, 45.140, 'TUIK'),  -- Ev  <- TÜİK: Konut, su, elektrik, gaz ve diğer yakıtlar
    ('2026-06-01', 7, 22.710, 'TUIK')   -- Bebek  <- TÜİK: Kişisel bakım, sosyal koruma ve çeşitli mal ve hizmetler
ON CONFLICT (month, category_id) DO UPDATE
    SET rate = EXCLUDED.rate,
        source = EXCLUDED.source;
