import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

def update_properties_table():
    app = create_app()
    with app.app_context():
        # Execute raw SQL
        sql = """
        -- Change monthly_rent type
        ALTER TABLE properties 
        ALTER COLUMN monthly_rent TYPE NUMERIC(10,2) 
        USING monthly_rent::numeric(10,2);

        -- Add new columns if they don't exist
        DO $$ 
        BEGIN 
            -- Add registry_number column
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name='properties' AND column_name='registry_number') 
            THEN 
                ALTER TABLE properties ADD COLUMN registry_number VARCHAR(100);
            END IF;

            -- Add area column
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name='properties' AND column_name='area') 
            THEN 
                ALTER TABLE properties ADD COLUMN area FLOAT;
            END IF;

            -- Add contract_term column
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name='properties' AND column_name='contract_term') 
            THEN 
                ALTER TABLE properties ADD COLUMN contract_term INTEGER;
            END IF;

            -- Add currency column
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name='properties' AND column_name='currency') 
            THEN 
                ALTER TABLE properties ADD COLUMN currency VARCHAR(3) DEFAULT 'AZN';
            END IF;
        END $$;
        """
        db.session.execute(sql)
        db.session.commit()
        print("Properties table updated successfully!")

if __name__ == "__main__":
    update_properties_table() 