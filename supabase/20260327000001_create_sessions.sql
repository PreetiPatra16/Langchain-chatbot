-- Migration: Create sessions table
-- Purpose: Stores chat session metadata for the MOSTLY AI Docs RAG Chatbot.
-- This table tracks each user's chat session, including the current AI model being used.
-- Used by db.py in the chatbot backend to persist session information across API calls.
-- Location: Applied to Supabase database via migrations.

CREATE TABLE sessions (
    -- Primary key: auto-generated UUID for internal database use
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Client-generated session ID: unique identifier for each chat session (from api.py or app.py)
    session_id    UUID NOT NULL UNIQUE,
    -- Current AI model for this session (e.g., 'gemini-2.0-flash') - configurable per session
    current_model TEXT NOT NULL DEFAULT 'gemini-2.0-flash',
    -- Timestamps for auditing when sessions were created/updated
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Function to automatically update the updated_at timestamp on row updates
-- Ensures audit trail is maintained without manual intervention
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Automatically calls the update function before any UPDATE on sessions table
-- Keeps updated_at current for session management and debugging
CREATE TRIGGER sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
