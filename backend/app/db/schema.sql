PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  device_id TEXT NOT NULL,
  scenario TEXT NOT NULL,
  transport TEXT NOT NULL,
  tls_enabled INTEGER NOT NULL,
  connection_mode TEXT NOT NULL,
  payload_bytes INTEGER NOT NULL,
  planned_messages INTEGER,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  seq INTEGER NOT NULL,
  payload_bytes INTEGER NOT NULL,
  total_bytes INTEGER NOT NULL,
  overhead_bytes INTEGER NOT NULL,
  latency_ms REAL NOT NULL,
  energy_mj REAL NOT NULL,

  FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
  UNIQUE (run_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_messages_run_id ON messages(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_scenario ON runs(scenario);
CREATE INDEX IF NOT EXISTS idx_runs_device ON runs(device_id);
