import os
from dotenv import load_dotenv

# Reads the .env file in the project root and loads its key=value pairs
# into the process environment (os.environ), if they aren't already set.
load_dotenv()

# os.getenv(key, default) reads the environment variable if present,
# otherwise falls back to the default. This means the app runs fine
# even if someone forgets to create a .env file.
DB_PATH = os.getenv("DB_PATH", "data/expense.db")
