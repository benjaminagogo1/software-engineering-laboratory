import json
print("sssssecond")


class JsonStorage:

    def load(self):
        with open("data/expense.json", "r") as save_file:
            return json.load(save_file)

    def save(self, data):
        with open("data/expense.json", "w") as save_file:
            json.dump(data, save_file, indent=4)