#!/usr/bin/env python3
"""
Test script to verify PostgreSQL setup and database operations.
Run this inside the Docker container or with proper environment variables set.
"""
import os
import sys
from agent_mcp.db import get_db_connection, return_connection
from agent_mcp.db.postgres_schema import init_database

def test_connection():
    """Test basic database connection."""
    print("Testing PostgreSQL connection...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        # RealDictCursor returns dict, not tuple
        version_str = version['version'] if isinstance(version, dict) else version[0]
        print(f"✅ Connected to PostgreSQL: {version_str}")
        return_connection(conn)
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_schema():
    """Test database schema initialization."""
    print("\nTesting schema initialization...")
    try:
        init_database()
        print("✅ Schema initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Schema initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tables():
    """Test that all required tables exist."""
    print("\nTesting table existence...")
    required_tables = [
        'agents', 'tasks', 'agent_actions', 'project_context',
        'file_metadata', 'rag_chunks', 'rag_embeddings', 'rag_meta',
        'agent_messages', 'claude_code_sessions', 'tokens'
    ]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        missing_tables = []
        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                ) as exists;
            """, (table,))
            result = cursor.fetchone()
            exists = result['exists'] if isinstance(result, dict) else result[0]
            if not exists:
                missing_tables.append(table)
            else:
                print(f"  ✅ Table '{table}' exists")
        
        return_connection(conn)
        
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("✅ All required tables exist")
            return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pgvector():
    """Test pgvector extension."""
    print("\nTesting pgvector extension...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if extension exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_extension 
                WHERE extname = 'vector'
            ) as exists;
        """)
        result = cursor.fetchone()
        exists = result['exists'] if isinstance(result, dict) else result[0]
        
        if exists:
            print("✅ pgvector extension is installed")
            
            # Test vector type (use a valid vector with dimension)
            cursor.execute("SELECT '[1,2,3]'::vector(3) as vec;")
            result = cursor.fetchone()
            vec_result = result['vec'] if isinstance(result, dict) else result[0]
            print(f"✅ Vector type works: {vec_result}")
            return_connection(conn)
            return True
        else:
            print("❌ pgvector extension not found")
            return_connection(conn)
            return False
    except Exception as e:
        print(f"❌ pgvector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_operations():
    """Test basic CRUD operations."""
    print("\nTesting basic CRUD operations...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test INSERT
        test_agent_id = "test_agent_12345"
        cursor.execute("""
            INSERT INTO agents (agent_id, token, status, capabilities, working_directory)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (agent_id) DO UPDATE SET token = EXCLUDED.token
        """, (test_agent_id, "test_token", "active", "[]", "/tmp"))
        conn.commit()
        print("  ✅ INSERT operation works")
        
        # Test SELECT
        cursor.execute("SELECT * FROM agents WHERE agent_id = %s", (test_agent_id,))
        result = cursor.fetchone()
        if result:
            print(f"  ✅ SELECT operation works: found agent {result['agent_id']}")
        else:
            print("  ❌ SELECT operation failed: agent not found")
            return_connection(conn)
            return False
        
        # Test UPDATE
        cursor.execute("""
            UPDATE agents SET status = %s WHERE agent_id = %s
        """, ("terminated", test_agent_id))
        conn.commit()
        print("  ✅ UPDATE operation works")
        
        # Test DELETE
        cursor.execute("DELETE FROM agents WHERE agent_id = %s", (test_agent_id,))
        conn.commit()
        print("  ✅ DELETE operation works")
        
        return_connection(conn)
        print("✅ All CRUD operations work correctly")
        return True
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Agent-MCP PostgreSQL Setup Test")
    print("=" * 60)
    
    # Check environment variables
    print("\nEnvironment variables:")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "agent_mcp")
    db_user = os.environ.get("DB_USER", "agent_mcp")
    print(f"  DB_HOST: {db_host}")
    print(f"  DB_PORT: {db_port}")
    print(f"  DB_NAME: {db_name}")
    print(f"  DB_USER: {db_user}")
    
    results = []
    results.append(("Connection", test_connection()))
    results.append(("Schema", test_schema()))
    results.append(("Tables", test_tables()))
    results.append(("pgvector", test_pgvector()))
    results.append(("CRUD Operations", test_basic_operations()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
