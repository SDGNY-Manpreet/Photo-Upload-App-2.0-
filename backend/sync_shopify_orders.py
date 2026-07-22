import os
import sys
import json
import pyodbc
import requests

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_SHOP_URL = "project-signs.myshopify.com"
DEFAULT_CLIENT_ID = "71aa8bca5f1c95800cad5c764cf4847f"

def load_dotenv_file():
    """Load backend/.env or .env file locally into os.environ if present."""
    env_paths = [
        os.path.join(os.getcwd(), "backend", ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            key = k.strip()
                            val = v.strip()
                            if key not in os.environ:
                                os.environ[key] = val
            except Exception:
                pass

def get_shopify_credentials():
    """Retrieve Shopify credentials from Environment Variables."""
    load_dotenv_file()
    return {
        'shop_url': os.getenv('SHOP_URL', DEFAULT_SHOP_URL),
        'client_id': os.getenv('CLIENT_ID', DEFAULT_CLIENT_ID),
        'client_secret': os.getenv('SHOPIFY_CLIENT_SECRET', '')
    }

def get_db_credentials():
    """Retrieve DB credentials from Environment Variables."""
    load_dotenv_file()
    server = (os.getenv('AZURE_DB_SERVER') or os.getenv('DB_SERVER') or '').strip()
    database = (os.getenv('AZURE_DB_NAME') or os.getenv('DB_NAME') or '').strip()
    username = (os.getenv('AZURE_DB_USERNAME') or os.getenv('DB_USERNAME') or '').strip()
    password = (os.getenv('AZURE_DB_PASSWORD') or os.getenv('DB_PASSWORD') or '').strip()
    driver = (os.getenv('AZURE_DB_DRIVER') or os.getenv('DB_DRIVER') or '{ODBC Driver 17 for SQL Server}').strip()

    # Clean server string
    server = server.replace('tcp:', '').split(',')[0].strip()
    if server and '.' not in server:
        server = f"{server}.database.windows.net"

    if driver and not driver.startswith('{'):
        driver = f"{{{driver}}}"

    return {
        'server': server,
        'database': database,
        'username': username,
        'password': password,
        'driver': driver
    }

def connect_to_db():
    creds = get_db_credentials()
    srv = creds['server']
    db = creds['database']
    usr = creds['username']
    drv = creds['driver']
    
    print(f"DEBUG: Connecting to Server='{srv}', DB='{db}', User='{usr}', Driver='{drv}'")
    
    if not srv or not creds['password']:
        print("[!] Missing database credentials.")
        return None
        
    try:
        conn_str = f"DRIVER={drv};SERVER={srv};DATABASE={db};UID={usr};PWD={{{creds['password']}}};Connection Timeout=30;"
        conn = pyodbc.connect(conn_str)
        print("[+] Connected to database successfully!")
        return conn
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        return None

def get_shopify_access_token(creds):
    token = creds.get('client_secret', '').strip()
    if token:
        print("[+] Using provided Shopify credential directly as the Access Token.")
        return token
    else:
        print("[!] Shopify credential is missing.")
        return None

def fetch_recent_orders(shop_url, token):
    print("[*] Fetching orders from Shopify...")
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }
    url = f"https://{shop_url}/admin/api/2024-01/orders.json?status=any&limit=250"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        orders = resp.json().get("orders", [])
        print(f"[+] Fetched {len(orders)} orders.")
        return orders
    except Exception as e:
        print(f"[!] Error fetching orders: {e}")
        return []

def get_existing_order_ids(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT OrderID FROM ShopifyProjectData")
    rows = cursor.fetchall()
    cursor.close()
    return {str(row[0]).strip().lower() for row in rows if row[0]}

def safe_truncate(text, max_length=100):
    if not text:
        return None
    return text[:max_length]

def sync_shopify_orders():
    print("[*] Starting Shopify Orders Synchronization...")
    
    shopify_creds = get_shopify_credentials()
    if not shopify_creds['client_secret']:
        print("[!] Shopify Client Secret is missing!")
        sys.exit(1)
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
        
    existing_orders = get_existing_order_ids(conn)
    print(f"[+] Found {len(existing_orders)} existing orders in database.")
    
    token = get_shopify_access_token(shopify_creds)
    if not token:
        conn.close()
        sys.exit(1)
        
    orders = fetch_recent_orders(shopify_creds['shop_url'], token)
    
    cursor = conn.cursor()
    added_count = 0
    skipped_count = 0
    
    for order in orders:
        order_name = str(order.get('name', '')).strip()
        
        if not order_name:
            continue
            
        order_name_lower = order_name.lower()
        if order_name_lower in existing_orders:
            skipped_count += 1
            continue
            
        print(f"[*] Found new order: {order_name}. Extracting details...")
        
        customer = order.get('customer') or {}
        shipping = order.get('shipping_address') or {}
        billing = order.get('billing_address') or {}
        
        customer_name = shipping.get('company') or billing.get('company')
        if not customer_name:
            first = customer.get('first_name', '')
            last = customer.get('last_name', '')
            customer_name = f"{first} {last}".strip()
            
        customer_email = customer.get('email')
        
        insert_query = """
            INSERT INTO ShopifyProjectData (OrderID, CustomerName, CustomerEmail)
            VALUES (?, ?, ?)
        """
        
        params = (
            safe_truncate(order_name, 50),
            safe_truncate(customer_name, 255),
            safe_truncate(customer_email, 500)
        )
        
        try:
            cursor.execute(insert_query, params)
            conn.commit()
            added_count += 1
            print(f"    [+] Added to database successfully.")
            existing_orders.add(order_name_lower)
        except Exception as e:
            print(f"    [!] Error inserting order {order_name}: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print(f"\n[*] Synchronization Complete!")
    print(f"    - Skipped existing: {skipped_count}")
    print(f"    - Newly Added: {added_count}")

if __name__ == "__main__":
    sync_shopify_orders()
