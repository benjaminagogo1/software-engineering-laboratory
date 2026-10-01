from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import config

# Resolved against this file, not against the process's working directory.
#
# Written as a bare Path("app/storage/migrations") this was correct only when
# the process happened to be started from the project root — and wrong in a way
# that was invisible rather than loud. `glob` on a path that does not exist
# returns nothing, so `run_migrations` iterated an empty list, recorded nothing,
# and reported success: a database left without its schema, and no error to say
# so. `__file__` is where this module actually is, whatever the CWD.
MIGRATION_DIR = Path(__file__).resolve().parent / "migrations"


def discover_migrations(migration_dir=MIGRATION_DIR):
      """
      Every migration file, in the order they must be applied.

      Raises rather than returning an empty list. Nothing downstream can tell
      "there is nothing to do" apart from "I could not find anything", and the
      second one is a misconfigured deployment, not a no-op. A packing mistake
      that leaves the directory out of the image should stop the service, not
      quietly start it against an empty database.
      """
      if not migration_dir.is_dir():
            raise RuntimeError(
                  f"Migration directory not found: {migration_dir}. "
                  "Refusing to start without knowing whether the schema is current."
            )

      migration_files = sorted(migration_dir.glob("*.py"))

      if not migration_files:
            raise RuntimeError(
                  f"No migrations found in {migration_dir}. "
                  "Refusing to start without knowing whether the schema is current."
            )

      return migration_files


migration_files = discover_migrations()




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
      # Autocommit mode, so the BEGIN below is the only transaction Python opens.
      #
      # sqlite3 auto-begins before DML but *not* before DDL. Left to itself, a
      # migration's CREATE / DROP / ALTER each run in autocommit and commit the
      # moment they succeed, so the BEGIN here would only ever cover the plain
      # INSERTs — and a table rebuild that drops the old table and then fails
      # before renaming the new one into place would leave the schema missing a
      # table with no way back. SQLite has transactional DDL; this is what makes
      # it apply.
      connection.isolation_level = None

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

            # The schema change and the history row commit together or not at
            # all: a migration that is recorded but did not run, or ran but was
            # not recorded, are both states the next startup cannot recover
            # from — the first skips the migration forever, the second applies
            # it twice.
            connection.execute("BEGIN")

            try:
                  module.run(connection)
                  connection.execute(
                        "INSERT INTO migrations (id, name) VALUES (?, ?)",
                        (migration_id, migration_file.name)
                  )
                  connection.commit()
            except Exception:
                  connection.rollback()
                  raise


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