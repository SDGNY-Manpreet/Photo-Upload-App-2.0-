import os
import sys
import json
import pyodbc
from procore_api import ProcoreAPI

def get_db_credentials():
    """Retrieve DB credentials from Environment Variables."""
    server = os.getenv('AZURE_DB_SERVER', os.getenv('DB_SERVER', ''))
    database = os.getenv('AZURE_DB_NAME', os.getenv('DB_NAME', ''))
    username = os.getenv('AZURE_DB_USERNAME', os.getenv('DB_USERNAME', ''))
    password = os.getenv('AZURE_DB_PASSWORD', os.getenv('DB_PASSWORD', ''))
    driver = os.getenv('AZURE_DB_DRIVER', os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}'))

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
    if not creds['server'] or not creds['password']:
        print("❌ Missing database credentials.")
        print(f"   Server: '{creds['server']}', Database: '{creds['database']}', User: '{creds['username']}'")
        return None
        
    print(f"🔌 Connecting to Azure SQL Server: {creds['server']} | DB: {creds['database']} | User: {creds['username']}...")
    try:
        conn_str = f"DRIVER={creds['driver']};SERVER={creds['server']};DATABASE={creds['database']};UID={creds['username']};PWD={creds['password']};Connection Timeout=30;"
        conn = pyodbc.connect(conn_str)
        print("✅ Connected to Azure SQL successfully!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def get_existing_project_numbers(conn):
    """Fetch existing ProjectNumbers to skip them."""
    cursor = conn.cursor()
    cursor.execute("SELECT ProjectNumber FROM ProcoreProjectData")
    rows = cursor.fetchall()
    cursor.close()
    return {str(row[0]).strip().lower() for row in rows if row[0]}

def safe_truncate(text, max_length=100):
    if not text:
        return None
    return text[:max_length]

def sync_projects():
    print("🚀 Starting Procore Project Data Synchronization...")
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
        
    existing_numbers = get_existing_project_numbers(conn)
    print(f"✅ Found {len(existing_numbers)} existing projects in database.")
    
    api = ProcoreAPI()
    if not api.authenticate():
        print("❌ Failed to authenticate with Procore API.")
        conn.close()
        sys.exit(1)
    
    headers = api.get_headers()
    
    print("📥 Fetching projects from Procore...")
    procore_projects = api.list_projects()
    print(f"✅ Fetched {len(procore_projects)} projects from Procore.")
    
    cursor = conn.cursor()
    added_count = 0
    skipped_count = 0
    
    for p in procore_projects:
        p_num = str(p.get('number', '')).strip()
        
        if not p_num or p_num == "No #" or p_num == "None":
            continue
            
        p_num_lower = p_num.lower()
        if p_num_lower in existing_numbers:
            skipped_count += 1
            continue
            
        p_id = p.get('id')
        p_name = p.get('name')
        print(f"🆕 Found new project: {p_name} ({p_num}). Fetching details...")
        
        url_ext = f"{api.base_url}projects/{p_id}?company_id={api.company_id}&serializer_view=extended"
        res_ext = api.session.get(url_ext, headers=headers)
        p_ext = res_ext.json() if res_ext.status_code == 200 else {}
        
        url_roles = f"{api.base_url}project_roles?project_id={p_id}&company_id={api.company_id}"
        res_roles = api.session.get(url_roles, headers=headers)
        roles_data = res_roles.json() if res_roles.status_code == 200 else []
        
        executives = []
        managers = []
        for r in roles_data:
            role_name = str(r.get('role', '')).lower()
            name = r.get('name', '')
            clean_name = name.split("(")[0].strip() if name else ""
            if not clean_name:
                continue
            if 'executive' in role_name or 'director' in role_name:
                executives.append(clean_name)
            elif 'manager' in role_name or 'pm' in role_name:
                managers.append(clean_name)
                
        url_contracts = f"{api.base_url}prime_contracts?project_id={p_id}"
        res_contracts = api.session.get(url_contracts, headers=headers)
        contracts_data = res_contracts.json() if res_contracts.status_code == 200 else []
        
        customer = None
        for pc in contracts_data:
            vendor = pc.get("vendor") or {}
            v_name = vendor.get("name")
            if v_name:
                customer = v_name
                break
                
        ptype_obj = p_ext.get('project_type')
        street_address = p.get('address') or p_ext.get('address')
        city = p.get('city') or p_ext.get('city')
        state = p.get('state_code') or p_ext.get('state_code')
        zip_code = p.get('zip') or p_ext.get('zip')
        
        project_type = ptype_obj.get('name') if ptype_obj else None
        project_exec = ", ".join(set(executives)) if executives else None
        project_mgr = ", ".join(set(managers)) if managers else None
        
        insert_query = """
            INSERT INTO ProcoreProjectData 
            (ProjectNumber, ProjectName, ProjectType, ProjectExecutive, ProjectManager, 
             Customer, StreetAddress, City, State, Zip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            safe_truncate(p_num, 50),
            safe_truncate(p_name, 255),
            safe_truncate(project_type, 100),
            safe_truncate(project_exec, 100),
            safe_truncate(project_mgr, 100),
            safe_truncate(customer, 255),
            safe_truncate(street_address, 255),
            safe_truncate(city, 100),
            safe_truncate(state, 100),
            safe_truncate(zip_code, 20)
        )
        
        try:
            cursor.execute(insert_query, params)
            conn.commit()
            added_count += 1
            print(f"   ✅ Added to database successfully.")
            existing_numbers.add(p_num_lower)
        except Exception as e:
            print(f"   ❌ Error inserting project {p_num}: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print(f"\n🎉 Synchronization Complete!")
    print(f"   - Skipped existing: {skipped_count}")
    print(f"   - Newly Added: {added_count}")

if __name__ == "__main__":
    sync_projects()
