-- V3__sprint2_tables.sql
-- Sprint 2: price_history, monthly_inflation, user_goals, ai_conversations tabloları

-- 1. Fiyat geçmişi: receipt_items'tan türeyen zaman serisi verisi
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id),
    store_id BIGINT REFERENCES stores(id),
    price NUMERIC(10,2) NOT NULL,
    recorded_date DATE NOT NULL,
    source_receipt_item_id BIGINT REFERENCES receipt_items(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_price_history_product_date ON price_history(product_id, recorded_date);

-- 2. Aylık kişisel enflasyon: kullanıcı bazlı hesaplama + TÜİK karşılaştırması
CREATE TABLE monthly_inflation (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    year_month DATE NOT NULL,
    personal_inflation_rate NUMERIC(5,2),
    basket_total_current NUMERIC(12,2),
    basket_total_previous NUMERIC(12,2),
    category_breakdown JSONB,
    official_inflation_rate NUMERIC(5,2),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, year_month)
);

-- 3. Kullanıcı hedefleri: bütçe / kategori bazlı hedefler
CREATE TABLE user_goals (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    category_id INT REFERENCES categories(id),
    target_amount NUMERIC(12,2) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. AI agent konuşma logları: Receipt, Inflation, Memory agent'ları tek tabloda
CREATE TABLE ai_conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('receipt', 'inflation', 'memory')),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ai_conversations_session ON ai_conversations(session_id, created_at);
CREATE INDEX idx_ai_conversations_user_agent ON ai_conversations(user_id, agent_type);
