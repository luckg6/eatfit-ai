"""
MySQL -> PostgreSQL data migration for eatfit_ai.

- Reads from MySQL (eatfit_ai), writes to PostgreSQL (eatfit_ai).
- Preserves original id values; PG sequences are advanced after insert.
- Handles MySQL quirks: 'null' string in metadata_json, tinyint->boolean, etc.
- embedding column is left NULL (embedding_status stays 'pending') until
  the embedding backfill step runs.
"""
import json
import pymysql
import psycopg2
from psycopg2.extras import Json, execute_values

MYSQL = dict(host='localhost', port=3306, user='root', password='gy7979829', database='eatfit_ai', charset='utf8mb4')
PG    = dict(host='localhost', port=5432, user='postgres', password='root', dbname='eatfit_ai')

def to_bool(v):
    if v is None: return None
    return bool(int(v))

def clean_metadata(v):
    """MySQL 'null' string -> real None."""
    if v is None: return None
    if isinstance(v, str) and v.strip() in ('null', 'NULL', ''):
        return None
    return v

def to_jsonb(v):
    v = clean_metadata(v)
    if v is None: return None
    if isinstance(v, (dict, list)): return Json(v)
    if isinstance(v, str):
        s = v.strip()
        if not s: return None
        return Json(json.loads(s))
    return Json(v)

# 1. static tables, no FK dependencies except users
def migrate_users(mc, pc):
    with mc.cursor() as cur:
        cur.execute("SELECT id, username, email, password_hash, auto_memory_enabled, created_at, updated_at FROM users ORDER BY id")
        rows = cur.fetchall()
    print(f"users: {len(rows)} rows")
    if not rows: return
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO users (id, username, email, password_hash, auto_memory_enabled, created_at, updated_at)
               VALUES %s
               ON CONFLICT (id) DO NOTHING""",
            [(r[0], r[1], r[2], r[3], to_bool(r[4]), r[5], r[6]) for r in rows])
        cur.execute("SELECT setval(pg_get_serial_sequence('users','id'), (SELECT MAX(id) FROM users))")

def migrate_user_food_profiles(mc, pc):
    with mc.cursor() as cur:
        cur.execute("""SELECT id, user_id, nickname, gender, age, height_cm, weight_kg, body_fat_percent,
                              target_weight_kg, primary_goal, activity_level, training_frequency, training_type,
                              food_preferences, food_dislikes, allergies, budget_per_meal,
                              common_eating_scenarios, sleep_sensitive, sleep_notes, notes, created_at, updated_at
                       FROM user_food_profiles ORDER BY id""")
        rows = cur.fetchall()
    print(f"user_food_profiles: {len(rows)} rows")
    if not rows: return
    data = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12],
             r[13], r[14], r[15], r[16], r[17], to_bool(r[18]), r[19], r[20], r[21], r[22]) for r in rows]
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO user_food_profiles
               (id, user_id, nickname, gender, age, height_cm, weight_kg, body_fat_percent,
                target_weight_kg, primary_goal, activity_level, training_frequency, training_type,
                food_preferences, food_dislikes, allergies, budget_per_meal,
                common_eating_scenarios, sleep_sensitive, sleep_notes, notes, created_at, updated_at)
               VALUES %s
               ON CONFLICT (id) DO NOTHING""", data)
        cur.execute("SELECT setval(pg_get_serial_sequence('user_food_profiles','id'), (SELECT MAX(id) FROM user_food_profiles))")

