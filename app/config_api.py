import json
from pathlib import Path
import os
class Config:
    def __init__(self):
        print(os.name)
        self.filePath = Path.home() / ".config" / "catf.json" if os.name != 'nt' else Path.home() / "AppData" / "Roaming" / "catf.json"
        self.data = {}
        self.load()
    def load(self):
        if os.path.exists(self.filePath):
            with open(self.filePath, 'r') as f:
                self.data = json.loads(f.read())
    def set(self, key, val):
        self.data[key] = val
        self.save()
    def delete(self, key):
        pass
    def get(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None
    def save(self):
        with open(self.filePath, 'w') as f:
            f.write(json.dumps(self.data))