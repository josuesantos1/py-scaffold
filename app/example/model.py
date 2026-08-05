"""msgspec Structs for the example app."""

import msgspec


class ItemCreate(msgspec.Struct):
    name: str
    description: str | None = None


class Item(msgspec.Struct, frozen=True, gc=False):
    id: int
    name: str
    description: str | None = None


item_decoder = msgspec.json.Decoder(ItemCreate)
item_encoder = msgspec.json.Encoder()
