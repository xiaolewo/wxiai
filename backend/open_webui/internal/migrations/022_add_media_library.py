"""Peewee migrations -- 022_add_media_library.py.

Creates media library tables used by the new media asset management feature.
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


VISIBILITY_USER = "user"


def _timestamp_default():
    return pw.SQL("DEFAULT (datetime('now'))")


def migrate(migrator: Migrator, database: pw.Database, *, fake: bool = False):
    """Write your migrations here."""

    @migrator.create_model
    class MediaFolder(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        parent_id = pw.CharField(max_length=255, null=True)
        visibility_scope = pw.CharField(max_length=20, default=VISIBILITY_USER)
        owner_id = pw.CharField(max_length=255)
        name = pw.CharField(max_length=255)
        slug = pw.CharField(max_length=255, null=True)
        preset_key = pw.CharField(max_length=100, null=True)
        sort_order = pw.IntegerField(default=0)
        is_locked = pw.BooleanField(default=False)
        created_at = pw.DateTimeField(constraints=[_timestamp_default()])
        updated_at = pw.DateTimeField(constraints=[_timestamp_default()])
        deleted_at = pw.DateTimeField(null=True)

        class Meta:
            table_name = "media_folder"
            indexes = ((("owner_id", "visibility_scope"), False),)

    @migrator.create_model
    class MediaAsset(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        file_id = pw.CharField(max_length=255)
        visibility_scope = pw.CharField(max_length=20, default=VISIBILITY_USER)
        owner_id = pw.CharField(max_length=255)
        display_name = pw.CharField(max_length=255)
        media_type = pw.CharField(max_length=20)
        mime_type = pw.CharField(max_length=100, null=True)
        width = pw.IntegerField(null=True)
        height = pw.IntegerField(null=True)
        duration = pw.FloatField(null=True)
        source = pw.CharField(max_length=100, null=True)
        folder_id = pw.CharField(max_length=255, null=True)
        tags = pw.TextField(null=True)
        metadata = pw.TextField(null=True)
        created_at = pw.DateTimeField(constraints=[_timestamp_default()])
        updated_at = pw.DateTimeField(constraints=[_timestamp_default()])
        created_by_task_id = pw.CharField(max_length=255, null=True)
        created_by_user_id = pw.CharField(max_length=255, null=True)
        thumbnail_url = pw.TextField(null=True)
        checksum = pw.CharField(max_length=128, null=True)
        deleted_at = pw.DateTimeField(null=True)

        class Meta:
            table_name = "media_asset"
            indexes = (
                (("owner_id", "visibility_scope"), False),
                (("media_type",), False),
                (("created_at",), False),
            )

    @migrator.create_model
    class MediaLibrarySettings(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        enable_group_sharing = pw.BooleanField(default=False)
        allow_bulk_download = pw.BooleanField(default=True)
        allowed_media_types = pw.TextField(null=True)
        default_visibility = pw.CharField(max_length=20, default=VISIBILITY_USER)
        max_storage_per_user = pw.BigIntegerField(null=True)
        max_storage_per_group = pw.BigIntegerField(null=True)
        signed_url_ttl_seconds = pw.IntegerField(null=True)
        thumbnail_strategy = pw.CharField(max_length=50, null=True)
        extra_config = pw.TextField(null=True)
        created_at = pw.DateTimeField(constraints=[_timestamp_default()])
        updated_at = pw.DateTimeField(constraints=[_timestamp_default()])

        class Meta:
            table_name = "media_library_settings"

    @migrator.create_model
    class MediaAssetAudit(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        asset_id = pw.CharField(max_length=255)
        action = pw.CharField(max_length=50)
        actor_id = pw.CharField(max_length=255)
        actor_role = pw.CharField(max_length=50, null=True)
        before = pw.TextField(null=True)
        after = pw.TextField(null=True)
        metadata = pw.TextField(null=True)
        created_at = pw.DateTimeField(constraints=[_timestamp_default()])

        class Meta:
            table_name = "media_asset_audit"
            indexes = (
                (("asset_id",), False),
                (("created_at",), False),
            )

    if not fake:
        try:
            database.execute_sql(
                """
                INSERT INTO media_library_settings (
                    id,
                    enable_group_sharing,
                    allow_bulk_download,
                    allowed_media_types,
                    default_visibility,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (
                    "default",
                    False,
                    True,
                    None,
                    VISIBILITY_USER,
                ),
            )
        except Exception as exc:  # pragma: no cover - protective insert
            print(f"Media library default settings may already exist: {exc}")


def rollback(migrator: Migrator, database: pw.Database, *, fake: bool = False):
    """Rollback migrations."""

    migrator.remove_model("media_asset_audit")

    migrator.remove_model("media_library_settings")

    migrator.remove_model("media_asset")

    migrator.remove_model("media_folder")
