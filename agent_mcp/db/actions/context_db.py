# Agent-MCP/agent_mcp/db/actions/context_db.py
"""
Context database operations.
This module provides functions for managing project context in the database.
"""

import psycopg2
import json
from typing import Dict, Optional, List, Any
from ...core.config import logger
from ..connection_factory import get_db_connection, db_connection
from ..postgres_connection import return_connection

def get_context() -> Optional[Dict[str, Any]]:
    """Get the current project context from the database."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_context")
            rows = cursor.fetchall()
            context = {}
            for row in rows:
                context[row['context_key']] = json.loads(row['value']) if row['value'] else None
            return context if context else None
    except psycopg2.Error as e:
        logger.error(f"Database error fetching context: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching context: {e}", exc_info=True)
        return None


def get_context_by_key(context_key: str) -> Optional[Dict[str, Any]]:
    """Get a specific context entry by key from the database."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT context_key, value, description, last_updated, updated_by FROM project_context WHERE context_key = %s",
                (context_key,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "context_key": row['context_key'],
                    "value": json.loads(row['value']) if row['value'] else None,
                    "description": row.get('description'),
                    "last_updated": row.get('last_updated'),
                    "updated_by": row.get('updated_by')
                }
            return None
    except psycopg2.Error as e:
        logger.error(f"Database error fetching context key {context_key}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching context key {context_key}: {e}", exc_info=True)
        return None

def update_context(context_data: Dict[str, Any]) -> bool:
    """Update the project context in the database."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            for key, value in context_data.items():
                cursor.execute("""
                    INSERT INTO project_context (context_key, value, last_updated, updated_by)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, 'admin')
                    ON CONFLICT (context_key) 
                    DO UPDATE SET value = %s, last_updated = CURRENT_TIMESTAMP
                """, (key, json.dumps(value), json.dumps(value)))
            
            conn.commit()
            logger.info(f"Updated context: {list(context_data.keys())}")
            return True
    except psycopg2.Error as e:
        logger.error(f"Database error updating context: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating context: {e}", exc_info=True)
        return False
