from __future__ import annotations
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from . import PogoData, PogoDataEnum, PokemonType


class Move:
    name: str
    proto: PogoDataEnum
    type: PokemonType

    def __init__(self, move_id: Union[str, int], pogodata: PogoData):
        self.proto = pogodata.move_enum.get(move_id)
        self.name = pogodata.move_translations.get(self.proto.value, "")
        self.type = pogodata.move_settings.get(self.proto.value).get_type(pogodata)

    def __repr__(self):
        return f"<Move {self.proto.name}>"

    def __str__(self):
        return self.name
