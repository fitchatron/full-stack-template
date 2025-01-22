-- Create the trigger function
CREATE OR REPLACE FUNCTION set_user_metadata()
RETURNS TRIGGER AS $$
BEGIN
  -- Check if created_at is NULL and set it to the id column
  IF NEW.created_by IS NULL THEN
    NEW.created_by := NEW.id;
  END IF;
  
  -- Check if updated_by is NULL and set it to the id column
  IF NEW.updated_by IS NULL THEN
    NEW.updated_by := NEW.id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach the trigger to the table
CREATE TRIGGER set_user_metadata_trigger
BEFORE INSERT ON "public"."users"
FOR EACH ROW
WHEN (NEW.created_by IS NULL OR NEW.updated_by IS NULL)
EXECUTE FUNCTION set_user_metadata();