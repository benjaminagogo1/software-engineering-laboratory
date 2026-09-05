# import os
# from dotenv import load_dotenv

# # Reads the .env file in the project root and loads its key=value pairs
# # into the process environment (os.environ), if they aren't already set.
# load_dotenv()

# # os.getenv(key, default) reads the environment variable if present,
# # otherwise falls back to the default. This means the app runs fine
# # even if someone forgets to create a .env file.
# DB_PATH = os.getenv("DB_PATH", "data/expense.db")

import logging

LOG_FILE = "app/app.log"

def setup_logging():
      log_file = LOG_FILE
      handler = logging.FileHandler(log_file)

      formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
      )
      handler.setFormatter(formatter)
      logger = logging.getLogger(__name__)
      logger.addHandler(handler)
      logger.setLevel(logging.INFO)
      return logger