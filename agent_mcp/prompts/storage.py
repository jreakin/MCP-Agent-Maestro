# Agent-MCP Prompt Storage
"""
Persistence layer for prompt templates.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.config import logger
from ..db import get_db_connection, return_connection


class PromptStorage:
    """Storage layer for prompt templates."""
    
    def create_prompt(self, prompt_data: Dict[str, Any], created_by: str = "admin") -> str:
        """
        Create a new prompt template.
        
        Args:
            prompt_data: Prompt data dictionary
            created_by: User/agent ID that created the prompt
            
        Returns:
            Prompt ID
        """
        prompt_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO prompts (
                    prompt_id, name, description, category, agent_roles,
                    template, variables, examples, tags, created_at, updated_at, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    prompt_id,
                    prompt_data.get('name'),
                    prompt_data.get('description'),
                    prompt_data.get('category', 'general'),
                    json.dumps(prompt_data.get('agent_roles', [])),
                    prompt_data.get('template'),
                    json.dumps(prompt_data.get('variables', [])),
                    json.dumps(prompt_data.get('examples', [])),
                    json.dumps(prompt_data.get('tags', [])),
                    now,
                    now,
                    created_by
                )
            )
            conn.commit()
            logger.info(f"Created prompt: {prompt_id}")
            return prompt_id
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating prompt: {e}", exc_info=True)
            raise
        finally:
            if conn:
                return_connection(conn)
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by ID."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prompts WHERE prompt_id = %s", (prompt_id,))
            row = cursor.fetchone()
            if row:
                return self._parse_prompt_row(dict(row))
            return None
        except Exception as e:
            logger.error(f"Error getting prompt {prompt_id}: {e}", exc_info=True)
            return None
        finally:
            if conn:
                return_connection(conn)
    
    def list_prompts(
        self,
        category: Optional[str] = None,
        agent_role: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """List prompts with optional filters."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM prompts WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = %s"
                params.append(category)
            
            if agent_role:
                query += " AND (agent_roles::jsonb ? %s OR agent_roles::jsonb = '[]'::jsonb)"
                params.append(agent_role)
            
            if tags:
                for tag in tags:
                    query += " AND (tags::jsonb ? %s)"
                    params.append(tag)
            
            query += " ORDER BY usage_count DESC, created_at DESC"
            
            cursor.execute(query, tuple(params))
            return [self._parse_prompt_row(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error listing prompts: {e}", exc_info=True)
            return []
        finally:
            if conn:
                return_connection(conn)
    
    def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> bool:
        """Update a prompt."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            for field, value in updates.items():
                if field in ['name', 'description', 'category', 'template']:
                    update_fields.append(f"{field} = %s")
                    params.append(value)
                elif field in ['agent_roles', 'variables', 'examples', 'tags']:
                    update_fields.append(f"{field} = %s")
                    params.append(json.dumps(value) if value else '[]')
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = %s")
            params.append(datetime.now().isoformat())
            params.append(prompt_id)
            
            query = f"UPDATE prompts SET {', '.join(update_fields)} WHERE prompt_id = %s"
            cursor.execute(query, tuple(params))
            conn.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating prompt {prompt_id}: {e}", exc_info=True)
            return False
        finally:
            if conn:
                return_connection(conn)
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prompts WHERE prompt_id = %s", (prompt_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error deleting prompt {prompt_id}: {e}", exc_info=True)
            return False
        finally:
            if conn:
                return_connection(conn)
    
    def increment_usage(self, prompt_id: str) -> None:
        """Increment usage count for a prompt."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE prompts SET usage_count = usage_count + 1 WHERE prompt_id = %s",
                (prompt_id,)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing usage for prompt {prompt_id}: {e}")
        finally:
            if conn:
                return_connection(conn)
    
    def _parse_prompt_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Parse prompt row from database."""
        parsed = row.copy()
        for field in ['agent_roles', 'variables', 'examples', 'tags']:
            if field in parsed and isinstance(parsed[field], str):
                try:
                    parsed[field] = json.loads(parsed[field] or '[]')
                except json.JSONDecodeError:
                    parsed[field] = []
        return parsed


def get_prompt_storage() -> PromptStorage:
    """Get prompt storage instance."""
    return PromptStorage()

