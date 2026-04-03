#!/usr/bin/env python3

import argparse
import dataclasses
import json
import pathlib
import re
from typing import Iterable, Iterator, Optional


@dataclasses.dataclass(frozen=True)
class ResourceBlock:
    rtype: str
    rid: int
    name: str
    text: str

    @property
    def key(self) -> tuple[str, int, str]:
        return (self.rtype, self.rid, self.name)


HEADER_RE = re.compile(
    r"^\s*(?:data|resource)\s+'([^']+)'\s*\((\d+)(?:,\s*\"([^\"]*)\")?.*$"
)
HEX_LINE_RE = re.compile(r'\$"([0-9A-Fa-f\s]+)"')
SAFE_REWRITE_TYPES = {"TEXT", "STR ", "STR#", "plst", "CSOm"}


def load_snapshot(snapshot_path: pathlib.Path) -> str:
    return snapshot_path.read_bytes().replace(b"\r", b"\n").decode("latin1")


def iter_resource_blocks(snapshot_text: str) -> Iterator[ResourceBlock]:
    current_header = None
    current_lines = []

    for line in snapshot_text.splitlines(keepends=True):
        if current_header is None:
            match = HEADER_RE.match(line)
            if match:
                current_header = (
                    match.group(1),
                    int(match.group(2)),
                    match.group(3) or "",
                )
                current_lines = [line]
            continue

        current_lines.append(line)
        if line.strip() == "};":
            rtype, rid, name = current_header
            yield ResourceBlock(rtype=rtype, rid=rid, name=name, text="".join(current_lines))
            current_header = None
            current_lines = []


def filter_blocks(
    blocks: Iterable[ResourceBlock],
    ids: Optional[set[int]] = None,
    id_min: Optional[int] = None,
    id_max: Optional[int] = None,
    types: Optional[set[str]] = None,
    names: Optional[set[str]] = None,
    name_regex: Optional[re.Pattern[str]] = None,
    exact_keys: Optional[set[tuple[str, int, str]]] = None,
) -> list[ResourceBlock]:
    selected = []
    for block in blocks:
        if exact_keys is not None and block.key not in exact_keys:
            continue
        if ids is not None and block.rid not in ids:
            continue
        if id_min is not None and block.rid < id_min:
            continue
        if id_max is not None and block.rid > id_max:
            continue
        if types is not None and block.rtype not in types:
            continue
        if names is not None and block.name not in names:
            continue
        if name_regex is not None and not name_regex.search(block.name):
            continue
        selected.append(block)
    return selected


def select_blocks(blocks: Iterable[ResourceBlock], selectors: Iterable[dict]) -> list[ResourceBlock]:
    materialized = list(blocks)
    results: list[ResourceBlock] = []
    seen: set[tuple[str, int, str]] = set()

    for selector in selectors:
        exact = selector.get("exact", [])
        exact_keys = None
        if exact:
            exact_keys = {
                (
                    item["type"],
                    int(item["id"]),
                    item.get("name", ""),
                )
                for item in exact
            }
        matched = filter_blocks(
            materialized,
            ids=set(selector["ids"]) if "ids" in selector else None,
            id_min=selector.get("id_min"),
            id_max=selector.get("id_max"),
            types=set(selector["types"]) if "types" in selector else None,
            names=set(selector["names"]) if "names" in selector else None,
            name_regex=re.compile(selector["name_regex"], re.IGNORECASE) if "name_regex" in selector else None,
            exact_keys=exact_keys,
        )
        for block in matched:
            if block.key in seen:
                continue
            seen.add(block.key)
            results.append(block)
    return results


def write_rez_source(output_path: pathlib.Path, blocks: Iterable[ResourceBlock]) -> int:
    materialized = list(blocks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(block.text.rstrip() for block in materialized) + ("\n" if materialized else ""),
        encoding="latin1",
    )
    return len(materialized)


def replace_visible_strings(text: str, replacements: Iterable[tuple[str, str]]) -> str:
    updated = text
    for old, new in replacements:
        updated = updated.replace(old, new)
    return updated


def block_header_line(block: ResourceBlock) -> str:
    return block.text.splitlines()[0]


