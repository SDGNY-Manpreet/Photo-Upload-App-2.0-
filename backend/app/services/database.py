import pyodbc
import time
from app.config import settings

# ---------------------------------------------------------------------------
# In-memory TTL Cache (10-minute expiration for instant responses)
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 600  # 10 minutes

_shopify_orders_cache = None
_shopify_orders_time = 0

_special_projects_cache = None
_special_projects_time = 0


def get_connection():
    """Create a connection to Azure SQL with the configured credentials."""
    conn_str = (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={settings.db_server};"
        f"DATABASE={settings.db_name};"
        f"UID={settings.db_username};"
        f"PWD={settings.db_password};"
        f"Connection Timeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    conn.setdecoding(pyodbc.SQL_CHAR, encoding="utf-8")
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding="utf-8")
    conn.setencoding(encoding="utf-8")
    return conn


def test_connection() -> tuple[bool, str]:
    """Test the database connection. Returns (ok, message)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True, "Connected"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Shopify
# ---------------------------------------------------------------------------

def get_all_shopify_orders(force_refresh: bool = False) -> list[dict]:
    """Returns all non-null OrderIDs and their CustomerNames, sorted by OrderID (cached 10m)."""
    global _shopify_orders_cache, _shopify_orders_time
    now = time.time()

    if not force_refresh and _shopify_orders_cache is not None and (now - _shopify_orders_time) < CACHE_TTL_SECONDS:
        return _shopify_orders_cache

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT OrderID, CustomerName FROM [dw-sqldb].dbo.ShopifyProjectData "
            "WHERE OrderID IS NOT NULL ORDER BY OrderID"
        )
        rows = [{"order_id": str(row[0]), "customer_name": str(row[1]) if row[1] else ""} for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        _shopify_orders_cache = rows
        _shopify_orders_time = now
        return rows
    except Exception:
        # Fallback to stale cache if DB query fails during wake-up
        if _shopify_orders_cache is not None:
            return _shopify_orders_cache
        return []


# ---------------------------------------------------------------------------
# Special Projects (letter-prefix project IDs)
# ---------------------------------------------------------------------------

def get_all_special_projects(force_refresh: bool = False) -> list[dict]:
    """
    Returns all special projects (ProjectNumber starting with a letter)
    and their ProjectName and Customer, sorted ascending by ProjectNumber (cached 10m).
    """
    global _special_projects_cache, _special_projects_time
    now = time.time()

    if not force_refresh and _special_projects_cache is not None and (now - _special_projects_time) < CACHE_TTL_SECONDS:
        return _special_projects_cache

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT ProjectNumber, ProjectName, Customer FROM [dw-sqldb].dbo.ProcoreProjectData "
            "WHERE ProjectNumber LIKE '[A-Za-z]%' ORDER BY ProjectNumber"
        )
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            p_num = str(row[0]) if row[0] else ""
            if p_num and p_num.strip() and p_num.strip()[0].isalpha():
                result.append({
                    "project_number": p_num,
                    "project_name": str(row[1]) if row[1] else "",
                    "customer": str(row[2]) if row[2] else ""
                })
        
        cursor.close()
        conn.close()

        _special_projects_cache = result
        _special_projects_time = now
        return result
    except Exception:
        if _special_projects_cache is not None:
            return _special_projects_cache
        return []

