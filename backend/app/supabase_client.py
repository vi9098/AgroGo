"""
AgriGo Supabase Cloud Database Client
Provides high-performance, pooled REST connectivity to Supabase PostgreSQL.
Supports direct reads, dual-writes, upserts, and sync to local SQLite cache.
"""
import logging
import os
from typing import Dict, List, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import settings

logger = logging.getLogger("agrigo.supabase")

TABLE_SCHEMAS = {
    'users': {'id', 'phone', 'name', 'password_hash', 'preferred_language', 'state', 'district', 'village', 'consent_json', 'created_at', 'status', 'role'},
    'crops': {'id', 'farm_id', 'farmer_id', 'crop_name', 'variety', 'stage', 'health_status', 'sowing_date', 'area_acres', 'created_at'},
    'farms': {'id', 'farmer_id', 'name', 'total_area_acres', 'soil_type', 'irrigation_type', 'created_at'},
    'crop_cycles': {'id', 'field_id', 'farmer_id', 'crop_name', 'variety', 'sowing_date', 'expected_harvest_date', 'area_acres', 'irrigation_method', 'soil_type', 'current_stage', 'health_status', 'created_at'},
    'reminders': {'id', 'farmer_id', 'title', 'description', 'due_date', 'is_completed', 'created_at', 'reminder_type', 'crop_id', 'priority'},
    'sessions': {'id', 'user_id', 'role', 'ip_address', 'user_agent', 'created_at', 'last_accessed_at', 'expires_at'},
    'otps': {'id', 'phone', 'code', 'expires_at', 'is_used', 'created_at', 'logid'},
    'admin_users': {'id', 'email', 'password_hash', 'full_name', 'role', 'is_2fa_enabled', 'totp_secret', 'created_at'},
    'knowledge_docs': {'id', 'title', 'category', 'crop', 'content', 'source', 'verified', 'created_at'},
    'knowledge_sources': {'id', 'name', 'url', 'organization', 'country', 'languages_json', 'source_type', 'license_name', 'license_url', 'terms_url', 'allows_automated_collection', 'allows_text_reuse', 'allows_model_training', 'requires_attribution', 'robots_checked', 'verified_at', 'status', 'created_at'},
    'knowledge_chunks': {'id', 'document_id', 'text', 'crop', 'topic', 'region', 'language', 'source', 'source_url', 'license', 'confidence', 'created_at'},
    'district_crop_benchmarks': {'state_name', 'district_name', 'crop_name', 'crop_type', 'season', 'avg_yield', 'max_yield', 'min_yield', 'avg_production', 'avg_area', 'record_count'},
    'audit_logs': {'id', 'actor_id', 'actor_type', 'action', 'resource_type', 'resource_id', 'ip_hash', 'details_json', 'timestamp'}
}

