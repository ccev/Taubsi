from typing import Dict, Any
import requests


class Area:
    name: str
    lat: float
    lon: float
    zoom: float

    def __init__(self, name: str, lat: float, lon: float, zoom: float):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.zoom = zoom


class Icons:
    name: str
    url: str
    index: Dict[str, Any]

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

        result = requests.get(url + "index.json")
        self.index = result.json()

        for key, value in self.index.copy().items():
            if not isinstance(value, dict):
                continue
            for sub_key, sub_value in value.items():
                self.index[f"{key}/{sub_key}"] = sub_value
            self.index.pop(key)
