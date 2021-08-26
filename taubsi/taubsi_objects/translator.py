import os
import json

from typing import Dict


class Translator:
    texts: Dict[str, str] = {}

    def __init__(self, language: str):
        for entry in os.scandir("locale/"):
            entry: os.DirEntry
            if language in entry.name and entry.name.endswith("json"):
                with open(entry.path, "r") as f:
                    self.texts = json.load(f)

    def translate(self, string: str) -> str:
        return self.texts.get(string, "?")
