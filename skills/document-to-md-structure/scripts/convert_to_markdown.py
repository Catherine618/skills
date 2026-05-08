#!/usr/bin/env python3
"""
Convert DOCX, PPTX, and text-like documents to Markdown with source markers.

This script intentionally avoids third-party dependencies. PDF extraction is
delegated to common local tools when present, because reliable PDF parsing is
not available in Python's standard library.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def escape_md_cell(text: str) -> str:
    return normalize_ws(text).replace("|", r"\|")


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def sort_key(path: str) -> tuple[int, str]:
    match = re.search(r"(\d+)(?=\.[^.]+$)", path)
    return (int(match.group(1)) if match else 0, path)


def iter_docx_text(node: ET.Element) -> Iterable[str]:
    for child in node.iter():
        name = local_name(child.tag)
        if name == "t" and child.text:
            yield child.text
        elif name == "tab":
            yield "\t"
        elif name in {"br", "cr"}:
            yield "\n"


def paragraph_style(paragraph: ET.Element) -> str:
    p_style = paragraph.find("w:pPr/w:pStyle", NS)
    if p_style is None:
        return ""
    return p_style.attrib.get(f"{{{NS['w']}}}val", "")


def docx_paragraph_to_md(paragraph: ET.Element, title_seen: bool = False) -> str:
    text = normalize_ws("".join(iter_docx_text(paragraph)))
    if not text:
        return ""

    style = paragraph_style(paragraph).lower()
    if "title" == style:
        return f"# {text}"
    heading_match = re.search(r"heading\s*([1-6])|heading([1-6])", style)
    if heading_match:
        level = int(next(group for group in heading_match.groups() if group))
        if title_seen:
            level = min(level + 1, 6)
        return f"{'#' * min(level, 6)} {text}"

    num_pr = paragraph.find("w:pPr/w:numPr", NS)
    if num_pr is not None:
        return f"- {text}"

    return text


def docx_table_to_md(table: ET.Element) -> str:
    rows: list[list[str]] = []
    for row in table.findall("w:tr", NS):
        cells: list[str] = []
        for cell in row.findall("w:tc", NS):
            parts = [normalize_ws("".join(iter_docx_text(p))) for p in cell.findall("w:p", NS)]
            cells.append(escape_md_cell(" ".join(part for part in parts if part)))
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header = padded[0]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in padded[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def convert_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find("w:body", NS)
    if body is None:
        return ""

    blocks: list[str] = []
    title_seen = False
    for child in body:
        name = local_name(child.tag)
        if name == "p":
            block = docx_paragraph_to_md(child, title_seen=title_seen)
            if block.startswith("# ") and paragraph_style(child).lower() == "title":
                title_seen = True
        elif name == "tbl":
            block = docx_table_to_md(child)
        else:
            block = ""
        if block:
            blocks.append(block)
    return "\n\n".join(blocks) + "\n"


def pptx_text_from_shape(shape: ET.Element) -> list[str]:
    paras: list[str] = []
    for paragraph in shape.findall(".//a:p", NS):
        text = normalize_ws("".join(t.text or "" for t in paragraph.findall(".//a:t", NS)))
        if text:
            paras.append(text)
    return paras


def convert_pptx(path: Path) -> str:
    blocks: list[str] = []
    with zipfile.ZipFile(path) as zf:
        slide_paths = sorted(
            [name for name in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
            key=sort_key,
        )
        for index, slide_path in enumerate(slide_paths, start=1):
            root = ET.fromstring(zf.read(slide_path))
            paras: list[str] = []
            for shape in root.findall(".//p:sp", NS):
                paras.extend(pptx_text_from_shape(shape))
            if paras:
                title = paras[0]
                body = "\n".join(f"- {p}" for p in paras[1:])
                blocks.append(f"# Slide {index}: {title}\n\n{body}".strip())
            else:
                blocks.append(f"# Slide {index}\n\n[No extractable text]")
    return "\n\n---\n\n".join(blocks) + "\n"


def run_command(command: list[str]) -> str:
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout


def convert_pdf(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            subprocess.run([pdftotext, "-layout", str(path), str(out)], check=True)
            text = out.read_text(encoding="utf-8", errors="replace")
        return text_to_markdown(text, source_label="PDF text")

    mutool = shutil.which("mutool")
    if mutool:
        text = run_command([mutool, "draw", "-F", "txt", str(path)])
        return text_to_markdown(text, source_label="PDF text")

    raise SystemExit(
        "PDF extraction requires a local PDF text tool such as pdftotext or mutool. "
        "Use the pdf skill or install a PDF extractor, then rerun."
    )


def text_to_markdown(text: str, source_label: str = "Text") -> str:
    paragraphs = [normalize_ws(part) for part in re.split(r"\n\s*\n", text) if normalize_ws(part)]
    if not paragraphs:
        return ""
    return f"<!-- Source: {source_label} -->\n\n" + "\n\n".join(paragraphs) + "\n"


def convert(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return convert_docx(path)
    if suffix == ".pptx":
        return convert_pptx(path)
    if suffix == ".pdf":
        return convert_pdf(path)
    if suffix in {".md", ".markdown"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".txt", ".rtf", ".html", ".htm"}:
        return text_to_markdown(path.read_text(encoding="utf-8", errors="replace"), source_label=suffix[1:].upper())
    raise SystemExit(f"Unsupported file type: {suffix}")


def stats_for(markdown: str) -> dict[str, int]:
    headings = len(re.findall(r"(?m)^#{1,6}\s+", markdown))
    bullets = len(re.findall(r"(?m)^\s*[-*+]\s+", markdown))
    words_or_cjk = re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", markdown)
    return {
        "characters": len(markdown),
        "tokens_rough": len(words_or_cjk),
        "headings": headings,
        "bullets": bullets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert common document formats to Markdown.")
    parser.add_argument("input", type=Path, help="Input .pdf, .docx, .pptx, .md, .txt, .rtf, or .html file")
    parser.add_argument("-o", "--output", type=Path, help="Output Markdown path. Defaults to stdout.")
    parser.add_argument("--stats-json", type=Path, help="Optional path for extraction stats JSON.")
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input does not exist: {input_path}")

    markdown = convert(input_path)
    title = html.escape(input_path.name)
    if not re.search(r"(?m)^#\s+", markdown):
        markdown = f"# {title}\n\n{markdown}"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    if args.stats_json:
        args.stats_json.parent.mkdir(parents=True, exist_ok=True)
        args.stats_json.write_text(json.dumps(stats_for(markdown), ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
