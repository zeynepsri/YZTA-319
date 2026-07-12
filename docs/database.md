# Veritabanı Dokümantasyonu

## Genel Bakış
PostgreSQL (Supabase) üzerinde çalışan veritabanı.
Tüm tablolarda RLS (Row Level Security) aktiftir.

---

## Tablolar

### categories
Harcama kategorilerini tutar. TÜİK kategori kodlarıyla eşleştirilir.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | SERIAL | Primary key |
| name | TEXT | Kategori adı (Gıda, Temizlik...) |
| tuik_code | TEXT | TÜİK resmi kategori kodu |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### stores
Market zincirlerini tutar.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | SERIAL | Primary key |
| name | TEXT | Market adı (Migros, BİM...) |
| chain | TEXT | Zincir adı |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### products
Normalize edilmiş ürün listesi.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | SERIAL | Primary key |
| name | TEXT | Normalize ürün adı |
| category_id | INT | Bağlı kategori (FK) |
| barcode | TEXT | Barkod numarası |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### users
Uygulama kullanıcıları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| email | TEXT | Kullanıcı e-postası |
| full_name | TEXT | Ad soyad |
| monthly_budget | DECIMAL | Aylık bütçe hedefi |
| savings_goal | DECIMAL | Tasarruf hedefi |
| created_at | TIMESTAMP | Oluşturulma tarihi |
| updated_at | TIMESTAMP | Güncellenme tarihi |

---

### receipts
Kullanıcının yüklediği fişler.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | SERIAL | Primary key |
| user_id | UUID | Bağlı kullanıcı (FK) |
| store_id | INT | Bağlı market (FK) |
| image_url | TEXT | Fiş görseli linki |
| raw_ocr_text | TEXT | OCR ham metin çıktısı |
| total_amount | DECIMAL | Fiş toplam tutarı |
| receipt_date | DATE | Alışveriş tarihi |
| ocr_confidence | DECIMAL | OCR doğruluk skoru (0-1) |
| status | TEXT | pending / processed / failed |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### receipt_items
Fişteki her bir ürün kalemi.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | SERIAL | Primary key |
| receipt_id | INT | Bağlı fiş (FK) |
| product_id | INT | Bağlı ürün (FK) |
| category_id | INT | Bağlı kategori (FK) |
| raw_name | TEXT | Fişte yazan ham isim |
| normalized_name | TEXT | AI normalize ettiği isim |
| price | DECIMAL | Ürün fiyatı |
| quantity | DECIMAL | Miktar |
| unit | TEXT | Birim (adet, kg, lt) |
| confidence | DECIMAL | AI doğruluk skoru (0-1) |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### official_inflation
TÜİK resmi enflasyon verileri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | SERIAL | Primary key |
| month | DATE | Ay (2026-07-01) |
| category_id | INT | Bağlı kategori (FK) |
| rate | DECIMAL | Enflasyon oranı (%) |
| source | TEXT | Kaynak (TUIK) |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### price_history
Ürünlerin zaman içindeki fiyat geçmişi. receipt_items'tan türetilir.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGSERIAL | Primary key |
| product_id | BIGINT | Bağlı ürün (FK) |
| store_id | BIGINT | Bağlı market (FK) |
| price | DECIMAL | Kayıtlı fiyat |
| recorded_date | DATE | Fiyatın kayıt tarihi |
| source_receipt_item_id | BIGINT | Kaynak fiş kalemi (FK) |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### monthly_inflation
Kullanıcı bazlı aylık kişisel enflasyon hesaplaması ve TÜİK karşılaştırması.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGSERIAL | Primary key |
| user_id | UUID | Bağlı kullanıcı (FK) |
| year_month | DATE | Hesaplama ayı (ayın ilk günü) |
| personal_inflation_rate | DECIMAL | Kullanıcının kişisel enflasyon oranı (%) |
| basket_total_current | DECIMAL | Bu ayki sepet toplamı |
| basket_total_previous | DECIMAL | Önceki ayki sepet toplamı |
| category_breakdown | JSONB | Kategori bazlı detaylı kırılım |
| official_inflation_rate | DECIMAL | O aya ait TÜİK oranı (referans kopya) |
| created_at | TIMESTAMP | Oluşturulma tarihi |

**Not:** `user_id + year_month` kombinasyonu unique'tir, kullanıcı başına ayda bir kayıt olur.

---

### user_goals
Kullanıcının bütçe/tasarruf hedefleri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGSERIAL | Primary key |
| user_id | UUID | Bağlı kullanıcı (FK) |
| category_id | INT | Bağlı kategori (FK, NULL ise genel hedef) |
| target_amount | DECIMAL | Hedef tutar |
| period_start | DATE | Hedef dönem başlangıcı |
| period_end | DATE | Hedef dönem bitişi |
| status | VARCHAR | active / completed / failed |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

### ai_conversations
AI agent (Receipt, Inflation, Memory) konuşma logları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGSERIAL | Primary key |
| user_id | UUID | Bağlı kullanıcı (FK) |
| session_id | UUID | Konuşma oturumu kimliği |
| agent_type | VARCHAR | receipt / inflation / memory |
| role | VARCHAR | user / assistant / system |
| message | TEXT | Mesaj içeriği |
| metadata | JSONB | Token sayısı, model adı, function call bilgisi vb. |
| created_at | TIMESTAMP | Oluşturulma tarihi |

---

## İlişkiler
- Bir kullanıcının birden fazla fişi olabilir
- Bir fişin birden fazla ürün kalemi olabilir
- Her ürün kalemi bir kategoriye bağlıdır
- TÜİK verileri kategorilerle eşleştirilir
- Bir kullanıcının birden fazla hedefi (user_goals) olabilir
- Bir kullanıcının birden fazla AI konuşma oturumu (ai_conversations) olabilir
- price_history, receipt_items'tan türetilen fiyat geçmişini tutar
- monthly_inflation, kullanıcı bazlı enflasyonu official_inflation ile karşılaştırır

## Sprint Planı
- Sprint 1: Temel tablolar ✅
- Sprint 2: PriceHistory, MonthlyInflation, UserGoals, AIConversations ✅
- Sprint 3: pgvector, UserMemory, ShoppingPatterns
