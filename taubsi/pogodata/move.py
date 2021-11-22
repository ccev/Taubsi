from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taubsi.pogodata import PogoData


class Move:
    id: int
    name: str
    proto_id: str

    def __init__(self, id_: int, pogodata: PogoData):
        self.id = id_
        self.name = pogodata.moves.get(id_, "")
        self.proto_id = pogodata.move_mapping.get(id_, "SIGNAL_BEAM")

    def __repr__(self):
        return f"<Move {self.id}>"

    def __str__(self):
        return self.name
