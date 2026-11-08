BEGIN;

ALTER TABLE enrollment_events
ADD COLUMN note VARCHAR(200);

INSERT INTO schema_migrations (version, description)
VALUES ('002', 'Add note column to enrollment_events');

COMMIT;

SELECT version, description, applied_at
FROM schema_migrations
ORDER BY version;