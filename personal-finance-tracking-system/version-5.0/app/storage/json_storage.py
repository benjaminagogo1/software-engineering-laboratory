import json


class JsonStorage:

    def load(self):
        with open("data/expense.json", "r") as save_file:
            data = save_file.read()

            if not data:
                return []

            return json.loads(data)

    def save(self, data):
        with open("data/expense.json", "w") as save_file:
            json.dump(data, save_file, indent=4)