def migrate_advice_sessions(mc, pc):
    with mc.cursor() as cur:
        cur.execute("""SELECT id, user_id, title, user_question, context_text, ai_response_json,
                              scenario, is_training_day, created_at, updated_at, restaurant_context
                       FROM advice_sessions ORDER BY id""")
        rows = cur.fetchall()
    print(f"advice_sessions: {len(rows)} rows")
    if not rows: return
    data = [(r[0], r[1], r[2], r[3], r[4], to_jsonb(r[5]), r[6], to_bool(r[7]), r[8], r[9], to_jsonb(r[10])) for r in rows]
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO advice_sessions
               (id, user_id, title, user_question, context_text, ai_response_json,
                scenario, is_training_day, created_at, updated_at, restaurant_context)
               VALUES %s
               ON CONFLICT (id) DO NOTHING""", data)
        cur.execute("SELECT setval(pg_get_serial_sequence('advice_sessions','id'), (SELECT MAX(id) FROM advice_sessions))")

def migrate_chat_messages(mc, pc):
    with mc.cursor() as cur:
        cur.execute("""SELECT id, session_id, user_id, role, content, action_type, action_status,
                              action_data, created_at, updated_at
                       FROM chat_messages ORDER BY id""")
        rows = cur.fetchall()
    print(f"chat_messages: {len(rows)} rows")
    if not rows: return
    data = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], to_jsonb(r[7]), r[8], r[9]) for r in rows]
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO chat_messages
               (id, session_id, user_id, role, content, action_type, action_status, action_data, created_at, updated_at)
               VALUES %s
               ON CONFLICT (id) DO NOTHING""", data)
        cur.execute("SELECT setval(pg_get_serial_sequence('chat_messages','id'), (SELECT MAX(id) FROM chat_messages))")

def migrate_meal_logs(mc, pc):
    with mc.cursor() as cur:
        cur.execute("""SELECT id, user_id, meal_type, meal_time, food_text, scenario,
                              estimated_calories, estimated_protein, estimated_carbs, estimated_fat,
                              calorie_confidence, nutrition_source, source_message_id,
                              health_score, sleep_impact, ai_comment, created_at, updated_at
                       FROM meal_logs ORDER BY id""")
        rows = cur.fetchall()
    print(f"meal_logs: {len(rows)} rows")
    if not rows: return
    data = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
             r[10], r[11], r[12], r[13], r[14], r[15], r[16], r[17]) for r in rows]
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO meal_logs
               (id, user_id, meal_type, meal_time, food_text, scenario,
                estimated_calories, estimated_protein, estimated_carbs, estimated_fat,
                calorie_confidence, nutrition_source, source_message_id,
                health_score, sleep_impact, ai_comment, created_at, updated_at)
               VALUES %s
               ON CONFLICT (id) DO NOTHING""", data)
        cur.execute("SELECT setval(pg_get_serial_sequence('meal_logs','id'), (SELECT MAX(id) FROM meal_logs))")

def migrate_memory_items(mc, pc):
    with mc.cursor() as cur:
        cur.execute("""SELECT id, user_id, memory_type, content, importance_score, confidence_score,
                              source_message_id, source, status, created_at, updated_at,
                              last_used_at, metadata_json
                       FROM memory_items ORDER BY id""")
        rows = cur.fetchall()
    print(f"memory_items: {len(rows)} rows")
    if not rows: return
    # embedding is NULL for now; embedding_status='pending'
    data = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], to_jsonb(r[12]), 'pending', None) for r in rows]
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO memory_items
               (id, user_id, memory_type, content, importance_score, confidence_score,
                source_message_id, source, status, created_at, updated_at,
                last_used_at, metadata_json, embedding_status, embedding_updated_at)
               VALUES %s
               ON CONFLICT (id) DO NOTHING""", data)
        cur.execute("SELECT setval(pg_get_serial_sequence('memory_items','id'), (SELECT MAX(id) FROM memory_items))")

def migrate_weight_records(mc, pc):
    with mc.cursor() as cur:
        cur.execute("SELECT id, user_id, weight_kg, record_date, note, created_at FROM weight_records ORDER BY id")
        rows = cur.fetchall()
    print(f"weight_records: {len(rows)} rows")
    if not rows: return
    with pc.cursor() as cur:
        execute_values(cur,
            "INSERT INTO weight_records (id, user_id, weight_kg, record_date, note, created_at) VALUES %s ON CONFLICT (id) DO NOTHING",
            rows)
        cur.execute("SELECT setval(pg_get_serial_sequence('weight_records','id'), (SELECT MAX(id) FROM weight_records))")

