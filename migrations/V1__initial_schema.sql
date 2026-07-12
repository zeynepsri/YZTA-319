-- Migration V1: Initial Schema
-- Tarih: 2026-07-12
-- Açıklama: Temel tabloların oluşturulması

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- CATEGORIES
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    tuik_code TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- STORES
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    chain TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- PRODUCTS
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INT REFERENCES categories(id),
    barcode TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- USERS
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    monthly_budget DECIMAL(10,2),
    savings_goal DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RECEIPTS
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    store_id INT REFERENCES stores(id),
    image_url TEXT,
    raw_ocr_text TEXT,
    total_amount DECIMAL(10,2),
    receipt_date DATE,
    ocr_confidence DECIMAL(4,3),
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- RECEIPT ITEMS
CREATE TABLE receipt_items (
    id SERIAL PRIMARY KEY,
    receipt_id INT REFERENCES receipts(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    category_id INT REFERENCES categories(id),
    raw_name TEXT,
    normalized_name TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity DECIMAL(6,2) DEFAULT 1,
    unit TEXT,
    confidence DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT NOW()
);

-- OFFICIAL INFLATION
CREATE TABLE official_inflation (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL,
    category_id INT REFERENCES categories(id),
    rate DECIMAL(6,3) NOT NULL,
    source TEXT DEFAULT 'TUIK',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(month, category_id)
);

-- INDEXLER
CREATE INDEX idx_receipts_user_id ON receipts(user_id);
CREATE INDEX idx_receipts_date ON receipts(receipt_date);
CREATE INDEX idx_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE INDEX idx_receipt_items_category ON receipt_items(category_id);
CREATE INDEX idx_official_inflation_month ON official_inflation(month);
