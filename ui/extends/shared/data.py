import json
import sys
from functools import cached_property
from pathlib import Path
from typing import Literal

from PySide6.QtCore import QFile

from .singleton import Singleton

TPartnerModifier = dict[str, Literal[0, 1, 2]]


class Data(metaclass=Singleton):
    def __init__(self):
        root = Path(sys.argv[0]).parent
        self.__dataPath = (root / "data").resolve()

    @property
    def dataPath(self):
        return self.__dataPath

    @cached_property
    def partnerModifiers(self) -> TPartnerModifier:
        data = {}
        builtinFile = QFile(":/partnerModifiers.json")
        builtinFile.open(QFile.OpenModeFlag.ReadOnly)
        builtinData = json.loads(str(builtinFile.readAll(), encoding="utf-8"))
        builtinFile.close()
        data |= builtinData

        customFile = self.dataPath / "partnerModifiers.json"
        if customFile.exists():
            with open(customFile, "r", encoding="utf-8") as f:
                customData = json.loads(f.read())
                data |= customData

        return data

    def expirePartnerModifiersCache(self):
        # expire property caches
        # https://stackoverflow.com/a/69367025/16484891, CC BY-SA 4.0
        self.__dict__.pop("partnerModifiers", None)

    @property
    def arcaeaPath(self):
        return self.dataPath / "Arcaea"
