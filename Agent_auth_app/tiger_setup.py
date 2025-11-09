# Agent_auth_app/tiger_setup.py
from django.db import connection

def setup_tiger_features():
    """Setup pg_textsearch with BM25 indexing"""
    with connection.cursor() as cursor:
        # Enable extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_textsearch")
        
        # Create attack patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_attack_patterns (
                id SERIAL PRIMARY KEY,
                pattern TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                severity INTEGER DEFAULT 1,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Insert patterns
        cursor.execute("""
            INSERT INTO security_attack_patterns (pattern, pattern_type, severity) 
            VALUES 
            ('OR 1=1', 'sql_injection', 3),
            ('UNION SELECT', 'sql_injection', 3),
            ('; DROP', 'sql_injection', 4),
            ('<script>', 'xss', 2),
            ('javascript:', 'xss', 2)
            ON CONFLICT DO NOTHING
        """)
        
        # Create BM25 index for intelligent pattern matching
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS security_patterns_bm25_idx 
            ON security_attack_patterns 
            USING bm25(pattern)
            WITH (text_config='english')
        """)
        
    print("Real pg_textsearch setup complete with BM25 indexing!")