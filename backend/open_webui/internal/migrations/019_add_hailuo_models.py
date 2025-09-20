"""Peewee migrations -- 019_add_hailuo_models.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    # Create hailuo_config table
    @migrator.create_model
    class HailuoConfig(pw.Model):
        id = pw.AutoField()
        enabled = pw.BooleanField(default=False)
        base_url = pw.CharField(max_length=500, default="https://api.minimaxi.com")
        api_key = pw.TextField(null=True)
        default_model = pw.CharField(max_length=64, default="MiniMax-Hailuo-02")
        default_duration = pw.IntegerField(default=6)
        default_resolution = pw.CharField(max_length=16, default="768P")
        prompt_optimizer = pw.BooleanField(default=True)
        model_credits_config = pw.TextField(null=True)  # JSON field
        max_concurrent_tasks = pw.IntegerField(default=3)
        task_timeout_ms = pw.IntegerField(default=900000)
        query_interval_ms = pw.IntegerField(default=10000)
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        updated_at = pw.DateTimeField(null=True)

        class Meta:
            table_name = "hailuo_config"

    # Create hailuo_tasks table
    @migrator.create_model
    class HailuoTask(pw.Model):
        id = pw.CharField(max_length=50, primary_key=True)
        user_id = pw.CharField(max_length=50)
        prompt = pw.TextField()
        model = pw.CharField(max_length=64)
        duration = pw.IntegerField()
        resolution = pw.CharField(max_length=16)
        prompt_optimizer = pw.BooleanField(default=True)
        first_frame_url = pw.TextField(null=True)
        last_frame_url = pw.TextField(null=True)
        cloud_input_images = pw.TextField(null=True)  # JSON field
        status = pw.CharField(max_length=20, default="submitted")
        progress = pw.CharField(max_length=10, null=True)
        external_task_id = pw.CharField(max_length=100, null=True)
        file_id = pw.CharField(max_length=100, null=True)
        fail_reason = pw.TextField(null=True)
        result_video_url = pw.TextField(null=True)
        cloud_video_url = pw.TextField(null=True)
        credits_cost = pw.IntegerField(null=True)
        properties = pw.TextField(null=True)  # JSON field
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        updated_at = pw.DateTimeField(null=True)
        finish_time = pw.DateTimeField(null=True)

        class Meta:
            table_name = "hailuo_tasks"

    # Add initial config record - only if not in fake mode
    if not fake:
        # Use raw SQL to insert the default configuration to avoid model dependency issues
        try:
            database.execute_sql(
                """
                INSERT INTO hailuo_config (
                    id, enabled, base_url, api_key, default_model, 
                    default_duration, default_resolution, prompt_optimizer,
                    model_credits_config, max_concurrent_tasks, 
                    task_timeout_ms, query_interval_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
                (
                    1,  # id
                    False,  # enabled
                    "https://api.minimaxi.com",  # base_url
                    None,  # api_key
                    "MiniMax-Hailuo-02",  # default_model
                    6,  # default_duration
                    "768P",  # default_resolution
                    True,  # prompt_optimizer
                    None,  # model_credits_config
                    3,  # max_concurrent_tasks
                    900000,  # task_timeout_ms
                    10000,  # query_interval_ms
                ),
            )
        except Exception as e:
            # If insertion fails, it might be because the record already exists
            print(
                f"Note: Could not create initial HailuoConfig record (may already exist): {e}"
            )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model("hailuo_task")
    migrator.remove_model("hailuo_config")
