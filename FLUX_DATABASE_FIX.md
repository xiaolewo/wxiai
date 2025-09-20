# Flux Database Migration Fix

## Issue

The application was throwing an error when trying to access the `flux_tasks` table:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: flux_tasks
```

## Solution

1. Created a new migration file (`020_add_flux_models.py`) that defines all required Flux tables:
   - `flux_config`: Stores configuration settings for the Flux service
   - `flux_tasks`: Tracks image generation tasks
   - `flux_credits`: Manages user credits for Flux usage

2. Ran the migration to create the tables in the database

3. Created a default configuration record in the `flux_config` table

## Verification

- All three tables now exist in the database
- The tables have the correct structure with all required columns
- The application should no longer throw the "no such table" error
- All Flux models can be imported and used without errors
