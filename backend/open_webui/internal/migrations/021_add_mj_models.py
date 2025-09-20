"""Peewee migrations -- 021_add_mj_models.py.

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

    # Create mj_config table
    @migrator.create_model
    class MJConfig(pw.Model):
        id = pw.AutoField()
        enabled = pw.BooleanField(default=False)
        base_url = pw.CharField(max_length=500)
        api_key = pw.TextField()
        modes = pw.TextField(null=True)  # JSON field
        default_mode = pw.CharField(max_length=50, default="fast")
        max_concurrent_tasks = pw.IntegerField(default=5)
        task_timeout = pw.IntegerField(default=300000)
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        updated_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])

        class Meta:
            table_name = "mj_config"

    # Create mj_tasks table
    @migrator.create_model
    class MJTask(pw.Model):
        id = pw.CharField(max_length=50, primary_key=True)
        user_id = pw.CharField(max_length=50, index=True)
        action = pw.CharField(max_length=50)
        status = pw.CharField(max_length=50, default="SUBMITTED")
        prompt = pw.TextField()
        prompt_en = pw.TextField()
        description = pw.TextField()
        mode = pw.CharField(max_length=50, default="fast")
        credits_cost = pw.IntegerField(default=0)
        submit_time = pw.DateTimeField(
            constraints=[pw.SQL("DEFAULT (datetime('now'))")]
        )
        start_time = pw.DateTimeField(null=True)
        finish_time = pw.DateTimeField(null=True)
        progress = pw.CharField(max_length=20, default="0%")
        image_url = pw.TextField(null=True)
        cloud_image_url = pw.TextField(null=True)
        fail_reason = pw.TextField(null=True)
        properties = pw.TextField(null=True)  # JSON field
        buttons = pw.TextField(null=True)  # JSON field
        parent_task_id = pw.CharField(max_length=50, null=True)
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        updated_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])

        class Meta:
            table_name = "mj_tasks"

    # Create mj_credits table
    @migrator.create_model
    class MJCredit(pw.Model):
        id = pw.CharField(max_length=50, primary_key=True)
        user_id = pw.CharField(max_length=50, index=True)
        amount = pw.IntegerField()
        balance = pw.IntegerField()
        reason = pw.CharField(max_length=200)
        task_id = pw.CharField(max_length=50, null=True)
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])

        class Meta:
            table_name = "mj_credits"

    # Add initial config record - only if not in fake mode
    if not fake:
        # Use raw SQL to insert the default configuration to avoid model dependency issues
        try:
            database.execute_sql(
                """
                INSERT INTO mj_config (
                    enabled, base_url, api_key, modes, default_mode,
                    max_concurrent_tasks, task_timeout, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
                (
                    False,  # enabled
                    "",  # base_url
                    "",  # api_key
                    None,  # modes (JSON)
                    "fast",  # default_mode
                    5,  # max_concurrent_tasks
                    300000,  # task_timeout
                ),
            )
        except Exception as e:
            # If insertion fails, it might be because the record already exists
            print(
                f"Note: Could not create initial MJConfig record (may already exist): {e}"
            )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model("mj_credit")
    migrator.remove_model("mj_task")
    migrator.remove_model("mj_config")
