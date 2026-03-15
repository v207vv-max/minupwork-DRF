from __future__ import annotations

import ast
import os
import struct
from pathlib import Path


def parse_po(path: Path) -> dict[str, str]:
    messages: dict[str, str] = {}
    current_id: str | None = None
    current_str: str | None = None
    state: str | None = None

    def flush() -> None:
        nonlocal current_id, current_str
        if current_id is not None and current_str is not None:
            messages[current_id] = current_str
        current_id = None
        current_str = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            flush()
            current_id = ast.literal_eval(line[5:].strip())
            current_str = ""
            state = "id"
            continue
        if line.startswith("msgstr "):
            current_str = ast.literal_eval(line[6:].strip())
            state = "str"
            continue
        if line.startswith('"'):
            value = ast.literal_eval(line)
            if state == "id" and current_id is not None:
                current_id += value
            elif state == "str" and current_str is not None:
                current_str += value
    flush()
    return messages


def write_mo(messages: dict[str, str], path: Path) -> None:
    ids = sorted(messages.keys())
    strs = [messages[msgid] for msgid in ids]

    ids_blob = b""
    strs_blob = b""
    id_offsets: list[tuple[int, int]] = []
    str_offsets: list[tuple[int, int]] = []

    for msgid in ids:
        data = msgid.encode("utf-8")
        id_offsets.append((len(data), len(ids_blob)))
        ids_blob += data + b"\0"

    for msgstr in strs:
        data = msgstr.encode("utf-8")
        str_offsets.append((len(data), len(strs_blob)))
        strs_blob += data + b"\0"

    keystart = 7 * 4
    valuestart = keystart + len(ids) * 8
    id_data_start = valuestart + len(ids) * 8
    str_data_start = id_data_start + len(ids_blob)

    output = bytearray()
    output += struct.pack("Iiiiiii", 0x950412DE, 0, len(ids), keystart, valuestart, 0, 0)

    for length, offset in id_offsets:
        output += struct.pack("ii", length, id_data_start + offset)

    for length, offset in str_offsets:
        output += struct.pack("ii", length, str_data_start + offset)

    output += ids_blob
    output += strs_blob
    path.write_bytes(output)


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "locale"
    for po_path in base.rglob("django.po"):
        mo_path = po_path.with_suffix(".mo")
        messages = parse_po(po_path)
        mo_path.parent.mkdir(parents=True, exist_ok=True)
        write_mo(messages, mo_path)
        print(f"compiled {po_path} -> {mo_path}")


if __name__ == "__main__":
    main()
