import re
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.supabase_client import supabase_client

def execute_supabase_write(query: str, params: tuple = ()):
    if not supabase_client.is_configured():
        return None
        
    q = query.strip()
    q_upper = q.upper()
    
    # 1. INSERT
    if q_upper.startswith("INSERT"):
        m = re.search(r"INSERT\s+(?:OR\s+REPLACE\s+|OR\s+IGNORE\s+)?INTO\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*VALUES\s*\((.*?)\)", q, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        table = m.group(1).lower()
        cols = [c.strip().strip('"').strip('`') for c in m.group(2).split(",")]
        val_tokens = [v.strip() for v in m.group(3).split(",")]
        
        row_dict = {}
        param_idx = 0
        for col, token in zip(cols, val_tokens):
            if token == "?":
                if param_idx < len(params):
                    row_dict[col] = params[param_idx]
                    param_idx += 1
            else:
                # literal value, e.g. 0 or 'hi'
                clean_val = token.strip("'\"")
                if clean_val.isdigit():
                    row_dict[col] = int(clean_val)
                else:
                    row_dict[col] = clean_val
                    
        return supabase_client.insert(table, row_dict, upsert=True)

    # 2. UPDATE
    elif q_upper.startswith("UPDATE"):
        m = re.search(r"UPDATE\s+([a-zA-Z0-9_]+)\s+SET\s+(.*?)\s+WHERE\s+(.*)", q, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        table = m.group(1).lower()
        set_clause = m.group(2).strip()
        where_clause = m.group(3).strip()
        
        update_data = {}
        param_idx = 0
        for item in set_clause.split(","):
            if "=" in item:
                col, val = item.split("=", 1)
                col = col.strip().strip('"').strip('`')
                val = val.strip()
                if val == "?":
                    if param_idx < len(params):
                        update_data[col] = params[param_idx]
                        param_idx += 1
                else:
                    clean_val = val.strip("'\"")
                    update_data[col] = int(clean_val) if clean_val.isdigit() else clean_val

        filters = {}
        for item in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE):
            if "=" in item:
                col, val = item.split("=", 1)
                col = col.strip().strip('"').strip('`')
                val = val.strip()
                if val == "?":
                    if param_idx < len(params):
                        filters[col] = params[param_idx]
                        param_idx += 1
                else:
                    clean_val = val.strip("'\"")
                    filters[col] = int(clean_val) if clean_val.isdigit() else clean_val
                    
        return supabase_client.update(table, update_data, filters)

    # 3. DELETE
    elif q_upper.startswith("DELETE"):
        m = re.search(r"DELETE\s+FROM\s+([a-zA-Z0-9_]+)\s+WHERE\s+(.*)", q, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        table = m.group(1).lower()
        where_clause = m.group(2).strip()
        
        filters = {}
        param_idx = 0
        for item in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE):
            if "=" in item:
                col, val = item.split("=", 1)
                col = col.strip().strip('"').strip('`')
                val = val.strip()
                if val == "?":
                    if param_idx < len(params):
                        filters[col] = params[param_idx]
                        param_idx += 1
                else:
                    clean_val = val.strip("'\"")
                    filters[col] = int(clean_val) if clean_val.isdigit() else clean_val

        return supabase_client.delete(table, filters)

    return None

if __name__ == "__main__":
    test_id = f"test-rem-{uuid.uuid4().hex[:6]}"
    now = datetime.datetime.utcnow().isoformat()
    print("Testing Supabase INSERT...")
    ins = execute_supabase_write(
        "INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
        (test_id, "farmer-1001", "Test Supabase Reminder", "Testing automated dual-write", "Tomorrow 10 AM", now)
    )
    print("Inserted:", ins)
    
    print("Testing Supabase UPDATE...")
    upd = execute_supabase_write(
        "UPDATE reminders SET is_completed = 1 WHERE id = ?",
        (test_id,)
    )
    print("Updated:", upd)
    
    print("Testing Supabase DELETE...")
    d = execute_supabase_write(
        "DELETE FROM reminders WHERE id = ?",
        (test_id,)
    )
    print("Deleted:", d)