def migrate_body_fat_records(mc, pc):
    with mc.cursor() as cur:
        cur.execute("SELECT id, user_id, body_fat_percent, record_date, note, created_at FROM body_fat_records ORDER BY id")
        rows = cur.fetchall()
    print(f"body_fat_records: {len(rows)} rows")
    if not rows: return
    with pc.cursor() as cur:
        execute_values(cur,
            "INSERT INTO body_fat_records (id, user_id, body_fat_percent, record_date, note, created_at) VALUES %s ON CONFLICT (id) DO NOTHING",
            rows)
        cur.execute("SELECT setval(pg_get_serial_sequence('body_fat_records','id'), (SELECT MAX(id) FROM body_fat_records))")

def migrate_training_records(mc, pc):
    with mc.cursor() as cur:
        cur.execute("SELECT id, user_id, training_type, duration_minutes, intensity, record_date, note, created_at FROM training_records ORDER BY id")
        rows = cur.fetchall()
    print(f"training_records: {len(rows)} rows")
    if not rows: return
    with pc.cursor() as cur:
        execute_values(cur,
            "INSERT INTO training_records (id, user_id, training_type, duration_minutes, intensity, record_date, note, created_at) VALUES %s ON CONFLICT (id) DO NOTHING",
            rows)
        cur.execute("SELECT setval(pg_get_serial_sequence('training_records','id'), (SELECT MAX(id) FROM training_records))")

def migrate_diet_advice_records(mc, pc):
    with mc.cursor() as cur:
        cur.execute("""SELECT id, user_id, session_id, situation_summary, recommendation_strategy,
                              recommended_options_json, not_recommended_json, estimated_summary_json,
                              next_meal_advice, sleep_friendly_tips, risk_level, created_at
                       FROM diet_advice_records ORDER BY id""")
        rows = cur.fetchall()
    print(f"diet_advice_records: {len(rows)} rows")
    if not rows: return
    data = [(r[0], r[1], r[2], r[3], r[4], to_jsonb(r[5]), to_jsonb(r[6]), to_jsonb(r[7]), r[8], r[9], r[10], r[11]) for r in rows]
    with pc.cursor() as cur:
        execute_values(cur,
            """INSERT INTO diet_advice_records
               (id, user_id, session_id, situation_summary, recommendation_strategy,
                recommended_options_json, not_recommended_json, estimated_summary_json,
                next_meal_advice, sleep_friendly_tips, risk_level, created_at)
               VALUES %s ON CONFLICT (id) DO NOTHING""", data)
        cur.execute("SELECT setval(pg_get_serial_sequence('diet_advice_records','id'), (SELECT MAX(id) FROM diet_advice_records))")

def verify(mc, pc):
    tables = ['users','user_food_profiles','memory_items','meal_logs','advice_sessions',
              'chat_messages','weight_records','body_fat_records','training_records','diet_advice_records']
    print("\n=== row count comparison ===")
    print(f"{'table':25s} {'mysql':>8s} {'pg':>8s}")
    with mc.cursor() as cur, pc.cursor() as pc2:
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{t}`")
            m = cur.fetchone()[0]
            pc2.execute(f"SELECT COUNT(*) FROM {t}")
            p = pc2.fetchone()[0]
            ok = "OK" if m == p else "DIFF"
            print(f"{t:25s} {m:>8d} {p:>8d}  {ok}")

def main():
    print("Connecting to MySQL and PostgreSQL...")
    mc = pymysql.connect(**MYSQL)
    pc = psycopg2.connect(**PG)
    try:
        # FK-safe order
        migrate_users(mc, pc)
        pc.commit()
        migrate_user_food_profiles(mc, pc)
        pc.commit()
        migrate_advice_sessions(mc, pc)
        pc.commit()
        migrate_chat_messages(mc, pc)
        pc.commit()
        migrate_meal_logs(mc, pc)
        pc.commit()
        migrate_memory_items(mc, pc)
        pc.commit()
        migrate_weight_records(mc, pc)
        pc.commit()
        migrate_body_fat_records(mc, pc)
        pc.commit()
        migrate_training_records(mc, pc)
        pc.commit()
        migrate_diet_advice_records(mc, pc)
        pc.commit()
        verify(mc, pc)
        print("\nMigration complete.")
    finally:
        mc.close()
        pc.close()

if __name__ == "__main__":
    main()
