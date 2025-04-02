import psycopg2
import psycopg2.extras
import os
from flask import current_app
import logging
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
from datetime import datetime
import threading
import json
from contextlib import contextmanager
# import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from typing import Dict, List, Optional, Union
from models import db

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# print("\nDatabase connection environment:")
# print("POSTGRES_USER:", os.getenv('POSTGRES_USER'))
# print("From direct environ:", os.environ.get('POSTGRES_USER'))

class DatabaseConfig:
    """Database configuration container"""
    def __init__(self, 
                 host: str = os.environ.get('POSTGRES_HOST', 'localhost'),
                 port: str = os.environ.get('POSTGRES_PORT', '5432'),
                 user: str = os.environ.get('POSTGRES_USER', 'postgres'),
                 password: str = os.environ.get('POSTGRES_PASSWORD', ''),
                 default_db: str = 'postgres',
                 min_connections: int = 1,
                 max_connections: int = 10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.default_db = default_db
        self.min_connections = min_connections
        self.max_connections = max_connections

    def get_connection_dict(self, database: Optional[str] = None) -> dict:
        """Get database connection parameters"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': database or self.default_db
        }

    def get_sqlalchemy_url(self, database: str) -> str:
        """Get SQLAlchemy connection URL"""
        return (f'postgresql://{self.user}:{self.password}@'
                f'{self.host}:{self.port}/{database}')

class DatabasePool:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pools = {}
        self._lock = threading.Lock()

    def get_pool(self, db_name: str) -> SimpleConnectionPool:
        with self._lock:
            if db_name not in self.pools:
                db_config = self.config.get_connection_dict(db_name)
                self.pools[db_name] = SimpleConnectionPool(
                    minconn=self.config.min_connections,
                    maxconn=self.config.max_connections,
                    **db_config
                )
            return self.pools[db_name]

    def close_all_pools(self):
        with self._lock:
            # Create a list of pools before closing them
            pools_to_close = list(self.pools.values())
            for pool in pools_to_close:
                if pool:
                    pool.closeall()
            self.pools.clear()

    def return_connection(self, conn, db_name):
        with self._lock:
            if db_name in self.pools:
                try:
                    self.pools[db_name].putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection: {str(e)}")
                    try:
                        conn.close()
                    except:
                        pass

class DatabaseConnection:
    def __init__(self, db_name, dict_cursor=False):
        self.db_name = db_name
        self.conn = None
        self.cur = None
        self.dict_cursor = dict_cursor
        self.rules = self._load_cursor_rules()

    def _load_cursor_rules(self):
        try:
            with open('.cursorrules', 'r') as f:
                rules = json.load(f)
                return rules.get(self.db_name, {})
        except FileNotFoundError:
            return {}

    def _format_value(self, value, type_name):
        if value is None:
            return None
        if type_name == 'timestamp' and value:
            try:
                return datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return None
        elif type_name == 'numeric' and value:
            try:
                return float(value) if value != '' else None
            except ValueError:
                return None
        return value

    def format_row(self, row, columns, table_name):
        """Format row data with column names and type casting"""
        formatted = {}
        table_rules = self.rules.get(table_name, {})
        
        for i, col in enumerate(columns):
            type_name = table_rules.get(col, 'text')
            formatted[col] = self._format_value(row[i], type_name)
            
        return formatted

    def __enter__(self):
        try:
            if self.conn is None:
                self.conn = get_db_connection(self.db_name)
            if self.cur is None:
                if self.dict_cursor:
                    self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                else:
                    self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            return self.cur
        except Exception as e:
            if self.conn:
                try:
                    self.conn.rollback()
                except:
                    pass
            raise Exception(f"Error getting database connection: {str(e)}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                if self.conn and not self.conn.closed:
                    self.conn.rollback()
            else:
                if self.conn and not self.conn.closed:
                    self.conn.commit()
            
            if self.cur and not self.cur.closed:
                self.cur.close()
            if self.conn and not self.conn.closed:
                return_db_connection(self.conn, self.db_name)
        except Exception as e:
            current_app.logger.error(f"Error in __exit__: {str(e)}")
            if exc_type:
                raise exc_type(exc_val)

class DatabaseManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config

    def get_project_root(self) -> Path:
        """Get the project root directory"""
        return Path(__file__).parent.parent

    def create_database(self, db_name: str) -> None:
        """Create a single database"""
        try:
            conn = psycopg2.connect(**self.config.get_connection_dict())
            conn.autocommit = True
            cur = conn.cursor()
            
            cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
            cur.execute(f"CREATE DATABASE {db_name}")
            
            logger.info(f"Database {db_name} created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating database {db_name}: {str(e)}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def import_csv_to_table(self, 
                           csv_path: Union[str, Path],
                           database: str,
                           table_name: str,
                           if_exists: str = 'replace',
                           column_map: Optional[Dict[str, str]] = None,
                           **pandas_kwargs) -> None:
        """
        Import CSV file to specified database table
        
        Args:
            csv_path: Path to CSV file
            database: Target database name
            table_name: Target table name
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            column_map: Dictionary mapping CSV column names to database column names
            **pandas_kwargs: Additional arguments passed to pd.read_csv()
        """
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found at: {csv_path}")

            engine = create_engine(self.config.get_sqlalchemy_url(database))
            
            logger.info(f"Loading data from {csv_path}...")
            
            df = pd.read_csv(csv_path, **pandas_kwargs)
            
            # Rename columns if column_map is provided
            if column_map:
                df = df.rename(columns=column_map)
            
            # Ensure all column names are lowercase
            df.columns = df.columns.str.lower()
            
            logger.info(f"Importing data to {database}.{table_name}...")
            df.to_sql(table_name, engine, if_exists=if_exists, index=False)
            logger.info("Data imported successfully!")

        except Exception as e:
            logger.error(f"Error importing data: {str(e)}")
            raise
        finally:
            if 'engine' in locals():
                engine.dispose()

    def batch_import_csvs(self, 
                         import_config: Dict[str, Dict[str, str]]) -> None:
        """
        Batch import multiple CSV files to different tables
        
        Args:
            import_config: Dictionary mapping database names to table configs
            Example:
            {
                'database1': {
                    'table1': 'path/to/csv1.csv',
                    'table2': 'path/to/csv2.csv'
                },
                'database2': {
                    'table3': 'path/to/csv3.csv'
                }
            }
        """
        for database, tables in import_config.items():
            for table_name, csv_path in tables.items():
                self.import_csv_to_table(csv_path, database, table_name)

# Example usage:
# config = DatabaseConfig(
#     host='localhost',
#     port='5432',
#     user='postgres',
#     password='your_password',
#     min_connections=1,
#     max_connections=20
# )
# db_manager = DatabaseManager(config)
# db_pool = DatabasePool(config)

# Initialize global instances with default config
default_config = DatabaseConfig()
db_pool = DatabasePool(default_config)
db_manager = DatabaseManager(default_config)

# Helper functions remain the same but use db_pool instance
def get_db_connection(db_name: str):
    return db_pool.get_pool(db_name).getconn()

def return_db_connection(conn, db_name: str):
    db_pool.return_connection(conn, db_name)

def format_row(row, columns, table_name):
    """Format row data with column names and type casting"""
    formatted = {}
    table_rules = db_pool.rules.get(table_name, {})
    
    for i, col in enumerate(columns):
        type_name = table_rules.get(col, 'text')
        formatted[col] = _format_value(row[i], type_name)
        
    return formatted

def _format_value(value, type_name):
    if value is None:
        return None
    if type_name == 'timestamp' and value:
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return None
    elif type_name == 'numeric' and value:
        try:
            return float(value) if value != '' else None
        except ValueError:
            return None
    return value

def reset_db():
    """Drop all tables and recreate them"""
    target_db = os.getenv('POSTGRES_DB')
    print(f"WARNING: This will reset all tables in database '{target_db}'")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Database reset cancelled.")
        return
        
    print(f"Resetting database '{target_db}'...")
    db.drop_all()
    db.create_all()
    print("Database reset completed successfully!")