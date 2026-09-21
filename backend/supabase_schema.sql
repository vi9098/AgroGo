-- ============================================================================
-- AgriGo Supabase PostgreSQL Schema Definition
-- Project Host: db.lebkgjebavldqqflwwox.supabase.co:5432
-- ============================================================================

CREATE TABLE IF NOT EXISTS "admin_users" (
    "id" TEXT PRIMARY KEY,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "role" TEXT DEFAULT 'admin',
    "is_2fa_enabled" BIGINT DEFAULT 0,
    "totp_secret" TEXT,
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "audit_logs" (
    "id" BIGSERIAL PRIMARY KEY,
    "actor_id" TEXT NOT NULL,
    "actor_type" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "resource_type" TEXT NOT NULL,
    "resource_id" TEXT,
    "ip_hash" TEXT,
    "details_json" TEXT,
    "timestamp" TEXT
);

CREATE TABLE IF NOT EXISTS "conversations" (
    "id" TEXT PRIMARY KEY,
    "farmer_id" TEXT NOT NULL,
    "language" TEXT DEFAULT 'hi',
    "updated_at" TEXT,
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "crop_cycles" (
    "id" TEXT PRIMARY KEY,
    "field_id" TEXT,
    "farmer_id" TEXT NOT NULL,
    "crop_name" TEXT NOT NULL,
    "variety" TEXT,
    "sowing_date" TEXT NOT NULL,
    "expected_harvest_date" TEXT,
    "area_acres" DOUBLE PRECISION DEFAULT 1.0,
    "irrigation_method" TEXT DEFAULT 'Drip',
    "soil_type" TEXT DEFAULT 'Sandy Loam',
    "current_stage" TEXT DEFAULT 'Sowing',
    "health_status" TEXT DEFAULT 'Good',
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "crop_production_historical" (
    "id" BIGINT,
    "year" TEXT,
    "state_name" TEXT,
    "state_code" BIGINT,
    "district_name" TEXT,
    "district_code" BIGINT,
    "crop_name" TEXT,
    "crop_code" DOUBLE PRECISION,
    "crop_type" TEXT,
    "season" TEXT,
    "area" DOUBLE PRECISION,
    "area_unit" TEXT,
    "production" DOUBLE PRECISION,
    "production_unit" TEXT,
    "yield" DOUBLE PRECISION,
    "yield_unit" TEXT
);

CREATE TABLE IF NOT EXISTS "crops" (
    "id" TEXT PRIMARY KEY,
    "farm_id" TEXT,
    "farmer_id" TEXT,
    "crop_name" TEXT NOT NULL,
    "variety" TEXT,
    "stage" TEXT DEFAULT 'Flowering',
    "health_status" TEXT DEFAULT 'Good',
    "sowing_date" TEXT,
    "area_acres" DOUBLE PRECISION DEFAULT 1.5,
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "district_crop_benchmarks" (
    "state_name" TEXT,
    "district_name" TEXT,
    "crop_name" TEXT,
    "crop_type" TEXT,
    "season" TEXT,
    "avg_yield" TEXT,
    "max_yield" TEXT,
    "min_yield" TEXT,
    "avg_production" TEXT,
    "avg_area" TEXT,
    "record_count" TEXT
);

CREATE TABLE IF NOT EXISTS "farmer_observations" (
    "id" TEXT PRIMARY KEY,
    "farmer_id" TEXT NOT NULL,
    "crop" TEXT NOT NULL,
    "location" TEXT NOT NULL,
    "problem" TEXT NOT NULL,
    "observed_pest" TEXT,
    "treatment_applied" TEXT,
    "result" TEXT,
    "evidence_type" TEXT DEFAULT 'COMMUNITY_OBSERVATION',
    "validation_status" TEXT DEFAULT 'pending_review',
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "farms" (
    "id" TEXT PRIMARY KEY,
    "farmer_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "total_area_acres" DOUBLE PRECISION DEFAULT 2.5,
    "soil_type" TEXT DEFAULT 'Alluvial Loam',
    "irrigation_type" TEXT DEFAULT 'Drip Irrigation',
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "fields" (
    "id" TEXT PRIMARY KEY,
    "farm_id" TEXT NOT NULL,
    "farmer_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "area_acres" DOUBLE PRECISION DEFAULT 1.0,
    "soil_type" TEXT DEFAULT 'Alluvial Loam',
    "irrigation_source" TEXT DEFAULT 'Tubewell',
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "knowledge_chunks" (
    "id" TEXT PRIMARY KEY,
    "document_id" TEXT,
    "text" TEXT NOT NULL,
    "crop" TEXT NOT NULL,
    "topic" TEXT NOT NULL,
    "region" TEXT DEFAULT 'India',
    "language" TEXT DEFAULT 'en',
    "source" TEXT NOT NULL,
    "source_url" TEXT,
    "license" TEXT,
    "confidence" DOUBLE PRECISION DEFAULT 0.95,
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "knowledge_docs" (
    "id" TEXT PRIMARY KEY,
    "title" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "crop" TEXT,
    "content" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "verified" BIGINT DEFAULT 1,
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "knowledge_sources" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "organization" TEXT NOT NULL,
    "country" TEXT DEFAULT 'India',
    "languages_json" TEXT DEFAULT '["en","hi"]',
    "source_type" TEXT DEFAULT 'government',
    "license_name" TEXT,
    "license_url" TEXT,
    "terms_url" TEXT,
    "allows_automated_collection" BIGINT DEFAULT 0,
    "allows_text_reuse" BIGINT DEFAULT 0,
    "allows_model_training" BIGINT DEFAULT 0,
    "requires_attribution" BIGINT DEFAULT 1,
    "robots_checked" BIGINT DEFAULT 1,
    "verified_at" TEXT,
    "status" TEXT DEFAULT 'Active',
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "live_mandi_prices" (
    "id" TEXT PRIMARY KEY,
    "state" TEXT NOT NULL,
    "district" TEXT NOT NULL,
    "market" TEXT NOT NULL,
    "commodity" TEXT NOT NULL,
    "variety" TEXT,
    "grade" TEXT,
    "arrival_date" TEXT,
    "min_price" DOUBLE PRECISION,
    "max_price" DOUBLE PRECISION,
    "modal_price" DOUBLE PRECISION NOT NULL,
    "unit" TEXT DEFAULT '₹/क्विंटल',
    "source" TEXT DEFAULT 'data.gov.in (Agmarknet)',
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "market_data" (
    "id" TEXT PRIMARY KEY,
    "commodity" TEXT NOT NULL,
    "variety" TEXT,
    "market_name" TEXT NOT NULL,
    "district" TEXT,
    "state" TEXT NOT NULL,
    "min_price" DOUBLE PRECISION,
    "max_price" DOUBLE PRECISION,
    "modal_price" DOUBLE PRECISION,
    "unit" TEXT DEFAULT '₹/Quintal',
    "updated_at" TEXT
);

CREATE TABLE IF NOT EXISTS "messages" (
    "id" TEXT PRIMARY KEY,
    "conversation_id" TEXT NOT NULL,
    "sender" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "provider" TEXT,
    "evidence_json" TEXT,
    "created_at" TEXT
);

CREATE TABLE IF NOT EXISTS "otps" (
    "id" BIGSERIAL PRIMARY KEY,
    "phone" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "expires_at" TEXT NOT NULL,
    "is_used" BIGINT DEFAULT 0,
    "created_at" TEXT NOT NULL,
    "logid" TEXT
);

CREATE TABLE IF NOT EXISTS "reminders" (
    "id" TEXT PRIMARY KEY,
    "farmer_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "due_date" TEXT,
    "is_completed" BIGINT DEFAULT 0,
    "created_at" TEXT,
    "reminder_type" TEXT DEFAULT 'general',
    "crop_id" TEXT,
    "priority" TEXT DEFAULT 'normal'
);

CREATE TABLE IF NOT EXISTS "sessions" (
    "id" TEXT PRIMARY KEY,
    "user_id" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "ip_address" TEXT,
    "user_agent" TEXT,
    "created_at" TEXT NOT NULL,
    "last_accessed_at" TEXT NOT NULL,
    "expires_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "soil_data" (
    "id" TEXT PRIMARY KEY,
    "farmer_id" TEXT NOT NULL,
    "field_id" TEXT,
    "soil_type" TEXT NOT NULL,
    "ph" DOUBLE PRECISION,
    "organic_carbon_pct" DOUBLE PRECISION,
    "nitrogen_kg_ha" DOUBLE PRECISION,
    "phosphorus_kg_ha" DOUBLE PRECISION,
    "potassium_kg_ha" DOUBLE PRECISION,
    "moisture_pct" DOUBLE PRECISION,
    "tested_at" TEXT
);

CREATE TABLE IF NOT EXISTS "users" (
    "id" TEXT PRIMARY KEY,
    "phone" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "password_hash" TEXT,
    "preferred_language" TEXT DEFAULT 'hi',
    "state" TEXT DEFAULT 'Uttar Pradesh',
    "district" TEXT DEFAULT 'Varanasi',
    "village" TEXT DEFAULT 'Rampur',
    "consent_json" TEXT,
    "created_at" TEXT,
    "status" TEXT DEFAULT 'active',
    "role" TEXT DEFAULT 'farmer'
);

CREATE TABLE IF NOT EXISTS "weather_cache" (
    "id" BIGSERIAL PRIMARY KEY,
    "lat" DOUBLE PRECISION NOT NULL,
    "lon" DOUBLE PRECISION NOT NULL,
    "temp_c" DOUBLE PRECISION,
    "rain_prob" BIGINT,
    "precipitation_mm" DOUBLE PRECISION,
    "humidity" BIGINT,
    "wind_kmh" DOUBLE PRECISION,
    "condition" TEXT,
    "spray_window_safe" BIGINT DEFAULT 1,
    "raw_json" TEXT,
    "fetched_at" TEXT
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_users_role ON "users"(role);
CREATE INDEX IF NOT EXISTS idx_users_status ON "users"(status);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON "sessions"(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON "sessions"(expires_at);
CREATE INDEX IF NOT EXISTS idx_crops_farmer ON "crops"(farmer_id);
CREATE INDEX IF NOT EXISTS idx_reminders_farmer ON "reminders"(farmer_id);
CREATE INDEX IF NOT EXISTS idx_hist_crop_state ON "crop_production_historical"(crop_name, state_name);
CREATE INDEX IF NOT EXISTS idx_hist_year ON "crop_production_historical"(year);
CREATE INDEX IF NOT EXISTS idx_mandi_commodity ON "live_mandi_prices"(commodity);