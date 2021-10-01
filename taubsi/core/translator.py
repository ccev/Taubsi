from typing import Dict
import os
import json


class Translator:
    texts: Dict[str, str] = {}

    def __init__(self, language: str):
        for entry in os.scandir("locale/"):
            entry: os.DirEntry
            if language in entry.name and entry.name.endswith("json"):
                with open(entry.path, "r", encoding="utf-8") as f:
                    self.texts = json.load(f)

    def translate(self, string: str) -> str:
        return self.texts.get(string, "?")
