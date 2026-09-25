from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import config

MIGRATION_DIR = Path("app/storage/migrations")

migration_files = sorted(MIGRATION_DIR.glob("*.py"))




def create_migration_history_table(connection):
      connection.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL
            
            )
            """
      )

def run_migrations(connection):
      create_migration_history_table(connection)
      applied_migrations= get_applied_migrations(connection)

      for migration_file in migration_files:
            if migration_file.name in applied_migrations:
                  continue

            spec = spec_from_file_location(
                  migration_file.stem,
                  migration_file
            )
            if spec is None:
                  raise ImportError(f"Could not load migration: {migration_file}")
            
            module = module_from_spec(spec)

            if spec.loader is None:
                  raise ImportError(f"Could not load migration: {migration_file}")
            
            spec.loader.exec_module(module)

            migration_id = int(migration_file.stem.split("_")[0])

            module.run(connection)
            connection.execute(
                  "INSERT INTO migrations (id, name) VALUES (?, ?)", 
                  (migration_id, migration_file.name)
            )
            connection.commit()


def get_applied_migrations(connection):
      cursor = connection.execute(
            "SELECT id, name FROM migrations"
      )
      rows = cursor.fetchall()
      return {row[1] for row in rows}



if __name__ == "__main__":
      import sqlite3
      import config

      connection = sqlite3.connect(config.DB_PATH)

      run_migrations(connection)

      connection.close()