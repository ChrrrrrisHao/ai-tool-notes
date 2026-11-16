#!/usr/bin/env python3
"""建立新筆記骨架（AGENTS.md 第 10 節 A 的第 3、4、6 步自動化）

會做三件事：
  1. 複製 templates/note.html → notes/<slug>/index.html
  2. 取代 {{SLUG}}、{{TITLE}}、{{SUMMARY}}，並移除模板開頭的說明註解
  3. 在 data/notes.json 新增一筆（order = 目前最大值 + 1，updated = 今天）

用法：
  python scripts/new_note.py mcp-intro "MCP 入門" "讓 AI 連上外部工具和資料的共通規格。" \
      --category concept --level 2 --minutes 7 --tags MCP,Agent

之後請依 AGENTS.md 第 5 節填完七個區塊，再執行 python scripts/check_notes.py。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ("tool", "concept", "skill", "workflow")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
TEMPLATE_HELP_RE = re.compile(r"<!--\s*\n\s*筆記模板.*?-->\n", re.S)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="建立新筆記骨架並登記到 data/notes.json")
    ap.add_argument("slug", help="小寫英文 + 連字號，2–4 個字，例如 rag-intro")
    ap.add_argument("title", help="筆記標題（≤ 24 字）")
    ap.add_argument("summary", help="一句話摘要（≤ 40 字，以「。」結尾）")
    ap.add_argument("--category", required=True, choices=CATEGORIES)
    ap.add_argument("--level", type=int, default=1, choices=(1, 2, 3))
    ap.add_argument("--minutes", type=int, default=6)
    ap.add_argument("--tags", default="", help="以逗號分隔，1–4 個")
    args = ap.parse_args()

    if not SLUG_RE.match(args.slug):
        print("✘ slug 格式錯誤：必須是 2–4 個小寫英文字，以連字號連接，例如 rag-intro")
        return 1
    if not args.summary.endswith("。"):
        print("✘ summary 必須以全形句號「。」結尾")
        return 1
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if not 1 <= len(tags) <= 4:
        print("✘ tags 必須是 1–4 個（以逗號分隔）")
        return 1

    reg_path = ROOT / "data" / "notes.json"
    data = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {"notes": []}
    if any(n.get("slug") == args.slug for n in data["notes"]):
        print(f"✘ notes.json 已經有 {args.slug}")
        return 1

    note_dir = ROOT / "notes" / args.slug
    if note_dir.exists():
        print(f"✘ 資料夾已存在：notes/{args.slug}/")
        return 1

    tpl = (ROOT / "templates" / "note.html").read_text(encoding="utf-8")
    html = TEMPLATE_HELP_RE.sub("", tpl, count=1)
    html = (html.replace("{{SLUG}}", args.slug)
                .replace("{{TITLE}}", args.title)
                .replace("{{SUMMARY}}", args.summary))
    note_dir.mkdir(parents=True)
    (note_dir / "index.html").write_text(html, encoding="utf-8", newline="\n")

    order = max((n.get("order", 0) for n in data["notes"]), default=0) + 1
    data["notes"].append({
        "slug": args.slug,
        "title": args.title,
        "summary": args.summary,
        "category": args.category,
        "level": args.level,
        "minutes": args.minutes,
        "updated": date.today().isoformat(),
        "tags": tags,
        "order": order,
    })
    reg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"✔ 已建立 notes/{args.slug}/index.html，並登記到 data/notes.json（order {order}）")
    print("下一步：依 AGENTS.md 第 5 節填完七個區塊 → python scripts/check_notes.py → 更新 CHANGELOG.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
