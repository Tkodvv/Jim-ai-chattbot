import json
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, filepath="user_memory.json"):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump({}, f)

    def _load(self):
        with open(self.filepath, "r") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=4)

    def get_user_memory(self, user_id):
        data = self._load()
        return data.get(user_id, {})

    def update_user_memory(self, user_id, key, value):
        data = self._load()
        if user_id not in data:
            data[user_id] = {}
        data[user_id][key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._save(data)

    def append_user_fact(self, user_id, fact):
        data = self._load()
        if user_id not in data:
            data[user_id] = {}
        if "facts" not in data[user_id]:
            data[user_id]["facts"] = []
        data[user_id]["facts"].append({
            "value": fact,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._save(data)

    def get_user_facts(self, user_id):
        data = self._load()
        user_data = data.get(user_id, {})
        return user_data.get("facts", [])

    def delete_user_memory(self, user_id):
        data = self._load()
        if user_id in data:
            del data[user_id]
            self._save(data)

    def get_all_users(self):
        return list(self._load().keys())
