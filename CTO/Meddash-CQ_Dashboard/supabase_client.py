"""
Singleton Supabase REST client.
All widgets use sb.query() for read-only counts.
v1.1 — Fixed column name awareness. Some tables don't have 'id'.
"""

import requests
from config import SUPABASE_URL, SUPABASE_KEY, SB_TABLE_SELECT_COLUMNS

class SupabaseClient:
    """Lightweight REST client — no heavy SDK needed for read-only queries."""

    def __init__(self):
        self.url = SUPABASE_URL.rstrip("/")
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self._healthy = None

    @property
    def is_configured(self):
        return bool(self.url and self.url != "https://YOUR_PROJECT.supabase.co" and SUPABASE_KEY and len(SUPABASE_KEY) > 20)

    def health(self):
        """Ping Supabase REST API."""
        try:
            r = requests.get(f"{self.url}/rest/v1/kols?select=id&limit=1", headers=self.headers, timeout=10)
            self._healthy = r.status_code in (200, 206)
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def count(self, table):
        """Get row count for a table via GET with Prefer: count=exact."""
        try:
            # Use the correct select column for tables without 'id'
            select_col = SB_TABLE_SELECT_COLUMNS.get(table, "id")
            r = requests.get(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "count=exact"},
                params={"select": select_col, "limit": 1},
                timeout=10,
            )
            if r.status_code in (200, 206):
                content_range = r.headers.get("content-range", "")
                if "/" in content_range:
                    return int(content_range.split("/")[1])
            return 0
        except Exception:
            return -1  # error sentinel

    def count_with_filter(self, table, column, operator, value):
        """Count rows matching a filter."""
        try:
            select_col = SB_TABLE_SELECT_COLUMNS.get(table, "id")
            params = {"select": select_col, "limit": 1}
            if operator == "not.is":
                params[column] = "not.is.null" if value is None else f"not.eq.{value}"
            elif operator == "eq":
                params[column] = f"eq.{value}"
            elif operator == "neq":
                params[column] = f"neq.{value}"
            else:
                params[column] = f"{operator}.{value}"

            r = requests.get(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "count=exact"},
                params=params,
                timeout=15,
            )
            if r.status_code in (200, 206):
                content_range = r.headers.get("content-range", "")
                if "/" in content_range:
                    return int(content_range.split("/")[1])
            return 0
        except Exception:
            return -1

    def select(self, table, columns="*", filters=None, limit=1000):
        """Select rows from a table."""
        try:
            params = {"select": columns, "limit": limit}
            if filters:
                for k, v in filters.items():
                    params[k] = f"eq.{v}"
            r = requests.get(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params=params,
                timeout=15,
            )
            if r.status_code in (200, 206):
                return r.json()
            return []
        except Exception:
            return []

    def get_table_row_counts(self, tables):
        """Bulk count for multiple tables. Returns dict {table: count}."""
        results = {}
        for table in tables:
            results[table] = self.count(table)
        return results


# Singleton
sb = SupabaseClient()