-- Инициализация базы данных PromoAI RAG

-- Создаем расширение pgvector если его нет
CREATE EXTENSION IF NOT EXISTS vector;

-- Создаем схему для приложения
CREATE SCHEMA IF NOT EXISTS app;

-- Устанавливаем поисковый путь
SET search_path TO app, public;

-- Создаем таблицу пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем таблицу документов
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mime VARCHAR(100) NOT NULL,
    storage_uri VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'uploaded',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем таблицу чанков документов
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES app.documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536), -- для OpenAI embeddings
    chunk_index INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем таблицу задач
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем таблицу API ключей
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Создаем таблицу использования
CREATE TABLE IF NOT EXISTS usage (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    queries_count INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON app.users(email);
CREATE INDEX IF NOT EXISTS idx_documents_status ON app.documents(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON app.jobs(status);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON app.api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_tenant_date ON app.usage(tenant_id, date);

-- Создаем векторный индекс для поиска по embeddings
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON app.document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Создаем триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применяем триггер к таблицам
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON app.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON app.documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON app.jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создаем представление для статистики пользователя
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.tenant_id,
    u.role,
    COUNT(DISTINCT d.id) as documents_count,
    COUNT(DISTINCT j.id) as jobs_count,
    COUNT(DISTINCT ak.id) as api_keys_count,
    COALESCE(SUM(u_usage.queries_count), 0) as total_queries,
    COALESCE(SUM(u_usage.documents_processed), 0) as total_documents_processed,
    COALESCE(SUM(u_usage.tokens_used), 0) as total_tokens_used
FROM app.users u
LEFT JOIN app.documents d ON u.tenant_id = u.tenant_id
LEFT JOIN app.jobs j ON u.tenant_id = u.tenant_id
LEFT JOIN app.api_keys ak ON u.tenant_id = ak.tenant_id
LEFT JOIN app.usage u_usage ON u.tenant_id = u_usage.tenant_id
GROUP BY u.id, u.email, u.tenant_id, u.role;

-- Выводим сообщение об успешной инициализации
SELECT 'База данных PromoAI RAG успешно инициализирована!' as message;
