"""Baseline benchmarks for the example app's hot paths.

Run with:  uv run pytest tests/benchmarks/ --benchmark-only
These benchmarks are excluded from the default test run via
pytest.ini_options addopts = "--benchmark-disable".
"""

import msgspec

from app.example.model import Item, ItemCreate, item_decoder

# ── Fixtures / shared data ────────────────────────────────────────────────────

_ITEM_JSON = b'{"name":"benchmark-item","description":"a test description"}'
_ITEM_JSON_NO_DESC = b'{"name":"benchmark-item"}'
_ITEM_LIST_JSON = (
    b'[{"id":1,"name":"alpha","description":"first"},'
    b'{"id":2,"name":"beta","description":null},'
    b'{"id":3,"name":"gamma","description":"third"}]'
)

_encoder = msgspec.json.Encoder()
_item_list_decoder = msgspec.json.Decoder(list[Item])

_SAMPLE_ITEM = Item(id=1, name="benchmark-item", description="a test description")
_SAMPLE_ITEMS = [
    Item(id=i, name=f"item-{i}", description="desc" if i % 2 == 0 else None)
    for i in range(1, 11)
]


# ── Struct construction ───────────────────────────────────────────────────────


def test_bench_item_construct(benchmark):
    """Cost of constructing an Item struct from scalar args."""
    benchmark(Item, id=1, name="book", description="novel")


def test_bench_item_create_construct(benchmark):
    """Cost of constructing an ItemCreate struct."""
    benchmark(ItemCreate, name="book", description="novel")


# ── JSON decode ───────────────────────────────────────────────────────────────


def test_bench_decode_item_create(benchmark):
    """Decode an ItemCreate from JSON bytes (the POST /items hot path)."""
    benchmark(item_decoder.decode, _ITEM_JSON)


def test_bench_decode_item_create_no_desc(benchmark):
    """Decode an ItemCreate without optional field."""
    benchmark(item_decoder.decode, _ITEM_JSON_NO_DESC)


# ── JSON encode ───────────────────────────────────────────────────────────────


def test_bench_encode_single_item(benchmark):
    """Encode a single Item struct to JSON bytes (GET /items/{id} hot path)."""
    benchmark(_encoder.encode, _SAMPLE_ITEM)


def test_bench_encode_item_list(benchmark):
    """Encode a list of 10 Items to JSON bytes (GET /items hot path)."""
    benchmark(_encoder.encode, _SAMPLE_ITEMS)


# ── Round-trip ────────────────────────────────────────────────────────────────


def test_bench_decode_item_list(benchmark):
    """Decode a list of 3 Items from JSON bytes."""
    benchmark(_item_list_decoder.decode, _ITEM_LIST_JSON)
