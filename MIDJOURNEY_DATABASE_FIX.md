# Midjourney Database Migration Fix

## Issue

The application was throwing an error when trying to access the `mj_config` table:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: mj_config
```

## Solution

1. Created a new migration file (`021_add_mj_models.py`) that defines all required Midjourney tables:
   - `mj_config`: Stores configuration settings for the Midjourney service
   - `mj_tasks`: Tracks Midjourney generation tasks
   - `mj_credits`: Manages user credits for Midjourney usage

2. Ran the migration to create the tables in the database

3. Created a default configuration record in the `mj_config` table

## Verification

- All three tables now exist in the database
- The tables have the correct structure with all required columns
- The application should no longer throw the "no such table" error
- All Midjourney models can be imported and used without errors
- Default configuration has been created successfully
