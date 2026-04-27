from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable, List


CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
PUNCTUATION = "，。！？、,.!?;；:："


@dataclass
class SubtitleChunk:
    start: float
    end: float
    text: str


def is_cjk_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    cjk_count = len(CJK_RE.findall(stripped))
    return cjk_count >= max(1, len(stripped) // 3)


def srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hh = total_ms // 3_600_000
    mm = (total_ms % 3_600_000) // 60_000
    ss = (total_ms % 60_000) // 1000
    ms = total_ms % 1000
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def split_text_units(text: str, char_limit: int) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []

    units: List[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            units.append(current.strip())
        current = ""

    for ch in text:
        current += ch
        if ch in PUNCTUATION:
            flush()
        elif len(current) >= char_limit:
            flush()

    flush()

    refined: List[str] = []
    for unit in units:
        if len(unit) <= char_limit:
            refined.append(unit)
            continue
        start = 0
        while start < len(unit):
            refined.append(unit[start : start + char_limit].strip())
            start += char_limit

    return [u for u in refined if u]


def build_lines(text: str) -> List[str]:
    cjk = is_cjk_text(text)
    limit = 16 if cjk else 42
    return split_text_units(text, limit)


def allocate_times(start: float, end: float, chunks: Iterable[str]) -> List[SubtitleChunk]:
    parts = [part for part in chunks if part.strip()]
    if not parts:
        return []

    duration = max(0.001, end - start)
    weights = [max(1, len(re.sub(r"\s+", "", part))) for part in parts]
    total_weight = sum(weights)

    allocated: List[SubtitleChunk] = []
    cursor = start
    for idx, (part, weight) in enumerate(zip(parts, weights)):
        if idx == len(parts) - 1:
            part_end = end
        else:
            part_duration = duration * (weight / total_weight)
            part_end = cursor + part_duration
        allocated.append(SubtitleChunk(start=cursor, end=part_end, text=part.strip()))
        cursor = part_end

    for i in range(1, len(allocated)):
        if allocated[i].start < allocated[i - 1].end:
            allocated[i].start = allocated[i - 1].end

    return allocated


def segment_to_subtitle_chunks(segment_start: float, segment_end: float, segment_text: str) -> List[SubtitleChunk]:
    lines = build_lines(segment_text)
    if not lines:
        return []

    blocks: List[str] = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines):
            blocks.append(f"{lines[i]}\n{lines[i + 1]}")
            i += 2
        else:
            blocks.append(lines[i])
            i += 1

    return allocate_times(segment_start, segment_end, blocks)


def segments_to_srt(segments: Iterable[dict]) -> str:
    all_chunks: List[SubtitleChunk] = []

    for segment in segments:
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start + 0.5))
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        all_chunks.extend(segment_to_subtitle_chunks(start, end, text))

    blocks = []
    for idx, chunk in enumerate(all_chunks, start=1):
        blocks.append(
            "\n".join(
                [
                    str(idx),
                    f"{srt_timestamp(chunk.start)} --> {srt_timestamp(chunk.end)}",
                    chunk.text,
                ]
            )
        )

    return "\n\n".join(blocks) + ("\n" if blocks else "")