def extract_block_bytes(block: ResourceBlock) -> bytes | None:
    chunks = []
    for match in HEX_LINE_RE.finditer(block.text):
        chunks.append(bytes.fromhex(match.group(1).replace(" ", "")))
    if not chunks:
        return None
    return b"".join(chunks)


def build_data_block(header_line: str, data: bytes) -> str:
    lines = [header_line.rstrip()]
    if data:
        hex_data = data.hex().upper()
        words = [hex_data[index:index + 4] for index in range(0, len(hex_data), 4)]
        for index in range(0, len(words), 8):
            lines.append('\t$"' + " ".join(words[index:index + 8]) + '"')
    lines.append("};")
    return "\n".join(lines) + "\n"


def rewrite_string_like_data(
    rtype: str,
    data: bytes,
    replacements: Iterable[tuple[str, str]],
) -> bytes:
    if rtype == "TEXT":
        return replace_visible_strings(data.decode("latin1", errors="replace"), replacements).encode("latin1", errors="replace")
    if rtype == "plst":
        text = data.decode("utf-8", errors="replace")
        return replace_visible_strings(text, replacements).encode("utf-8")
    if rtype in {"STR ", "CSOm"}:
        if not data:
            return data
        length = data[0]
        body = data[1:1 + length]
        tail = data[1 + length:]
        rewritten = replace_visible_strings(body.decode("latin1", errors="replace"), replacements).encode("latin1", errors="replace")
        return bytes([min(len(rewritten), 255)]) + rewritten[:255] + tail
    if rtype == "STR#":
        if len(data) < 2:
            return data
        count = int.from_bytes(data[:2], byteorder="big")
        offset = 2
        rewritten_items = []
        for _ in range(count):
            if offset >= len(data):
                return data
            length = data[offset]
            offset += 1
            item = data[offset:offset + length]
            if len(item) != length:
                return data
            offset += length
            rewritten = replace_visible_strings(item.decode("latin1", errors="replace"), replacements).encode("latin1", errors="replace")
            rewritten_items.append(bytes([min(len(rewritten), 255)]) + rewritten[:255])
        return data[:2] + b"".join(rewritten_items) + data[offset:]
    return data


def rewrite_block(
    block: ResourceBlock,
    replacements: Iterable[tuple[str, str]],
    allowed_types: set[str] | None = None,
) -> ResourceBlock:
    if allowed_types is None:
        allowed_types = SAFE_REWRITE_TYPES
    if block.rtype not in allowed_types:
        return block
    data = extract_block_bytes(block)
    if data is None:
        return block
    rewritten = rewrite_string_like_data(block.rtype, data, replacements)
    if rewritten == data:
        return block
    return ResourceBlock(
        rtype=block.rtype,
        rid=block.rid,
        name=block.name,
        text=build_data_block(block_header_line(block), rewritten),
    )


def rewrite_blocks(
    blocks: Iterable[ResourceBlock],
    replacements: Iterable[tuple[str, str]],
    allowed_types: set[str] | None = None,
) -> list[ResourceBlock]:
    return [rewrite_block(block, replacements, allowed_types=allowed_types) for block in blocks]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract resource subsets from eudora.r")
    parser.add_argument("--snapshot", default="eudora.r")
    parser.add_argument("--output", required=True)
    parser.add_argument("--id", action="append", dest="ids", type=int)
    parser.add_argument("--id-min", type=int)
    parser.add_argument("--id-max", type=int)
    parser.add_argument("--type", action="append", dest="types")
    parser.add_argument("--name", action="append", dest="names")
    parser.add_argument("--name-regex")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    snapshot_text = load_snapshot(pathlib.Path(args.snapshot))
    blocks = list(iter_resource_blocks(snapshot_text))
    filtered = filter_blocks(
        blocks,
        ids=set(args.ids) if args.ids else None,
        id_min=args.id_min,
        id_max=args.id_max,
        types=set(args.types) if args.types else None,
        names=set(args.names) if args.names else None,
        name_regex=re.compile(args.name_regex, re.IGNORECASE) if args.name_regex else None,
    )
    count = write_rez_source(pathlib.Path(args.output), filtered)
    if args.summary:
        print(json.dumps({"output": args.output, "count": count}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
