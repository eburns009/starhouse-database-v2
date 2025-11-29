-- Migration: Add business_name column to contacts table
-- Phase: 1 - Contact Foundation
-- Task: 1.1 Edit Contact Function
-- Date: 2025-11-29
--
-- This migration adds a generic business_name column to the contacts table
-- for manual entry of business/organization names separate from PayPal-sourced data.

-- Add business_name column if it doesn't exist
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS business_name TEXT;

-- Add comment for documentation
COMMENT ON COLUMN contacts.business_name IS 'Business or organization name (manually entered, separate from paypal_business_name)';

-- Verify the column was added
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'contacts' AND column_name = 'business_name'
  ) THEN
    RAISE NOTICE 'SUCCESS: business_name column exists in contacts table';
  ELSE
    RAISE EXCEPTION 'FAILED: business_name column was not created';
  END IF;
END $$;
