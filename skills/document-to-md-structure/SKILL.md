---
name: document-to-md-structure
description: Convert common documents into Markdown, accurately understand their content, and output a concise Chinese summary plus a three-level logical structure with core claims. Use when the user asks to read, open, parse, review, analyze, summarize, outline, extract the structure of, or "读取/阅读/分析/总结/梳理/拆解 XXX 文件" for PDF, DOCX, PPTX, Markdown, TXT, RTF, HTML, or similar knowledge documents, especially when they want the document converted to Markdown or organized into a clear content structure.
---

# Document To Markdown Structure

## Goal

Turn a source document into usable Markdown, then produce:

1. A 1-3 sentence Chinese summary.
2. A three-level logical structure with each part's core claim.

Prioritize accurate understanding over format conversion aesthetics. Preserve evidence markers such as page numbers, slide numbers, headings, captions, and table labels when available.

## Workflow

1. Identify the input file type and user intent.
   - Use this skill for document understanding tasks, not ordinary source-code reading.
   - If the user only asks to convert to Markdown, still preserve structure and source markers so later analysis is reliable.

2. Convert or extract the document to Markdown.
   - Prefer specialized existing skills for difficult formats when available: use the PDF, DOCX/Documents, Presentations, or Spreadsheets skills if layout fidelity, OCR, speaker notes, tracked changes, comments, charts, or tables matter.
   - For straightforward DOCX/PPTX/text conversion, run:

```bash
python3 /Users/ericcheng/.codex/skills/document-to-md-structure/scripts/convert_to_markdown.py <input-file> -o <output.md> --stats-json <stats.json>
```

   - For PDFs, first try the script. If it reports missing PDF extraction tools, use the PDF skill or another available local extraction method. If the PDF is scanned or image-heavy, state that OCR is required before claiming a full reading.

3. Check extraction quality before analysis.
   - Confirm the Markdown is non-empty and contains enough text to support the requested summary.
   - Skim the beginning, middle, and end of the converted Markdown.
   - Compare extracted headings/slide markers against the source file when practical.
   - Flag limitations such as missing OCR, unreadable charts, embedded images, speaker notes not extracted, or lost table structure.

4. Analyze the content logic.
   - Read for argument flow: background/problem, concepts/framework, evidence, solution/recommendation, implementation path, risks, and conclusion.
   - Group slides or pages by logical argument, not mechanically one top-level section per slide/page.
   - Treat headings as evidence, but repair shallow or inconsistent heading levels when the actual logic is clearer.
   - Mark reconstructed hierarchy with "可推断为" when it is inferred rather than explicit.

5. Produce the final response using `references/output-schema.md`.
   - Load that reference before writing the final response.
   - Include the Markdown output file path if a file was created.
   - Keep the final answer concise unless the user asks for exhaustive notes.

## Output Rules

- Write the final answer in Chinese unless the user asks otherwise.
- Use "文档概况" for the 1-3 sentence summary.
- Use "逻辑结构" for the outline.
- Include three levels when the source supports them. Do not invent empty third-level sections.
- For each level, include a "核心论点" that states what that section claims, argues, explains, or recommends.
- If extraction quality is limited, add a short "读取限制" note before the summary.

## Resource Guide

- `scripts/convert_to_markdown.py`: dependency-light converter for DOCX, PPTX, PDF with local PDF tools, Markdown, TXT, RTF, and HTML-like text.
- `references/output-schema.md`: final answer schema and quality checklist. Read it before composing the answer.
