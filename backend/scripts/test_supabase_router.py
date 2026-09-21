import re
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.supabase_client import supabase_client

def parse_and_query_supabase(query: str, params: tuple = ()):
    q = query.strip()
    q_upper = q.upper()
    
    if not q_upper.startswith("SELECT"):
        return None
        
    m = re.search(r"FROM\s+([a-zA-Z0-9_]+)", q, re.IGNORECASE)
    if not m:
        return None
    table = m.group(1).lower()
    
    known_tables = {
        "users", "crops", "farms", "crop_cycles", "reminders", "sessions", "otps",
        "admin_users", "knowledge_docs", "knowledge_sources", "knowledge_chunks",
        "live_mandi_prices", "crop_production_historical", "district_crop_benchmarks",
        "market_data", "farmer_observations", "soil_data", "fields", "audit_logs"
    }
    if table not in known_tables:
        return None
        
    if "GROUP BY" in q_upper or "JOIN" in q_upper or "HAVING" in q_upper:
        return None

    # Handle COUNT(*) queries
    if re.search(r"SELECT\s+COUNT\(\*\)\s+AS\s+([a-zA-Z0-9_]+)", q, re.IGNORECASE):
        # We can fetch count directly
        cnt_match = re.search(r"AS\s+([a-zA-Z0-9_]+)", q, re.IGNORECASE)
        alias = cnt_match.group(1) if cnt_match else "count"
        cnt = supabase_client.count(table)
        return [{alias: cnt}]

    # Parse ORDER BY
    order_val = None
    order_m = re.search(r"ORDER\s+BY\s+([^LIMIT]+)", q, re.IGNORECASE)
    if order_m:
        raw_order = order_m.group(1).strip()
        parts = []
        for p in raw_order.split(","):
            p = p.strip()
            if not p:
                continue
            tokens = p.split()
            col = tokens[0]
            direction = tokens[1].lower() if len(tokens) > 1 else "asc"
            parts.append(f"{col}.{direction}")
        order_val = ",".join(parts)

    # Parse LIMIT
    limit_val = None
    offset_val = None
    limit_m = re.search(r"LIMIT\s+(\d+|\?)", q, re.IGNORECASE)
    if limit_m:
        lim_str = limit_m.group(1)
        if lim_str == "?":
            # Find index of limit in params
            limit_val = params[-1]
        else:
            limit_val = int(lim_str)

    # Parse WHERE clauses
    filters = {}
    where_m = re.search(r"WHERE\s+(.*?)(ORDER\s+BY|LIMIT|$)", q, re.IGNORECASE | re.DOTALL)
    if where_m:
        where_clause = where_m.group(1).strip()
        
        # Handle "phone = ? OR id = ?"
        if " OR " in where_clause.upper():
            col_matches = re.findall(r"([a-zA-Z0-9_]+)\s*=\s*\?", where_clause)
            if len(col_matches) == 2 and len(params) >= 2:
                r1 = supabase_client.select(table, filters={col_matches[0]: params[0]}, limit=1)
                if r1:
                    return r1
                return supabase_client.select(table, filters={col_matches[1]: params[1]}, limit=1)
        
        # Handle "col1 = ? AND col2 = ?"
        conds = [c.strip() for c in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)]
        param_idx = 0
        for cond in conds:
            eq_m = re.match(r"([a-zA-Z0-9_]+)\s*=\s*\?", cond)
            if eq_m and param_idx < len(params):
                filters[eq_m.group(1)] = params[param_idx]
                param_idx += 1
            elif "is_used = 0" in cond.lower():
                filters["is_used"] = 0
            elif "is_completed = 0" in cond.lower():
                filters["is_completed"] = 0
            elif "is_completed = 1" in cond.lower():
                filters["is_completed"] = 1

    return supabase_client.select(
        table=table,
        filters=filters if filters else None,
        order=order_val,
        limit=limit_val,
        offset=offset_val
    )

if __name__ == "__main__":
    print("Testing Supabase Query Router:")
    # 1. Select crops by farmer_id
    res1 = parse_and_query_supabase("SELECT * FROM crops WHERE farmer_id = ?", ("farmer-1001",))
    print("1. Crops for farmer-1001:", len(res1) if res1 else "None", [c.get("crop_name") for c in (res1 or [])])
    
    # 2. Select user by phone or id
    res2 = parse_and_query_supabase("SELECT * FROM users WHERE phone = ? OR id = ?", ("9876543210", "9876543210"))
    print("2. User by phone/id:", res2[0].get("name") if res2 else "None")
    
    # 3. Select reminders ordered
    res3 = parse_and_query_supabase("SELECT * FROM reminders WHERE farmer_id = ? ORDER BY is_completed ASC, created_at DESC", ("farmer-1001",))
    print("3. Reminders for farmer-1001:", len(res3) if res3 else "None", [r.get("title") for r in (res3 or [])])
    
    # 4. Count users
    res4 = parse_and_query_supabase("SELECT COUNT(*) as count FROM users")
    print("4. Users count:", res4)
