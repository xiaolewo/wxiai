#!/usr/bin/env python3
"""
Quick script to create inpainting tables for development
"""

import sqlite3
import os
import sys

# Database path
db_path = "/Users/liuqingliang/Desktop/wxiai/wxiai-main/backend/data/webui.db"


def create_inpainting_tables():
    """Create inpainting tables directly in SQLite"""

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Creating inpainting_config table...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inpainting_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enabled BOOLEAN NOT NULL DEFAULT 0,
                base_url TEXT NOT NULL DEFAULT 'https://api.linkapi.org',
                api_key TEXT NOT NULL DEFAULT '',
                credits_per_task INTEGER NOT NULL DEFAULT 50,
                max_concurrent_tasks INTEGER NOT NULL DEFAULT 3,
                task_timeout INTEGER NOT NULL DEFAULT 300000,
                default_steps INTEGER NOT NULL DEFAULT 30,
                default_strength REAL NOT NULL DEFAULT 0.8,
                default_scale REAL NOT NULL DEFAULT 7.0,
                default_quality TEXT NOT NULL DEFAULT 'M',
                default_dilate_size INTEGER NOT NULL DEFAULT 15,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        print("Creating inpainting_tasks table...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inpainting_tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                external_task_id TEXT,
                status TEXT NOT NULL DEFAULT 'submitted',
                task_status_msg TEXT,
                
                steps INTEGER NOT NULL DEFAULT 30,
                strength REAL NOT NULL DEFAULT 0.8,
                scale REAL NOT NULL DEFAULT 7.0,
                quality TEXT NOT NULL DEFAULT 'M',
                dilate_size INTEGER NOT NULL DEFAULT 15,
                
                credits_cost INTEGER NOT NULL DEFAULT 50,
                submit_time TIMESTAMP,
                start_time TIMESTAMP,
                finish_time TIMESTAMP,
                
                input_image_url TEXT,
                mask_image_url TEXT,
                output_image_url TEXT,
                cloud_image_url TEXT,
                fail_reason TEXT,
                
                properties TEXT,
                progress TEXT DEFAULT '0%',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes
        print("Creating indexes...")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_inpainting_tasks_user_id ON inpainting_tasks (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_inpainting_tasks_status ON inpainting_tasks (status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_inpainting_tasks_created_at ON inpainting_tasks (created_at)"
        )

        # Insert default config if not exists
        print("Inserting default configuration...")
        cursor.execute(
            "INSERT OR IGNORE INTO inpainting_config (id, enabled) VALUES (1, 0)"
        )

        conn.commit()
        print("✅ Inpainting tables created successfully!")

        # Verify tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'inpainting_%'"
        )
        tables = cursor.fetchall()
        print(f"Created tables: {[table[0] for table in tables]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


if __name__ == "__main__":
    success = create_inpainting_tables()
    if success:
        print("\n🎨 Inpainting tables are ready!")
        print("You can now access the admin panel to configure the service.")
    else:
        print("\n❌ Failed to create inpainting tables.")
        sys.exit(1)
