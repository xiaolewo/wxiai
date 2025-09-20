import os
import json
import logging
from contextlib import contextmanager
from typing import Any, Optional

from open_webui.internal.wrappers import register_connection
from open_webui.env import (
    OPEN_WEBUI_DIR,
    DATABASE_URL,
    DATABASE_SCHEMA,
    SRC_LOG_LEVELS,
    DATABASE_POOL_MAX_OVERFLOW,
    DATABASE_POOL_RECYCLE,
    DATABASE_POOL_SIZE,
    DATABASE_POOL_TIMEOUT,
)
from peewee_migrate import Router
from sqlalchemy import Dialect, create_engine, MetaData, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.sql.type_api import _T
from typing_extensions import Self

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["DB"])


class JSONField(types.TypeDecorator):
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value: Optional[_T], dialect: Dialect) -> Any:
        return json.dumps(value)

    def process_result_value(self, value: Optional[_T], dialect: Dialect) -> Any:
        if value is not None:
            return json.loads(value)

    def copy(self, **kw: Any) -> Self:
        return JSONField(self.impl.length)

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


# Workaround to handle the peewee migration
# This is required to ensure the peewee migration is handled before the alembic migration
def handle_peewee_migration(DATABASE_URL):
    # db = None
    try:
        # Replace the postgresql:// with postgres:// to handle the peewee migration
        db = register_connection(DATABASE_URL.replace("postgresql://", "postgres://"))
        migrate_dir = OPEN_WEBUI_DIR / "internal" / "migrations"
        router = Router(db, logger=log, migrate_dir=migrate_dir)
        router.run()
        db.close()

    except Exception as e:
        log.error(f"Failed to initialize the database connection: {e}")
        log.warning(
            "Hint: If your database password contains special characters, you may need to URL-encode it."
        )
        raise
    finally:
        # Properly closing the database connection
        if db and not db.is_closed():
            db.close()

        # Assert if db connection has been closed
        assert db.is_closed(), "Database connection is still open."


handle_peewee_migration(DATABASE_URL)


SQLALCHEMY_DATABASE_URL = DATABASE_URL

# Handle SQLCipher URLs
if SQLALCHEMY_DATABASE_URL.startswith("sqlite+sqlcipher://"):
    database_password = os.environ.get("DATABASE_PASSWORD")
    if not database_password or database_password.strip() == "":
        raise ValueError(
            "DATABASE_PASSWORD is required when using sqlite+sqlcipher:// URLs"
        )

    # Extract database path from SQLCipher URL
    db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite+sqlcipher://", "")
    if db_path.startswith("/"):
        db_path = db_path[1:]  # Remove leading slash for relative paths

    # Create a custom creator function that uses sqlcipher3
    def create_sqlcipher_connection():
        import sqlcipher3

        conn = sqlcipher3.connect(db_path, check_same_thread=False)
        conn.execute(f"PRAGMA key = '{database_password}'")
        return conn

    engine = create_engine(
        "sqlite://",  # Dummy URL since we're using creator
        creator=create_sqlcipher_connection,
        echo=False,
    )

    log.info("Connected to encrypted SQLite database using SQLCipher")

elif "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Handle MySQL and PostgreSQL connections
    engine_options = {"pool_pre_ping": True}

    # Add connection pool settings if provided
    if isinstance(DATABASE_POOL_SIZE, int) and DATABASE_POOL_SIZE > 0:
        engine_options.update(
            {
                "pool_size": DATABASE_POOL_SIZE,
                "max_overflow": DATABASE_POOL_MAX_OVERFLOW,
                "pool_timeout": DATABASE_POOL_TIMEOUT,
                "pool_recycle": DATABASE_POOL_RECYCLE,
                "poolclass": QueuePool,
            }
        )
    else:
        engine_options["poolclass"] = NullPool

    # Special handling for MySQL
    if "mysql" in SQLALCHEMY_DATABASE_URL.lower():
        engine_options.update(
            {
                "connect_args": {
                    "charset": "utf8mb4",
                    "autocommit": True,
                    "connect_timeout": 30,
                },
                "echo": False,
            }
        )

        # For MySQL, we might need to handle connection issues more gracefully
        try:
            engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_options)
        except Exception as e:
            log.warning(
                f"Initial MySQL connection failed: {e}, retrying with different options..."
            )
            # Try with different connect_args for MySQL
            engine_options["connect_args"] = {
                "charset": "utf8mb4",
                "autocommit": True,
                "connect_timeout": 30,
                "read_timeout": 30,
                "write_timeout": 30,
            }
            engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_options)

    # Special handling for PostgreSQL
    elif "postgresql" in SQLALCHEMY_DATABASE_URL.lower():
        engine_options.update(
            {
                "connect_args": {
                    "connect_timeout": 30,
                },
                "echo": False,
            }
        )
        engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_options)

    # Default handling for other databases
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_options)


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
metadata_obj = MetaData(schema=DATABASE_SCHEMA)
Base = declarative_base(metadata=metadata_obj)
Session = scoped_session(SessionLocal)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


get_db = contextmanager(get_session)