class SupabaseClient:
    def __init__(self):
        self.url = (settings.SUPABASE_URL or os.getenv("SUPABASE_URL", "")).rstrip("/")
        # Determine active Supabase key (prioritizing the verified working publishable key)
        self.api_key = (
            settings.SUPABASE_KEY or 
            os.getenv("SUPABASE_KEY") or 
            settings.SUPABASE_SERVICE_ROLE_KEY or 
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
            ""
        )
        self.secret_key = self.api_key
        self.publishable_key = self.api_key
        
        # Configure robust connection pooling with retries
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(pool_connections=15, pool_maxsize=30, max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Default headers for Supabase PostgREST
        self._headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self._is_available: Optional[bool] = None

    def is_configured(self) -> bool:
        return bool(self.url and self.api_key)

    def is_available(self) -> bool:
        if self._is_available is None:
            return self.check_health()
        return self._is_available

    def check_health(self) -> bool:
        """Verifies live connectivity to Supabase PostgREST endpoint."""
        if not self.is_configured():
            self._is_available = False
            return False
        try:
            # Query a known table with limit=1 to verify PostgREST table read access
            r = self.session.get(f"{self.url}/rest/v1/crops", headers=self._headers, params={"limit": "1"}, timeout=5.0)
            if r.status_code in (200, 206):
                self._is_available = True
                logger.info(f"[Supabase] Live PostgREST connection verified on {self.url} (HTTP 200)")
                return True
            # Alternative: verify GoTrue auth health
            r_auth = self.session.get(f"{self.url}/auth/v1/health", headers=self._headers, timeout=5.0)
            if r_auth.status_code == 200:
                self._is_available = True
                logger.info(f"[Supabase] Live GoTrue connection verified on {self.url} (HTTP 200)")
                return True
            logger.warning(f"[Supabase Health] Check returned HTTP {r.status_code}: {r.text[:200]}")
            self._is_available = False
            return False
        except Exception as e:
            logger.error(f"[Supabase Health Check] Connection error: {e}")
            self._is_available = False
            return False

    def select(
        self,
        table: str,
        select: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        timeout: float = 6.0
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Executes a PostgREST SELECT query against Supabase.
        Returns None if Supabase is unavailable or returns an error, triggering SQLite fallback.
        """
        if not self.is_available():
            return None

        params: Dict[str, str] = {"select": select}
        if filters:
            for col, val in filters.items():
                if val is None:
                    params[col] = "is.null"
                elif isinstance(val, bool):
                    params[col] = f"eq.{'true' if val else 'false'}"
                elif isinstance(val, str) and (val.startswith("eq.") or val.startswith("ilike.") or val.startswith("gte.") or val.startswith("lte.") or val.startswith("in.")):
                    params[col] = val
                else:
                    params[col] = f"eq.{val}"
                    
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)

        url = f"{self.url}/rest/v1/{table}"
        try:
            r = self.session.get(url, headers=self._headers, params=params, timeout=timeout)
            if r.status_code in (200, 206):
                return r.json() if isinstance(r.json(), list) else []
            if r.status_code in (401, 403):
                self._is_available = False
                logger.info(f"[Supabase] {table} authentication rejected (HTTP {r.status_code}). Marked offline; continuing with SQLite.")
                return None
            logger.warning(f"[Supabase Select] {table} returned HTTP {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[Supabase Select Error] {table}: {e}")
            return None

    def select_one(
        self,
        table: str,
        select: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        rows = self.select(table, select=select, filters=filters, order=order, limit=1, timeout=timeout)
        if rows is None:
            return None
        return rows[0] if rows else None

    def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        upsert: bool = False,
        timeout: float = 6.0
    ) -> List[Dict[str, Any]]:
        """Inserts or upserts records into Supabase table with automatic column sanitization."""
        if not self.is_available():
            self.check_health()

        # Sanitize data against known Supabase schema columns
        if table in TABLE_SCHEMAS:
            allowed = TABLE_SCHEMAS[table]
            def _clean(item: Dict[str, Any]) -> Dict[str, Any]:
                d = dict(item)
                if table == "reminders" and "description" in d:
                    extras = []
                    if "acreage" in d and d["acreage"]:
                        extras.append(f"क्षेत्रफल: {d['acreage']} एकड़")
                    if "stage_name" in d and d["stage_name"]:
                        extras.append(f"चरण: {d['stage_name']}")
                    if "dosage_info" in d and d["dosage_info"]:
                        extras.append(f"मात्रा: {d['dosage_info']}")
                    if extras:
                        d["description"] = f"{d['description']} ({', '.join(extras)})"
                return {k: v for k, v in d.items() if k in allowed}

            if isinstance(data, dict):
                data = _clean(data)
            elif isinstance(data, list):
                data = [_clean(item) for item in data]

        url = f"{self.url}/rest/v1/{table}"
        headers = dict(self._headers)
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        else:
            headers["Prefer"] = "return=representation"

        try:
            r = self.session.post(url, headers=headers, json=data, timeout=timeout)
            if r.status_code in (200, 201):
                return r.json() if isinstance(r.json(), list) else [data]
            logger.warning(f"[Supabase Insert] {table} returned HTTP {r.status_code}: {r.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"[Supabase Insert Error] {table}: {e}")
            return []

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        timeout: float = 6.0
    ) -> List[Dict[str, Any]]:
        """Updates records matching filters in Supabase table."""
        if not self.is_available():
            self.check_health()

        if table in TABLE_SCHEMAS:
            allowed = TABLE_SCHEMAS[table]
            data = {k: v for k, v in data.items() if k in allowed}
            filters = {k: v for k, v in filters.items() if k in allowed}

        params: Dict[str, str] = {}
        for col, val in filters.items():
            if val is None:
                params[col] = "is.null"
            elif isinstance(val, str) and (val.startswith("eq.") or val.startswith("in.")):
                params[col] = val
            else:
                params[col] = f"eq.{val}"

        url = f"{self.url}/rest/v1/{table}"
        headers = dict(self._headers)
        headers["Prefer"] = "return=representation"

        try:
            r = self.session.patch(url, headers=headers, params=params, json=data, timeout=timeout)
            if r.status_code in (200, 204):
                try:
                    return r.json() if isinstance(r.json(), list) else []
                except Exception:
                    return [data]
            logger.warning(f"[Supabase Update] {table} returned HTTP {r.status_code}: {r.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"[Supabase Update Error] {table}: {e}")
            return []

    def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        timeout: float = 6.0
    ) -> bool:
        """Deletes records matching filters in Supabase table."""
        if not self.is_available():
            return False

        params: Dict[str, str] = {}
        for col, val in filters.items():
            params[col] = f"eq.{val}"

        url = f"{self.url}/rest/v1/{table}"
        try:
            r = self.session.delete(url, headers=self._headers, params=params, timeout=timeout)
            if r.status_code in (401, 403):
                self._is_available = False
                return False
            return r.status_code in (200, 204)
        except Exception as e:
            logger.error(f"[Supabase Delete Error] {table}: {e}")
            return False

    def count(self, table: str, timeout: float = 5.0) -> int:
        """Returns exact count of rows in Supabase table."""
        if not self.is_available():
            return 0

        url = f"{self.url}/rest/v1/{table}?select=id"
        headers = {**self._headers, "Range": "0-0", "Prefer": "count=exact"}
        try:
            r = self.session.get(url, headers=headers, timeout=timeout)
            if r.status_code in (401, 403):
                self._is_available = False
                return 0
            content_range = r.headers.get("Content-Range", "")
            if "/" in content_range:
                return int(content_range.split("/")[1])
            return len(r.json()) if isinstance(r.json(), list) else 0
        except Exception:
            return 0

    def get_all_table_counts(self) -> Dict[str, int]:
        """Returns row counts for all core tables in Supabase."""
        core_tables = [
            "crop_production_historical", "district_crop_benchmarks", "live_mandi_prices",
            "users", "crops", "farms", "reminders", "crop_cycles", "admin_users",
            "knowledge_docs", "knowledge_sources", "knowledge_chunks", "sessions", "otps"
        ]
        counts = {}
        for t in core_tables:
            counts[t] = self.count(t)
        return counts

# Singleton instance for app-wide use
supabase_client = SupabaseClient()
