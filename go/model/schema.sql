CREATE TABLE IF NOT EXISTS schemas (
    table_name TEXT PRIMARY KEY,
    schema_version INT NOT NULL
);

DO $$
BEGIN
IF NOT EXISTS (SELECT 1 FROM schemas WHERE table_name = 'tasks') THEN
    CREATE TABLE tasks (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        priority INTEGER NOT NULL CHECK (priority >= 0 AND priority <= 3),
        estimate_minutes INTEGER NOT NULL CHECK (estimate_minutes > 0),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_tasks_date ON tasks(date);
    CREATE INDEX idx_tasks_priority ON tasks(priority);

    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $func$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $func$ LANGUAGE plpgsql;

    CREATE TRIGGER update_tasks_updated_at
        BEFORE UPDATE ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Record schema version for tasks table
    INSERT INTO schemas (table_name, schema_version) VALUES ('tasks', 1);
END IF;
END $$ LANGUAGE plpgsql;
