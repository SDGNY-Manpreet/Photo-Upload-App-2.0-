import pyodbc
from app.config import settings


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

def get_all_shopify_orders() -> list[dict]:
    """Returns all non-null OrderIDs and their CustomerNames, sorted by OrderID."""
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
        return rows
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Special Projects (letter-prefix project IDs)
# ---------------------------------------------------------------------------

def get_all_special_projects() -> list[dict]:
    """
    Returns all special projects (ProjectNumber starting with a letter)
    and their ProjectName and Customer, sorted ascending by ProjectNumber.
    """
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
            # Fallback filter in Python in case LIKE '[A-Za-z]%' returned weird things
            p_num = str(row[0]) if row[0] else ""
            if p_num and p_num.strip() and p_num.strip()[0].isalpha():
                result.append({
                    "project_number": p_num,
                    "project_name": str(row[1]) if row[1] else "",
                    "customer": str(row[2]) if row[2] else ""
                })
        
        cursor.close()
        conn.close()
        return result
    except Exception:
        return []
