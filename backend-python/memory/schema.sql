-- SQLite Performance and Resilience Tuning
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

-- 1. Multi-LLM Configurations
CREATE TABLE IF NOT EXISTS llm_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    api_key_encrypted TEXT,
    base_url TEXT,
    is_active INTEGER DEFAULT 0 CHECK (is_active IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    system_state TEXT DEFAULT 'ONLINE',
    crash_reason TEXT
);

-- 3. Conversation Context Logs
CREATE TABLE IF NOT EXISTS conversation_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message_content TEXT NOT NULL,
    audio_file_path TEXT,
    latency_ms INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
);

-- 4. Autonomous Task Executions
CREATE TABLE IF NOT EXISTS task_executions (
    task_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    initial_prompt TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'ABORTED', 'FAILED')),
    initiated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
);

-- 5. Atomic OS Action Logs
CREATE TABLE IF NOT EXISTS action_logs (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_payload TEXT NOT NULL,
    execution_order INTEGER NOT NULL,
    execution_status TEXT DEFAULT 'SUCCESS' CHECK (execution_status IN ('SUCCESS', 'SKIPPED', 'FAILED')),
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_executions (task_id) ON DELETE CASCADE
);

-- 6. Security Violations and Kill-Switch Audits
CREATE TABLE IF NOT EXISTS audit_violations (
    violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    violation_code TEXT NOT NULL,
    flagged_content TEXT NOT NULL,
    action_taken TEXT DEFAULT 'ABORT_TASK',
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_executions (task_id) ON DELETE CASCADE
);

-- Indices for Fast Querying and Context Hydration
CREATE INDEX IF NOT EXISTS idx_active_llm ON llm_configurations (is_active);
CREATE INDEX IF NOT EXISTS idx_conv_session_time ON conversation_logs (session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_task_session_status ON task_executions (session_id, status);
CREATE INDEX IF NOT EXISTS idx_action_task_order ON action_logs (task_id, execution_order);
CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_violations (task_id);
