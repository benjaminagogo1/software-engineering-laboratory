import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# from logging.handlers import RotatingFileHandler

# Reads the .env file in the project root and loads its key=value pairs
# into the process environment (os.environ), if they aren't already set.
load_dotenv()

# os.getenv(key, default) reads the environment variable if present,
# otherwise falls back to the default. This means the app runs fine
# even if someone forgets to create a .env file.
DB_PATH = os.getenv("DB_PATH", "data/expense.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "app.log"


LOG_LEVELS = {
      "DEBUG": logging.DEBUG,
      "INFO": logging.INFO,
      "WARNING": logging.WARNING,
      "ERROR": logging.ERROR,
      "CRITICAL": logging.CRITICAL
}

# LOG_FILE = "logs/app.log"

def setup_logging():
      log_directory = LOG_FILE.parent
      log_directory.mkdir(parents=True, exist_ok=True)


      # This is designed for string --> LOG_FILE = "logs/app.log"

      # os.makedirs("logs", exist_ok=True)
      # directory_name = os.path.dirname(LOG_FILE)
      # os.makedirs(directory_name, exist_ok=True)


      # Rotating log records by creating new log file at set capacity of memeory space

      # handler = RotatingFileHandler(
      #       LOG_FILE,
      #       maxBytes=1_000_000,
      #       backupCount=3
      #       )

      handler = logging.FileHandler(LOG_FILE)

      formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
      )
      handler.setFormatter(formatter)
      logger = logging.getLogger()
      logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))
      if not logger.handlers:
            logger.addHandler(handler)
      
      return logger 