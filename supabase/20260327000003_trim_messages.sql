-- Trim trigger: keep only the 50 most recent messages per session
-- Fires after each INSERT to prevent unbounded growth
CREATE OR REPLACE FUNCTION trim_session_messages()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM messages
    WHERE session_id = NEW.session_id
      AND id NOT IN (
        SELECT id FROM messages
        WHERE session_id = NEW.session_id
        ORDER BY created_at DESC
        LIMIT 50
      );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trim_messages_after_insert
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION trim_session_messages();
