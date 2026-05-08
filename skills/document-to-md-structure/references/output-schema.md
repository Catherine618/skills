# Output Schema

Use this reference when producing the final answer after converting and reading the document.

## Required Output

### 1. Document Summary

Write 1-3 Chinese sentences. Capture the document's topic, purpose, and most important conclusion or proposal. Avoid generic phrases such as "本文主要介绍了"; state the substance directly.

### 2. Logical Structure

Use a three-level outline when the source content supports it:

```markdown
## 逻辑结构

1. 一级部分：主题或阶段
   核心论点：该部分想证明、说明或推动的关键判断。
   1.1 二级部分：子主题
       核心论点：该子主题的关键判断。
       1.1.1 三级部分：论据、机制、步骤或案例
             核心论点：它如何支撑上级论点。
```

If the source document has fewer than three levels, do not invent fake levels. Mark absent levels as "原文未展开到第三级" only when that helps avoid ambiguity.

## Accuracy Rules

- Preserve document-native headings, page numbers, slide numbers, table labels, and section order whenever available.
- Distinguish explicit claims from inferred structure. Use "可推断为" only when the hierarchy is reconstructed from content rather than headings.
- Merge repeated agenda/transition pages into the nearest substantive section.
- Do not treat every slide as a top-level section. Group slides by argument flow.
- When text extraction appears incomplete, state the limitation before summarizing.
- For tables, summarize the trend, comparison, or decision implication rather than reproducing every cell unless the user asks for a full table conversion.

## Quality Checklist

- The 1-3 sentence summary answers: "What is this document about, and what is it trying to get the reader to understand or do?"
- The outline shows argument logic, not just a table of contents.
- Every level has a concise core claim.
- Important constraints, risks, recommendations, or action items are included.
- Any uncertainty from OCR, images, charts, or missing speaker notes is disclosed.
