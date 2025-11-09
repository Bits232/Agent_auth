# Agent_auth_app/security_checker.py
from django.db import connection
import os, requests, json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Ensure this is set in your .env

class SecurityChecker:
    @staticmethod
    def check_input(user_input):
        """Use REAL pg_textsearch + fallback AI agent"""
        threats = []
        used_ai = False

        print(f"\n🧠 [SECURITY_CHECKER] Analyzing input: {user_input}")

        with connection.cursor() as cursor:
            try:
                # --- PostgreSQL BM25 search ---
                cursor.execute("""
                    SELECT DISTINCT pattern, pattern_type, severity,
                           text_bm25query_score(pattern, to_bm25query(%s, 'security_patterns_bm25_idx')) AS bm25_score
                    FROM security_attack_patterns 
                    WHERE text_bm25query_score(pattern, to_bm25query(%s, 'security_patterns_bm25_idx')) < -0.1
                    ORDER BY bm25_score
                    LIMIT 5
                """, [user_input, user_input])

                threats = cursor.fetchall()
                print(f"✅ [PG] Using REAL pg_textsearch BM25 — found {len(threats)} threats")

            except Exception as e:
                print(f"❌ [PG] pg_textsearch failed: {e}")
                cursor.execute("""
                    SELECT DISTINCT pattern, pattern_type, severity
                    FROM security_attack_patterns 
                    WHERE %s ILIKE '%%' || pattern || '%%'
                """, [user_input])
                threats = cursor.fetchall()
                print(f"📋 [PG] Using fallback SQL — found {len(threats)} threats")

        # If PG found nothing, escalate to AI (without storing new patterns)
        if not threats:
            print("🤖 [AI_AGENT] No results from pg_textsearch → escalating to AI Agent...")
            ai_result = SecurityChecker.analyze_with_ai(user_input)
            if ai_result:
                used_ai = True
                threats.append(ai_result)

        # --- Structure final output ---
        structured = [ {
            'pattern': t[0] if isinstance(t, (list, tuple)) else t.get('pattern'),
            'type': t[1] if isinstance(t, (list, tuple)) else t.get('type'),
            'severity': t[2] if isinstance(t, (list, tuple)) else t.get('severity'),
            'bm25_score': t[3] if isinstance(t, (list, tuple)) and len(t) > 3 else None
        } for t in threats ]

        if used_ai:
            print("⚡ [AI_AGENT] AI-based analysis included in final results")
        elif not threats:
            print("✅ [SAFE] No threats detected by PG or AI agent")
        else:
            print("🚨 [PG] Threats found and returned from database")

        return structured

    @staticmethod
    def analyze_with_ai(user_input):
        """Groq AI Security Agent – checks for suspicious behavior"""
        if not GROQ_API_KEY:
            print("⚠️ [AI_AGENT] Missing GROQ_API_KEY — skipping AI analysis.")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            prompt = f"""
You are a security input classifier. Determine if this input is malicious or safe.
Only flag inputs with clear attack patterns: SQL Injection, XSS, Command Injection.
Input: {user_input}

Respond ONLY in JSON with this format:
{{
    "pattern": "exact input or relevant keyword",
    "type": "SQL Injection | XSS | Command Injection | Safe | Other",
    "severity": "low | medium | high | critical",
    "action": "flag | ignore | log"
}}
            """

            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=payload, timeout=10
            )

            text = response.json()["choices"][0]["message"]["content"].strip()
            result = json.loads(text)
            print(f"🧩 [AI_AGENT] Result: {result}")

            # Do NOT add anything to the DB
            return result

        except Exception as e:
            print(f"❌ [AI_AGENT] Error during AI analysis: {e}")
            return None
