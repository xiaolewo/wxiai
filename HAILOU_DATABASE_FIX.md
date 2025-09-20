# Hailuo Database Migration Fix

## Issue

The application was throwing an error when trying to access the `hailuo_config` table:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: hailuo_config
```

## Solution

1. Created a new migration file (`019_add_hailuo_models.py`) that defines both required tables:
   - `hailuo_config`: Stores configuration settings for the Hailuo service
   - `hailuo_tasks`: Tracks video generation tasks

2. Ran the migration to create the tables in the database

3. Created a default configuration record in the `hailuo_config` table

## Verification

- Both tables now exist in the database
- The configuration can be retrieved successfully
- The application should no longer throw the "no such table" error
