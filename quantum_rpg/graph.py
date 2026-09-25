"""Layout for the dialogue graph. Boxes and arrows, no pictures."""

from __future__ import annotations


def dialogue_layout(nodes: dict, cols: int = 3) -> tuple[dict, list, int]:
    ids = [str(k) for k in (nodes or {})]
    boxes: dict[str, tuple[int, int, int, int]] = {}
    width, height, gapx, gapy = 150, 36, 28, 36
    for i, nid in enumerate(ids):
        col, row = i % cols, i // cols
        x = 16 + col * (width + gapx)
        y = 16 + row * (height + gapy)
        boxes[nid] = (x, y, x + width, y + height)
    edges: list[tuple[str, str]] = []
    for nid, node in (nodes or {}).items():
        nid = str(nid)
        if not isinstance(node, dict):
            continue
        for choice in node.get("choices") or []:
            if not isinstance(choice, dict):
                continue
            goto = str(choice.get("goto") or "")
            if goto and goto in boxes and goto != nid:
                edges.append((nid, goto))
    rows = max(1, (len(ids) + cols - 1) // cols) if ids else 1
    canvas_h = 16 + rows * (height + gapy) + 8
    return boxes, edges, canvas_h
