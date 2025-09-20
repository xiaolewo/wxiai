"""Peewee migrations -- 020_add_flux_models.py.

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

    # Create flux_config table
    @migrator.create_model
    class FluxConfig(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        api_key = pw.TextField()
        base_url = pw.CharField(max_length=500, default="https://queue.fal.run")
        enabled = pw.BooleanField(default=True)
        timeout = pw.IntegerField(default=300)
        max_concurrent_tasks = pw.IntegerField(default=5)
        default_model = pw.CharField(max_length=100, default="fal-ai/flux-1/dev")
        model_credits = pw.TextField(null=True)  # JSON field
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        updated_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])

        class Meta:
            table_name = "flux_config"

    # Create flux_tasks table
    @migrator.create_model
    class FluxTask(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        user_id = pw.CharField(max_length=255, index=True)
        request_id = pw.CharField(max_length=255, index=True)
        model = pw.CharField(max_length=100)
        task_type = pw.CharField(max_length=20)
        status = pw.CharField(max_length=20, default="PENDING")
        prompt = pw.TextField(null=True)
        input_image_url = pw.TextField(null=True)
        input_image_urls = pw.TextField(null=True)  # JSON field
        uploaded_image_url = pw.TextField(null=True)
        num_images = pw.IntegerField(default=1)
        aspect_ratio = pw.CharField(max_length=20, default="1:1")
        image_size = pw.TextField(null=True)  # JSON field
        guidance_scale = pw.FloatField(default=3.5)
        num_inference_steps = pw.IntegerField(default=28)
        seed = pw.IntegerField(null=True)
        safety_tolerance = pw.IntegerField(default=2)
        strength = pw.FloatField(default=0.95)
        sync_mode = pw.BooleanField(default=False)
        output_format = pw.CharField(max_length=10, default="jpeg")
        enable_safety_checker = pw.BooleanField(default=True)
        image_url = pw.TextField(null=True)
        cloud_image_url = pw.TextField(null=True)
        generation_time = pw.FloatField(null=True)
        queue_position = pw.IntegerField(null=True)
        error_message = pw.TextField(null=True)
        retry_count = pw.IntegerField(default=0)
        flux_response = pw.TextField(null=True)  # JSON field
        created_at = pw.DateTimeField(
            constraints=[pw.SQL("DEFAULT (datetime('now'))")], index=True
        )
        updated_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        completed_at = pw.DateTimeField(null=True)

        class Meta:
            table_name = "flux_tasks"

    # Create flux_credits table
    @migrator.create_model
    class FluxCredits(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        user_id = pw.CharField(max_length=255, index=True)
        credits_balance = pw.IntegerField(default=0)
        total_used = pw.IntegerField(default=0)
        created_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])
        updated_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT (datetime('now'))")])

        class Meta:
            table_name = "flux_credits"

    # Add initial config record - only if not in fake mode
    if not fake:
        # Use raw SQL to insert the default configuration to avoid model dependency issues
        try:
            database.execute_sql(
                """
                INSERT INTO flux_config (
                    id, api_key, base_url, enabled, timeout, 
                    max_concurrent_tasks, default_model, model_credits, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
                (
                    "default",  # id
                    "",  # api_key (empty by default)
                    "https://queue.fal.run",  # base_url
                    False,  # enabled
                    300,  # timeout
                    5,  # max_concurrent_tasks
                    "fal-ai/flux-1/dev",  # default_model
                    None,  # model_credits
                ),
            )
        except Exception as e:
            # If insertion fails, it might be because the record already exists
            print(
                f"Note: Could not create initial FluxConfig record (may already exist): {e}"
            )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model("flux_credits")
    migrator.remove_model("flux_task")
    migrator.remove_model("flux_config")
