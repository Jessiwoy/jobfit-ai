ALTER TABLE email_messages
ADD COLUMN detected_provider TEXT;

ALTER TABLE jobs
ADD COLUMN provider TEXT;

CREATE INDEX IF NOT EXISTS idx_email_messages_detected_provider
ON email_messages (detected_provider);

CREATE INDEX IF NOT EXISTS idx_jobs_provider
ON jobs (provider);

