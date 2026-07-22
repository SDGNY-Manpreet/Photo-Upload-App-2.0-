import os
import sys
import json
import pyodbc
import requests

DEFAULT_SHOP_URL = "project-signs.myshopify.com"
DEFAULT_CLIENT_ID = "71aa8bca5f1c95800cad5c764cf4847f"

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

def get_shopify_credentials():
    """Retrieve Shopify credentials from Streamlit Secrets or Environment Variables."""
    creds = {
        'shop_url': DEFAULT_SHOP_URL,
        'client_id': DEFAULT_CLIENT_ID,
        'client_secret': ''
    }
    
    if HAS_STREAMLIT:
        try:
            if 'shopify' in st.secrets:
                creds['shop_url'] = st.secrets["shopify"].get("SHOP_URL", creds['shop_url'])
                creds['client_id'] = st.secrets["shopify"].get("CLIENT_ID", creds['client_id'])
                creds['client_secret'] = st.secrets["shopify"].get("SHOPIFY_CLIENT_SECRET", "")
            if not creds['client_secret'] and 'SHOPIFY_CLIENT_SECRET' in st.secrets:
                creds['client_secret'] = st.secrets.get("SHOPIFY_CLIENT_SECRET", "")
        except Exception:
            pass

    creds['shop_url'] = os.getenv('SHOP_URL', creds['shop_url'])
    creds['client_id'] = os.getenv('CLIENT_ID', creds['client_id'])
    creds['client_secret'] = os.getenv('SHOPIFY_CLIENT_SECRET', creds['client_secret'])
    
    return creds

def get_db_credentials():
    """Retrieve DB credentials from Streamlit Secrets or Environment Variables."""
    creds = {
        'server': '',
        'database': '',
        'username': '',
        'password': '',
        'driver': '{ODBC Driver 17 for SQL Server}'
    }
    
    if HAS_STREAMLIT:
        try:
            if 'azure_sql' in st.secrets:
                creds['server'] = st.secrets["azure_sql"].get("AZURE_DB_SERVER", "")
                creds['database'] = st.secrets["azure_sql"].get("AZURE_DB_NAME", "")
                creds['username'] = st.secrets["azure_sql"].get("AZURE_DB_USERNAME", "")
                creds['password'] = st.secrets["azure_sql"].get("AZURE_DB_PASSWORD", "")
                creds['driver'] = st.secrets["azure_sql"].get("AZURE_DB_DRIVER", creds['driver'])
                return creds
            elif 'DB_SERVER' in st.secrets:
                creds['server'] = st.secrets.get("DB_SERVER", "")
                creds['database'] = st.secrets.get("DB_NAME", "")
                creds['username'] = st.secrets.get("DB_USERNAME", "")
                creds['password'] = st.secrets.get("DB_PASSWORD", "")
                creds['driver'] = st.secrets.get("DB_DRIVER", creds['driver'])
                return creds
        except Exception:
            pass

    creds['server'] = os.getenv('AZURE_DB_SERVER', creds['server'])
    creds['database'] = os.getenv('AZURE_DB_NAME', creds['database'])
    creds['username'] = os.getenv('AZURE_DB_USERNAME', creds['username'])
    creds['password'] = os.getenv('AZURE_DB_PASSWORD', creds['password'])
    creds['driver'] = os.getenv('AZURE_DB_DRIVER', creds['driver'])
    
    if os.name != 'nt' and creds['driver'] == '{ODBC Driver 17 for SQL Server}':
        creds['driver'] = 'ODBC Driver 17 for SQL Server'
        
    return creds

def connect_to_db():
    creds = get_db_credentials()
    print(f"DEBUG: Connecting with Server='{creds['server']}', Database='{creds['database']}', User='{creds['username']}', Driver='{creds['driver']}'")
    if not creds['server'] or not creds['password']:
        print("[!] Missing database credentials.")
        return None
        
    try:
        conn_str = f"DRIVER={creds['driver']};SERVER={creds['server']};DATABASE={creds['database']};UID={creds['username']};PWD={creds['password']};Connection Timeout=30;"
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        return None

def get_shopify_access_token(creds):
    print(f"[*] Authenticating with Shopify ({creds['shop_url']})...")
    token_url = f"https://{creds['shop_url']}/admin/oauth/access_token"
    payload = {
        "client_id": creds['client_id'],
        "client_secret": creds['client_secret'],
        "grant_type": "client_credentials",
    }
    try:
        resp = requests.post(token_url, json=payload, timeout=15)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if token:
            print("[+] Successfully authenticated with Shopify.")
            return token
        else:
            print("[!] Failed to get access token from response.")
            return None
    except Exception as e:
        print(f"[!] Authentication Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Details: {e.response.text}")
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
