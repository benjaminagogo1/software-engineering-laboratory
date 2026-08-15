import json
from app.storage.storage_error import StorageError


class JsonStorage:

    def load(self):
        try:
            with open("data/expense.json", "r") as save_file:
                data = save_file.read()

                if not data:
                    return []

                return json.loads(data)
        except ValueError:
            return []
        
        except json.JSONDecodeError as error:
            raise StorageError("Expense storage is corrupted") from error






    def save(self, data):
        with open("data/expense.json", "w") as save_file:
            json.dump(data, save_file, indent=4)