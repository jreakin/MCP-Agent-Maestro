"""
PostgreSQL schema initialization for Agent-MCP.
This replaces the SQLite schema with PostgreSQL-compatible SQL.
"""
import os
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from ..core.config import logger
from .postgres_connection import get_postgres_connection, return_connection


def init_database() -> None:
    """
    Initializes the PostgreSQL database and creates tables if they don't exist.
    This function should be called once at application startup.
    """
    logger.info("Initializing PostgreSQL database schema...")

    conn = None
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()

        # Enable pgvector extension
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension: {e}")
            conn.rollback()

        # Agents Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                token VARCHAR(255) PRIMARY KEY,
                agent_id VARCHAR(255) UNIQUE NOT NULL,
                capabilities TEXT, -- JSON List
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) NOT NULL, -- e.g., 'created', 'active', 'terminated'
                current_task VARCHAR(255),    -- Task ID
                working_directory TEXT NOT NULL,
                color VARCHAR(50),           -- For dashboard visualization
                terminated_at TIMESTAMP,   -- Timestamp of termination
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Indexes for agents table
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents (status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents (agent_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_current_task ON agents (current_task) WHERE current_task IS NOT NULL"
        )
        logger.debug("Agents table and indexes ensured.")

        # Tasks Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id VARCHAR(255) PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                assigned_to VARCHAR(255),     -- Agent ID or None
                created_by VARCHAR(255) NOT NULL, -- Agent ID or 'admin'
                status VARCHAR(50) NOT NULL,     -- e.g., 'pending', 'in_progress', 'completed', 'cancelled', 'failed'
                priority VARCHAR(50) NOT NULL,   -- e.g., 'low', 'medium', 'high'
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                parent_task VARCHAR(255),         -- Task ID of parent task or None
                child_tasks TEXT,         -- JSON List of child Task IDs
                depends_on_tasks TEXT,    -- JSON List of Task IDs this task depends on
                notes TEXT,               -- JSON List of note objects: [{"timestamp": "", "author": "", "content": ""}]
                display_order INTEGER DEFAULT 0   -- Display order for kanban/sorting (higher = later)
            )
        """
        )
        # Indexes for tasks table
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks (assigned_to) WHERE assigned_to IS NOT NULL"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks (created_by)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_parent_task ON tasks (parent_task) WHERE parent_task IS NOT NULL"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks (updated_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks (status, priority)"
        )
        # Add display_order column if it doesn't exist (for existing databases)
        # This must be done BEFORE creating the index on display_order
        try:
            # Check if column exists first
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='tasks' AND column_name='display_order'
            """)
            column_exists = cursor.fetchone() is not None
            
            if not column_exists:
                cursor.execute("ALTER TABLE tasks ADD COLUMN display_order INTEGER DEFAULT 0")
                conn.commit()
                logger.debug("Added display_order column to tasks table")
            else:
                logger.debug("display_order column already exists in tasks table")
        except psycopg2.Error as e:
            # Error checking or adding column, but continue
            logger.warning(f"Could not ensure display_order column exists: {e}")
            conn.rollback()
        # Now create the index on display_order (after ensuring the column exists)
        try:
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_display_order ON tasks (display_order)"
            )
        except psycopg2.Error as e:
            # Index creation might fail if column doesn't exist, but that's okay
            logger.warning(f"Could not create display_order index: {e}")
            conn.rollback()
        logger.debug("Tasks table and indexes ensured.")

        # Agent Actions Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_actions (
                action_id SERIAL PRIMARY KEY,
                agent_id VARCHAR(255) NOT NULL, -- Can be agent_id or 'admin'
                action_type VARCHAR(100) NOT NULL, -- e.g., 'assigned_task', 'started_work', 'completed_task', 'updated_context', 'locked_file'
                task_id VARCHAR(255),          -- Optional: Link action to a specific task_id
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                details TEXT           -- Optional JSON blob for extra info (e.g., context_key, filepath, tool args)
            )
        """
        )
        # Indexes for agent_actions
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_actions_agent_id_timestamp ON agent_actions (agent_id, timestamp DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_actions_task_id_timestamp ON agent_actions (task_id, timestamp DESC)"
        )
        logger.debug("Agent_actions table and indexes ensured.")

        # Project Context Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_context (
                context_key VARCHAR(255) PRIMARY KEY,
                value TEXT NOT NULL,         -- Stored as JSON string
                last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(255) NOT NULL,    -- Agent ID or 'admin' or 'server_startup'
                description TEXT
            )
        """
        )
        # Index for project_context (last_updated for sorting)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_project_context_updated ON project_context (last_updated DESC)"
        )
        logger.debug("Project_context table and indexes ensured.")

        # File Metadata Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_metadata (
                filepath TEXT PRIMARY KEY,   -- Normalized, absolute path
                metadata TEXT NOT NULL,      -- JSON object containing various metadata keys/values
                last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(255) NOT NULL,    -- Agent ID or 'admin'
                content_hash VARCHAR(64)            -- SHA256 hash of file content, for change detection
            )
        """
        )
        # Index for file_metadata (last_updated for sorting)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_updated ON file_metadata (last_updated DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_hash ON file_metadata (content_hash) WHERE content_hash IS NOT NULL"
        )
        logger.debug("File_metadata table and indexes ensured.")

        # RAG Chunks Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_chunks (
                chunk_id SERIAL PRIMARY KEY,
                source_type VARCHAR(50) NOT NULL, -- e.g., 'markdown', 'context', 'filemeta', 'codefile', 'code', 'code_summary'
                source_ref TEXT NOT NULL,  -- Filepath, context_key, or other reference
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0, -- Index of this chunk within the source
                metadata TEXT, -- JSON object for additional metadata
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Indexes for RAG chunks
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rag_chunks_source ON rag_chunks (source_type, source_ref)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rag_chunks_created_at ON rag_chunks (created_at DESC)"
        )
        logger.debug("RAG_chunks table and indexes ensured.")

        # RAG Embeddings Table (using pgvector)
        try:
            # Get embedding dimension from environment or use default
            embedding_dim = int(os.environ.get("EMBEDDING_DIMENSION", "1536"))
            
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS rag_embeddings (
                    chunk_id INTEGER PRIMARY KEY REFERENCES rag_chunks(chunk_id) ON DELETE CASCADE,
                    embedding vector({embedding_dim}) NOT NULL,
                    model_name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            
            # Create index for vector similarity search
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_rag_embeddings_vector 
                ON rag_embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """
            )
            logger.debug("RAG_embeddings table with pgvector ensured.")
        except Exception as e:
            logger.warning(f"Could not create RAG embeddings table: {e}")
            conn.rollback()

        # RAG Meta Table (key-value store like SQLite version)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_meta (
                meta_key VARCHAR(255) PRIMARY KEY,
                meta_value TEXT
            )
        """
        )
        logger.debug("RAG_meta table ensured.")

        # Agent Messages Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_messages (
                message_id VARCHAR(255) PRIMARY KEY,
                sender_id VARCHAR(255) NOT NULL,
                recipient_id VARCHAR(255) NOT NULL,
                message_content TEXT NOT NULL,
                message_type VARCHAR(50) NOT NULL DEFAULT 'text',
                priority VARCHAR(50) NOT NULL DEFAULT 'normal',
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                delivered BOOLEAN NOT NULL DEFAULT FALSE,
                read BOOLEAN NOT NULL DEFAULT FALSE
            )
        """
        )
        # Indexes for agent_messages
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_recipient_timestamp ON agent_messages (recipient_id, timestamp DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_sender_timestamp ON agent_messages (sender_id, timestamp DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_unread ON agent_messages (recipient_id, read, timestamp DESC)"
        )
        logger.debug("Agent_messages table and indexes ensured.")

        # Claude Code Sessions Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS claude_code_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                pid INTEGER NOT NULL,
                parent_pid INTEGER NOT NULL,
                first_detected TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                working_directory TEXT,
                agent_id VARCHAR(255),              -- Links to agents.agent_id if registered
                status VARCHAR(50) DEFAULT 'detected',  -- detected, registered, active, inactive
                git_commits TEXT,           -- JSON array of commit hashes
                metadata TEXT               -- Additional session metadata
            )
        """
        )
        # Indexes for claude_code_sessions
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_claude_sessions_pid ON claude_code_sessions (pid, parent_pid)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_claude_sessions_activity ON claude_code_sessions (last_activity DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_claude_sessions_agent ON claude_code_sessions (agent_id)"
        )
        logger.debug("Claude_code_sessions table and indexes ensured.")

        # Tokens Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                token_type VARCHAR(50) PRIMARY KEY, -- 'admin_token' or 'agent_token'
                token_value TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        logger.debug("Tokens table ensured.")

        conn.commit()
        logger.info("PostgreSQL database schema initialized successfully.")

    except psycopg2.Error as e:
        logger.error(
            f"A PostgreSQL database error occurred during schema initialization: {e}",
            exc_info=True,
        )
        if conn:
            conn.rollback()
        raise RuntimeError(f"Failed to initialize database schema: {e}") from e
    except Exception as e:
        logger.error(
            f"Unexpected error during database schema initialization: {e}",
            exc_info=True,
        )
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_connection(conn)
            logger.debug("PostgreSQL connection closed after schema initialization.")
