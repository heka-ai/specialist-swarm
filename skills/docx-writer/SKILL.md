---
name: docx-writer
description: Generate a branded Sia Partners Word document (.docx) from a markdown proposal. Use whenever the final deliverable should be a Word document. Trigger on any request to produce a .docx, Word document, or branded proposal document.
---

# Docx Writer — Sia Partners Branded Proposal

## When to use

Call this skill whenever you need to write the final proposal as a `.docx` file. Use the bash tool to run the Python snippet below. The output file will be saved as `proposal-response.docx` in the current working directory.

## How to produce the docx

Run this Python script via bash, replacing `MARKDOWN_CONTENT` with the full proposal markdown:

```python
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "python-docx"])

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

MARKDOWN = """REPLACE_WITH_PROPOSAL_MARKDOWN"""

OUTPUT_PATH = "proposal-response.docx"

# --- Sia Partners brand colours ---
SIA_PURPLE = RGBColor(0x5C, 0x27, 0x8F)   # #5C278F
SIA_DARK   = RGBColor(0x1A, 0x1A, 0x2E)   # #1A1A2E
SIA_GREY   = RGBColor(0x6C, 0x75, 0x7D)   # #6C757D

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin   = Inches(1.2)
    section.right_margin  = Inches(1.2)

def set_heading(para, text, level):
    run = para.add_run(text)
    run.bold = True
    if level == 1:
        run.font.size = Pt(20)
        run.font.color.rgb = SIA_PURPLE
    elif level == 2:
        run.font.size = Pt(14)
        run.font.color.rgb = SIA_DARK
    else:
        run.font.size = Pt(12)
        run.font.color.rgb = SIA_GREY
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after  = Pt(4)

def add_body(doc, text):
    para = doc.add_paragraph()
    # Handle **bold** inline
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = para.add_run(part[2:-2])
            run.bold = True
        else:
            para.add_run(part)
    para.paragraph_format.space_after = Pt(4)
    return para

# Title block
title_para = doc.add_paragraph()
title_run = title_para.add_run("Sia Partners")
title_run.font.size = Pt(10)
title_run.font.color.rgb = SIA_PURPLE
title_run.bold = True
title_para.paragraph_format.space_after = Pt(0)

# Parse and render markdown
for line in MARKDOWN.split("\n"):
    line = line.rstrip()
    if line.startswith("### "):
        p = doc.add_paragraph()
        set_heading(p, line[4:], 3)
    elif line.startswith("## "):
        p = doc.add_paragraph()
        set_heading(p, line[3:], 2)
    elif line.startswith("# "):
        p = doc.add_paragraph()
        set_heading(p, line[2:], 1)
    elif line.startswith("- ") or line.startswith("* "):
        p = doc.add_paragraph(style="List Bullet")
        content = line[2:]
        parts = re.split(r'(\*\*[^*]+\*\*)', content)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)
    elif re.match(r'^\d+\.', line):
        p = doc.add_paragraph(style="List Number")
        content = re.sub(r'^\d+\.\s*', '', line)
        p.add_run(content)
    elif line.startswith("|"):
        # Table row — collect below
        pass
    elif line.strip() == "" or line.startswith("---"):
        doc.add_paragraph()
    else:
        add_body(doc, line)

# Re-parse for tables (second pass)
lines = MARKDOWN.split("\n")
i = 0
# Clear doc and redo with table support
doc2 = Document()
for section in doc2.sections:
    section.top_margin    = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin   = Inches(1.2)
    section.right_margin  = Inches(1.2)

title_para2 = doc2.add_paragraph()
title_run2 = title_para2.add_run("Sia Partners")
title_run2.font.size = Pt(10)
title_run2.font.color.rgb = SIA_PURPLE
title_run2.bold = True

while i < len(lines):
    line = lines[i].rstrip()
    if line.startswith("### "):
        p = doc2.add_paragraph(); set_heading(p, line[4:], 3)
    elif line.startswith("## "):
        p = doc2.add_paragraph(); set_heading(p, line[3:], 2)
    elif line.startswith("# "):
        p = doc2.add_paragraph(); set_heading(p, line[2:], 1)
    elif line.startswith("- ") or line.startswith("* "):
        p = doc2.add_paragraph(style="List Bullet")
        content = line[2:]
        parts = re.split(r'(\*\*[^*]+\*\*)', content)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                r = p.add_run(part[2:-2]); r.bold = True
            else:
                p.add_run(part)
    elif re.match(r'^\d+\.', line):
        p = doc2.add_paragraph(style="List Number")
        p.add_run(re.sub(r'^\d+\.\s*', '', line))
    elif line.startswith("|") and i + 1 < len(lines) and lines[i+1].startswith("|---"):
        # Markdown table: collect all rows
        table_lines = [line]
        i += 1
        while i < len(lines) and lines[i].startswith("|"):
            if not re.match(r'^\|[-| ]+\|', lines[i]):
                table_lines.append(lines[i])
            i += 1
        headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
        rows    = [[c.strip() for c in r.split("|")[1:-1]] for r in table_lines[1:]]
        tbl = doc2.add_table(rows=1 + len(rows), cols=len(headers))
        tbl.style = "Table Grid"
        hdr_cells = tbl.rows[0].cells
        for j, h in enumerate(headers):
            hdr_cells[j].text = h
            run = hdr_cells[j].paragraphs[0].runs[0] if hdr_cells[j].paragraphs[0].runs else hdr_cells[j].paragraphs[0].add_run(h)
            run.bold = True
            run.font.color.rgb = SIA_PURPLE
        for ri, row in enumerate(rows):
            for ci, cell in enumerate(row):
                tbl.rows[ri+1].cells[ci].text = cell
        doc2.add_paragraph()
        continue
    elif line.strip() == "" or line.startswith("---"):
        doc2.add_paragraph()
    else:
        add_body(doc2, line)
    i += 1

doc2.save(OUTPUT_PATH)
print(f"Saved: {OUTPUT_PATH}")
```

## Important

- Replace `REPLACE_WITH_PROPOSAL_MARKDOWN` with the full proposal text (escape any triple-quotes).
- The file is written to `proposal-response.docx` in the agent's working directory. The session file system will make it downloadable.
- Run this **after** all specialists have replied and you have synthesised the final proposal text.
