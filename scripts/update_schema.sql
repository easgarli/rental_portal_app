-- First, create the contract_status enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contract_status') THEN
        CREATE TYPE contract_status AS ENUM ('draft', 'pending_signatures', 'active', 'completed', 'terminated');
    END IF;
END$$;

-- Add the contract_status column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'rental_applications' 
        AND column_name = 'contract_status'
    ) THEN
        ALTER TABLE rental_applications 
        ADD COLUMN contract_status contract_status NOT NULL DEFAULT 'draft';
    END IF;
END$$;

-- Add the application_id column to contracts table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'contracts' 
        AND column_name = 'application_id'
    ) THEN
        ALTER TABLE contracts 
        ADD COLUMN application_id UUID REFERENCES rental_applications(id) ON DELETE CASCADE;
    END IF;
END$$;

-- Add contract-related columns to rental_applications table
DO $$
BEGIN
    -- Add contract_content column
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'rental_applications' 
        AND column_name = 'contract_content'
    ) THEN
        ALTER TABLE rental_applications 
        ADD COLUMN contract_content TEXT;
    END IF;

    -- Add contract_generated_at column
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'rental_applications' 
        AND column_name = 'contract_generated_at'
    ) THEN
        ALTER TABLE rental_applications 
        ADD COLUMN contract_generated_at TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Add tenant_signature column
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'rental_applications' 
        AND column_name = 'tenant_signature'
    ) THEN
        ALTER TABLE rental_applications 
        ADD COLUMN tenant_signature TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Add landlord_signature column
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'rental_applications' 
        AND column_name = 'landlord_signature'
    ) THEN
        ALTER TABLE rental_applications 
        ADD COLUMN landlord_signature TIMESTAMP WITH TIME ZONE;
    END IF;
END$$;

-- Add contract_id column to ratings table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'ratings' 
        AND column_name = 'contract_id'
    ) THEN
        ALTER TABLE ratings 
        ADD COLUMN contract_id UUID REFERENCES rental_applications(id) ON DELETE CASCADE;
    END IF;
END$$; 