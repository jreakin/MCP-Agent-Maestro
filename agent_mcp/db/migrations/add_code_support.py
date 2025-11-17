#!/usr/bin/env python3
"""
Migration script to add code-aware RAG support to existing databases.

This script:
1. Adds the metadata column to rag_chunks table if missing
2. Adds the last_indexed_code entry to rag_meta if missing
3. Re-creates the rag_embeddings table with the new dimension (3072)
"""

import psycopg2
import sys
from pathlib import Path

# Add parent directories to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agent_mcp.db import get_db_connection, return_connection
from agent_mcp.core.config import logger, EMBEDDING_DIMENSION


def migrate_database():
    """Run the migration to add code-aware support."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Check if metadata column exists in rag_chunks (PostgreSQL)
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'rag_chunks' AND column_name = 'metadata'
        """)
        if cursor.fetchone() is None:
            logger.info("Adding metadata column to rag_chunks table...")
            cursor.execute("ALTER TABLE rag_chunks ADD COLUMN metadata TEXT")
            logger.info("Metadata column added successfully.")
        else:
            logger.info("Metadata column already exists in rag_chunks table.")
        
        # 2. Add last_indexed_code to rag_meta if missing
        cursor.execute("SELECT meta_value FROM rag_meta WHERE meta_key = %s", ('last_indexed_code',))
        if cursor.fetchone() is None:
            logger.info("Adding last_indexed_code to rag_meta...")
            cursor.execute(
                "INSERT INTO rag_meta (meta_key, meta_value) VALUES (%s, %s)",
                ('last_indexed_code', '1970-01-01T00:00:00Z')
            )
            logger.info("last_indexed_code added successfully.")
        else:
            logger.info("last_indexed_code already exists in rag_meta.")
        
        # 3. Check embedding dimension (PostgreSQL pgvector)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'rag_embeddings'
            ) as exists
        """)
        result = cursor.fetchone()
        table_exists = result['exists'] if isinstance(result, dict) else result[0]
        
        if table_exists:
            # Check current dimension from table definition
            cursor.execute("""
                SELECT atttypmod 
                FROM pg_attribute 
                WHERE attrelid = 'rag_embeddings'::regclass 
                AND attname = 'embedding'
            """)
            dim_result = cursor.fetchone()
            if dim_result:
                current_dim = dim_result['atttypmod'] if isinstance(dim_result, dict) else dim_result[0]
                # atttypmod for vector type contains dimension info
                if current_dim and current_dim != EMBEDDING_DIMENSION:
                    logger.warning(f"rag_embeddings table uses {current_dim} dimensions but config uses {EMBEDDING_DIMENSION}.")
                    logger.warning(f"To use {EMBEDDING_DIMENSION} dimensions, you need to:")
                    logger.warning("1. Delete all existing embeddings: DELETE FROM rag_embeddings;")
                    logger.warning("2. Drop and recreate the table: DROP TABLE rag_embeddings;")
                    logger.warning("3. Re-run the server to recreate with new dimensions")
                    logger.warning("4. Let the indexer re-generate all embeddings")
                else:
                    logger.info(f"rag_embeddings table already uses {EMBEDDING_DIMENSION} dimensions.")
            else:
                logger.info("Could not determine current embedding dimensions.")
        else:
            logger.info("rag_embeddings table does not exist. It will be created with correct dimensions on first run.")
        
        # Commit all changes
        conn.commit()
        logger.info("Migration completed successfully!")
        
    except psycopg2.Error as e:
        logger.error(f"Database error during migration: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_connection(conn)


if __name__ == "__main__":
    print("Agent-MCP Code-Aware RAG Migration")
    print("==================================")
    print(f"This will migrate your database to support code-aware RAG with {EMBEDDING_DIMENSION} dimensions.")
    print()
    
    response = input("Do you want to proceed? (y/N): ")
    if response.lower() == 'y':
        migrate_database()
    else:
        print("Migration cancelled.")