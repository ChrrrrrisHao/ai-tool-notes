#!/usr/bin/env python3
"""換站名、英文副標與 GitHub 位置（AGENTS.md 第 14 節第 1 步）

站名、副標、repo 都記在 data/site.json。這支腳本會把所有頁面、模板和說明文件裡
舊的值換成新的值，再更新 site.json。CHANGELOG.md 是歷史紀錄，不會被改。

用法：
  python scripts/rename_site.py --name "資料結構講義站" --sub "DS Lessons" --repo yourname/ds-lessons
  python scripts/rename_site.py --name "資料結構講義站" --dry-run   # 只列出會改哪些檔案

三個參數都可以單獨使用，沒給的就維持原樣。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "data" / "site.json"
SKIP_DIRS = {".git", "__pycache__"}
SKIP_FILES = {"CHANGELOG.md"}


def pages_url(repo: str) -> str:
    owner, name = repo.split("/", 1)
    return f"{owner.lower()}.github.io/{name}"


def targets() -> list[Path]:
    files: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_FILES:
            continue
        if p.suffix == ".html" or (p.suffix == ".md" and p.parent in (ROOT, ROOT / ".claude" / "commands")):
            files.append(p)
    return sorted(files)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="換站名、英文副標與 GitHub 位置")
    ap.add_argument("--name", help="新的站名，例如：資料結構講義站")
    ap.add_argument("--sub", help="新的英文副標，例如：DS Lessons")
    ap.add_argument("--repo", help="新的 GitHub repo，格式 帳號/repo 名稱")
    ap.add_argument("--dry-run", action="store_true", help="只列出會改的檔案，不寫入")
    args = ap.parse_args()

    if not (args.name or args.sub or args.repo):
        ap.error("至少要給 --name、--sub、--repo 其中一個")
    if args.repo and args.repo.count("/") != 1:
        ap.error("--repo 格式必須是 帳號/repo 名稱")

    old = json.loads(SITE.read_text(encoding="utf-8"))
    new = dict(old)
    pairs: list[tuple[str, str]] = []
    if args.repo and args.repo != old["repo"]:
        pairs.append((pages_url(old["repo"]), pages_url(args.repo)))
        pairs.append((old["repo"], args.repo))
        new["repo"] = args.repo
    if args.name and args.name != old["name"]:
        pairs.append((old["name"], args.name))
        new["name"] = args.name
    if args.sub and args.sub != old["sub"]:
        pairs.append((old["sub"], args.sub))
        new["sub"] = args.sub
    if not pairs:
        print("沒有需要改的地方（新值和 data/site.json 相同）。")
        return 0

    changed = 0
    for path in targets():
        src = path.read_text(encoding="utf-8")
        out = src
        for a, b in pairs:
            out = out.replace(a, b)
        if out != src:
            changed += 1
            print(f"  {'會修改' if args.dry_run else '已修改'} {path.relative_to(ROOT).as_posix()}")
            if not args.dry_run:
                path.write_text(out, encoding="utf-8", newline="\n")

    if args.dry_run:
        print(f"\n（dry-run）共 {changed} 個檔案會被修改，沒有寫入。")
        return 0

    SITE.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\n✔ 共修改 {changed} 個檔案，並更新 data/site.json。")

    # 提醒：舊的 repo 名稱單獨出現的地方（例如說明裡的 /ai-tool-notes/ 子路徑）要人工確認
    if args.repo and new["repo"] != old["repo"]:
        bare = old["repo"].split("/", 1)[1]
        left = [p.relative_to(ROOT).as_posix() for p in targets() if bare in p.read_text(encoding="utf-8")]
        if left:
            print(f"\n以下檔案還有舊的 repo 名稱「{bare}」，多半是說明或範例，請自己確認要不要改：")
            for f in left:
                print(f"  - {f}")
    print("\n下一步：照 AGENTS.md 第 14 節繼續（分類、段落、配色、範例筆記），最後執行 python scripts/check_notes.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
