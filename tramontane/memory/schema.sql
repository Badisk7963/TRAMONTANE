-- Tramontane Memory Schema v1
-- Auto-applied on first write. Also runnable via `tramontane init`.

-- Schema version tracking
CREATE TABLE IF NOT EXISTS tramontane_schema (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
INSERT OR IGNORE INTO tramontane_schema VALUES (1, CURRENT_TIMESTAMP, 'Initial schema');

-- Main memory table
CREATE TABLE IF NOT EXISTS tramontane_memory (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    pipeline_name TEXT,
    entity_key TEXT,
    memory_type TEXT,  -- fact | preference | history | entity
    content TEXT NOT NULL,
    embedding BLOB,    -- mistral-embed vector
    importance REAL DEFAULT 0.5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME,
    access_count INTEGER DEFAULT 0,
    expires_at DATETIME,   -- NULL = permanent
    erased_at DATETIME     -- GDPR Article 17
);

-- Full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS tramontane_memory_fts
USING fts5(content, entity_key, pipeline_name, content=tramontane_memory, content_rowid=rowid);

-- GDPR erasure log
CREATE TABLE IF NOT EXISTS tramontane_erasure_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    erased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    erased_count INTEGER,
    requested_by TEXT
);

-- Audit log (APPEND ONLY — never delete rows)
CREATE TABLE IF NOT EXISTS tramontane_audit (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    pipeline_name TEXT,
    agent_role TEXT,
    action_type TEXT,  -- llm_call | tool_call | handoff | error
    model_used TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_eur REAL,
    gdpr_sensitivity TEXT,
    pii_detected BOOLEAN,
    pii_redacted BOOLEAN,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT      -- JSON
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_memory_user_id ON tramontane_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_entity_key ON tramontane_memory(entity_key);
CREATE INDEX IF NOT EXISTS idx_memory_pipeline ON tramontane_memory(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_memory_expires ON tramontane_memory(expires_at)
    WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_run_id ON tramontane_audit(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_pipeline ON tramontane_audit(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON tramontane_audit(timestamp);
