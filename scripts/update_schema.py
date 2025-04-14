import os
import psycopg2
from dotenv import load_dotenv

def update_schema():
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters
    db_params = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT')
    }
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Read and execute the SQL file
        with open('scripts/update_schema.sql', 'r') as f:
            sql_script = f.read()
            cur.execute(sql_script)
        
        print("Schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    update_schema() 