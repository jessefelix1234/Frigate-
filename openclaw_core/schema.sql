PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS provider_quota (
    provider TEXT PRIMARY KEY,
    used_tokens INTEGER NOT NULL DEFAULT 0,
    monthly_limit INTEGER NOT NULL,
    last_reset DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
    tier INTEGER NOT NULL CHECK(tier BETWEEN 1 AND 3),
    payload TEXT NOT NULL,
    context_refs TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    token_estimate INTEGER NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 5,
    next_run_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('pending','in_progress','completed','failed')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS dead_letter_tasks (
    task_id TEXT,
    task_type TEXT,
    payload TEXT,
    context_refs TEXT,
    failure_type TEXT,
    failure_time DATETIME,
    attempts INTEGER,
    original_created DATETIME
);

CREATE TABLE IF NOT EXISTS task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    provider TEXT,
    token_estimate INTEGER,
    token_actual INTEGER,
    latency_ms INTEGER,
    outcome TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS live_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
