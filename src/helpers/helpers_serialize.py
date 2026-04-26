# src/helpers/helpers_serialize.py
import json
import os.path
from typing import Dict

import toml
import yaml


def get_serialized_data(path: str) -> Dict:
    """
    Reads and deserializes data from a file based on its extension.
    Supported formats: YAML, JSON, TOML.

    :param path: The file path of the serialized data to be loaded.
    :return: A Python dictionary containing the deserialized data.
    :raises ValueError: If the file extension is not supported.
    """
    _, extension = os.path.splitext(path)
    with open(path, mode="r", encoding="utf-8") as file:
        if extension in (".yaml", ".yml"):
            return yaml.safe_load(file)
        elif extension == ".json":
            return json.load(file)
        elif extension == ".toml":
            return toml.load(file)
        raise ValueError(f"Unsupported file extension {extension} | file={path}")


def dict_to_serialized_file(data: Dict, path: str) -> None:
    """
    Serializes a Python dictionary and writes it to a file.
    Supported formats: YAML, JSON, TOML.

    :param data: The Python dictionary to serialize.
    :param path: The file path where the serialized data will be saved.
    :raises ValueError: If the file extension is not supported.
    """
    _, extension = os.path.splitext(path)
    with open(path, mode="w", encoding="utf-8") as file:
        if extension in (".yaml", ".yml"):
            yaml.dump(data, file, allow_unicode=True)
        elif extension == ".json":
            json.dump(data, file, indent=4)
        elif extension == ".toml":
            toml.dump(data, file)
        else:
            raise ValueError(f"Unsupported file extension {extension} | file={path}")
