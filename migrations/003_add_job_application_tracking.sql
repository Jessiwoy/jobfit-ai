ALTER TABLE jobs
ADD COLUMN application_status TEXT NOT NULL DEFAULT 'not_applied';

ALTER TABLE jobs
ADD COLUMN applied_at TEXT;

CREATE INDEX IF NOT EXISTS idx_jobs_application_status
ON jobs (application_status);
