#!/usr/bin/env python3
"""AI 工具學習筆記站 — 規則檢查腳本（把 AGENTS.md 的規則變成程式）

用法：
    python scripts/check_notes.py

檢查項目（對應 AGENTS.md）：
    第 3 節  每篇筆記都已登記；每筆登記都有資料夾
    第 4 節  slug、圖片命名、大小寫、圖片大小
    第 5 節  七個固定區塊的 id、標題、順序與數量
    第 6 節  notes.json 欄位、型別、長度、分類
    第 2、7 節  相對路徑、連結存在、外部連結屬性、禁止 inline style / <style> / 行內 <script>
    第 13 節  不可殘留 {{…}} 或 TODO

零錯誤 exit 0；有錯誤時列出全部問題並 exit 1。只用 Python 標準函式庫。
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE_NAME = "AI 工具學習筆記站"

# 新增分類時要同步修改（AGENTS.md 第 10 節 D）
CATEGORIES = {"tool": "工具", "concept": "概念", "skill": "技巧", "workflow": "流程"}

SECTIONS = [
    ("tldr", "三個重點"),
    ("what", "是什麼"),
    ("how", "怎麼用"),
    ("example", "實際範例"),
    ("pitfalls", "常見錯誤"),
    ("quiz", "小測驗"),
    ("refs", "延伸閱讀"),
]

FIELDS = {
    "slug": str, "title": str, "summary": str, "category": str, "level": int,
    "minutes": int, "updated": str, "tags": list, "order": int,
}
OPTIONAL_FIELDS = {"draft": bool}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IMG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.(?:webp|png|svg|jpg)$")
CJK_RE = re.compile(r"[　-〿㐀-䶿一-鿿豈-﫿＀-￯]")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+#_-]*")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NOTE_SCRIPTS = ["../../assets/js/theme.js", "../../assets/js/main.js"]
MAX_IMG_BYTES = 300 * 1024

errors: list[str] = []


def err(where: Path | str, msg: str) -> None:
    where = where.relative_to(ROOT).as_posix() if isinstance(where, Path) else where
    errors.append(f"{where}: {msg}")


def text_len(s: str) -> int:
    """字數：中文字與全形標點各算 1，英文單字或數字串算 1（AGENTS.md 第 5、6 節）。"""
    return len(CJK_RE.findall(s)) + len(WORD_RE.findall(s))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- HTML parsing
class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict]] = []
        self.body: dict = {}
        self.title = ""
        self.h1: list[str] = []
        self.summary: list[str] = []
        self.description: str | None = None
        self.sections: list[dict] = []
        self.cur: dict | None = None
        self.quizzes: list[dict] = []
        self.links: list[tuple[str, str, dict]] = []  # (tag, url, attrs)
        self.imgs: list[dict] = []
        self.inline_styles = 0
        self.style_tags = 0
        self.scripts: list[str | None] = []
        self._caps: list[list] = []  # [depth, key, buf, target]

    # -- helpers
    @staticmethod
    def classes(a: dict) -> set[str]:
        return set((a.get("class") or "").split())

    def parent(self, n: int = 1) -> tuple[str, dict]:
        return self.stack[-n] if len(self.stack) >= n else ("", {})

    def capture(self, key: str, target: dict | None = None) -> None:
        self._caps.append([len(self.stack), key, [], target])

    # -- HTMLParser hooks
    def handle_starttag(self, tag: str, attrs_list) -> None:  # noqa: C901
        a = {k: (v or "") for k, v in attrs_list}
        cls = self.classes(a)
        ptag, pa = self.parent()
        pcls = self.classes(pa)

        if "style" in a:
            self.inline_styles += 1
        if tag == "style":
            self.style_tags += 1
        if tag == "script":
            self.scripts.append(a.get("src"))
        if tag == "body":
            self.body = a
        if tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        if tag in ("a", "link") and "href" in a:
            self.links.append((tag, a["href"], a))
        if tag in ("img", "script", "source") and a.get("src"):
            self.links.append((tag, a["src"], a))
        if tag == "img":
            self.imgs.append(a)

        if tag == "section" and "note-section" in cls:
            self.cur = {"id": a.get("id", ""), "h2": "", "keypoints": [], "steps": 0,
                        "steps_strong": 0, "code": 0, "warn": 0, "quiz": 0, "refs": 0}
            self.sections.append(self.cur)

        c = self.cur
        if c is not None:
            if tag == "h2" and ptag == "section":
                self.capture("h2", c)
            if tag == "li" and ptag == "ul" and "keypoints" in pcls:
                self.capture("kp", c)
            if tag == "li" and ptag == "ol" and "steps" in pcls:
                c["steps"] += 1
            if tag == "strong" and ptag == "li":
                gtag, ga = self.parent(2)
                if gtag == "ol" and "steps" in self.classes(ga):
                    c["steps_strong"] += 1
            if tag == "pre" and "code" in cls:
                c["code"] += 1
            if tag == "aside" and "callout--warn" in cls:
                c["warn"] += 1
            if tag == "div" and "quiz" in cls:
                c["quiz"] += 1
                self.quizzes.append({"answer": a.get("data-answer", ""), "options": [], "explain": False})
            if tag == "button" and "data-option" in a and self.quizzes:
                self.quizzes[-1]["options"].append(a["data-option"])
            if tag == "p" and "quiz__explain" in cls and self.quizzes:
                self.quizzes[-1]["explain"] = True
            if tag == "li" and ptag == "ul" and "refs" in pcls:
                c["refs"] += 1

        if tag == "title":
            self.capture("title")
        if tag == "h1":
            self.capture("h1")
        if tag == "p" and "note-header__summary" in cls:
            self.capture("summary")

        if tag not in VOID:
            self.stack.append((tag, a))

    def handle_startendtag(self, tag, attrs_list) -> None:
        self.handle_starttag(tag, attrs_list)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                popped = self.stack[i:]
                del self.stack[i:]
                if any(t == "section" and "note-section" in self.classes(x) for t, x in popped):
                    self.cur = None
                break
        self._finish_caps()

    def handle_data(self, data: str) -> None:
        for cap in self._caps:
            cap[2].append(data)

    def _finish_caps(self) -> None:
        keep = []
        for depth, key, buf, target in self._caps:
            if len(self.stack) > depth:
                keep.append([depth, key, buf, target])
                continue
            text = norm("".join(buf))
            if key == "title":
                self.title = text
            elif key == "h1":
                self.h1.append(text)
            elif key == "summary":
                self.summary.append(text)
            elif key == "h2" and target is not None:
                target["h2"] = text
            elif key == "kp" and target is not None:
                target["keypoints"].append(text)
        self._caps = keep


def parse(path: Path) -> tuple[PageParser, str]:
    src = path.read_text(encoding="utf-8")
    p = PageParser()
    p.feed(src)
    p.close()
    return p, src


# ---------------------------------------------------------------- path checks
def exists_exact_case(path: Path) -> bool:
    """GitHub Pages 區分大小寫；Windows 不分，所以逐層比對實際檔名。"""
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        return path.exists()
    cur = ROOT
    for part in rel.parts:
        if not cur.is_dir() or part not in os.listdir(cur):
            return False
        cur = cur / part
    return True


def check_links(path: Path, p: PageParser, external_attrs: bool) -> None:
    for tag, url, attrs in p.links:
        if not url or url.startswith(("#", "mailto:", "data:")):
            continue
        parts = urlsplit(url)
        if parts.scheme in ("http", "https"):
            if external_attrs and tag == "a":
                if attrs.get("target") != "_blank" or "noopener" not in attrs.get("rel", ""):
                    err(path, f'外部連結缺少 target="_blank" rel="noopener"：{url}')
            continue
        if parts.scheme or url.startswith("//"):
            continue
        if url.startswith("/"):
            err(path, f"禁止使用 / 開頭的絕對路徑（GitHub Pages 子路徑會壞）：{url}")
            continue
        target = (path.parent / unquote(parts.path)) if parts.path else path
        if parts.path.endswith("/") or (target.exists() and target.is_dir()):
            target = target / "index.html"
        if not exists_exact_case(target):
            err(path, f"連結指向不存在的檔案（或大小寫不符）：{url}")


def check_common(path: Path, p: PageParser, src: str, scripts: list[str] | None) -> None:
    if p.inline_styles:
        err(path, f"禁止 inline style（找到 {p.inline_styles} 處 style=）")
    if p.style_tags:
        err(path, "禁止在頁面內寫 <style>，樣式請放 assets/css/style.css")
    if any(s is None for s in p.scripts):
        err(path, "禁止行內 <script>，互動請寫在 assets/js/main.js")
    if scripts is not None and p.scripts != scripts:
        err(path, f"只能依序載入 {scripts}，實際為 {p.scripts}")
    if "{{" in src or "}}" in src:
        err(path, "殘留模板 placeholder（{{…}}）")
    if "TODO" in src:
        err(path, "殘留 TODO")
    for img in p.imgs:
        if "alt" not in img:  # 裝飾性圖片可用 alt=""
            err(path, f"<img src=\"{img.get('src')}\"> 缺少 alt")
        for attr in ("width", "height"):
            if not img.get(attr):
                err(path, f"<img src=\"{img.get('src')}\"> 缺少 {attr}")
        if img.get("loading") != "lazy" and "/assets/img/favicon" not in "/" + img.get("src", ""):
            err(path, f"<img src=\"{img.get('src')}\"> 需要 loading=\"lazy\"")


# ---------------------------------------------------------------- notes.json
def check_registry() -> list[dict]:
    reg_path = ROOT / "data" / "notes.json"
    try:
        data = json.loads(reg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        err(reg_path, f"無法讀取或不是合法 JSON：{e}")
        return []
    notes = data.get("notes") if isinstance(data, dict) else None
    if not isinstance(notes, list):
        err(reg_path, '最外層必須是 {"notes": [...]}')
        return []

    seen_slug: set[str] = set()
    seen_order: set[int] = set()
    valid: list[dict] = []
    for i, n in enumerate(notes):
        where = f"data/notes.json[{i}]"
        if not isinstance(n, dict):
            err(where, "每一筆必須是物件")
            continue
        ok = True
        for key, typ in FIELDS.items():
            v = n.get(key)
            if v is None:
                err(where, f"缺少欄位 {key}")
                ok = False
            elif not isinstance(v, typ) or (typ is int and isinstance(v, bool)):
                err(where, f"欄位 {key} 型別應為 {typ.__name__}")
                ok = False
        for key in n:
            if key not in FIELDS and key not in OPTIONAL_FIELDS:
                err(where, f"未定義的欄位 {key}（請先在 AGENTS.md 第 6 節定義）")
        if "draft" in n and not isinstance(n["draft"], bool):
            err(where, "draft 必須是 true 或 false")
        if not ok:
            continue

        slug = n["slug"]
        where = f"data/notes.json[{slug}]"
        if not SLUG_RE.match(slug):
            err(where, "slug 必須是 2–4 個小寫英文字、以連字號連接（例如 rag-intro）")
        if slug in seen_slug:
            err(where, "slug 重複")
        seen_slug.add(slug)
        if n["order"] in seen_order:
            err(where, f"order {n['order']} 重複")
        seen_order.add(n["order"])
        if n["category"] not in CATEGORIES:
            err(where, f"category 只能是 {list(CATEGORIES)}")
        if n["level"] not in (1, 2, 3):
            err(where, "level 只能是 1、2、3")
        if not 1 <= n["minutes"] <= 15:
            err(where, "minutes 必須在 1–15 之間")
        if not DATE_RE.match(n["updated"]):
            err(where, "updated 格式必須是 YYYY-MM-DD")
        else:
            try:
                if date.fromisoformat(n["updated"]) > date.today():
                    err(where, "updated 不能是未來日期")
            except ValueError:
                err(where, "updated 不是合法日期")
        if text_len(n["title"]) > 24:
            err(where, f"title 超過 24 字（目前 {text_len(n['title'])}）")
        if text_len(n["summary"]) > 40:
            err(where, f"summary 超過 40 字（目前 {text_len(n['summary'])}）")
        if not n["summary"].endswith("。"):
            err(where, "summary 必須以全形句號「。」結尾")
        tags = n["tags"]
        if not 1 <= len(tags) <= 4 or not all(isinstance(t, str) and t.strip() for t in tags):
            err(where, "tags 必須是 1–4 個非空字串")
        valid.append(n)
    return valid


# ---------------------------------------------------------------- note pages
def check_note(n: dict) -> None:
    slug = n["slug"]
    path = ROOT / "notes" / slug / "index.html"
    if not exists_exact_case(path):
        err(f"notes/{slug}/", "已登記在 notes.json，但找不到 index.html")
        return
    p, src = parse(path)

    check_common(path, p, src, NOTE_SCRIPTS)
    check_links(path, p, external_attrs=True)

    if p.body.get("data-page") != "note":
        err(path, '<body> 必須有 data-page="note"')
    if p.body.get("data-root") != "../../":
        err(path, '<body> 必須有 data-root="../../"')
    if p.body.get("data-slug") != slug:
        err(path, f'<body data-slug> 必須是 "{slug}"')

    expected_title = f"{n['title']}｜{SITE_NAME}"
    if p.title != expected_title:
        err(path, f"<title> 應為「{expected_title}」，實際為「{p.title}」")
    if p.h1 != [n["title"]]:
        err(path, f"必須剛好一個 <h1> 且與 notes.json title 相同，實際為 {p.h1}")
    if p.summary != [n["summary"]]:
        err(path, f".note-header__summary 必須與 notes.json summary 相同，實際為 {p.summary}")
    if p.description != n["summary"]:
        err(path, '<meta name="description"> 必須與 summary 相同')

    ids = [s["id"] for s in p.sections]
    want = [sid for sid, _ in SECTIONS]
    if ids != want:
        err(path, f"區塊 id 與順序必須是 {want}，實際為 {ids}")
    by_id = {s["id"]: s for s in p.sections}
    for sid, h2 in SECTIONS:
        s = by_id.get(sid)
        if s is None:
            continue
        if s["h2"] != h2:
            err(path, f"#{sid} 的 <h2> 必須是「{h2}」，實際為「{s['h2']}」")

    s = by_id.get("tldr")
    if s:
        if len(s["keypoints"]) != 3:
            err(path, f"#tldr 必須剛好 3 條 .keypoints，實際 {len(s['keypoints'])} 條")
        for kp in s["keypoints"]:
            if text_len(kp) > 30:
                err(path, f"#tldr 重點超過 30 字（{text_len(kp)}）：{kp}")
    s = by_id.get("how")
    if s:
        if not 3 <= s["steps"] <= 7:
            err(path, f"#how 必須有 3–7 個 .steps 步驟，實際 {s['steps']} 個")
        if s["steps_strong"] < s["steps"]:
            err(path, "#how 每個步驟都要有 <strong> 步驟標題")
    s = by_id.get("example")
    if s and s["code"] < 1:
        err(path, "#example 至少要有 1 個 pre.code")
    s = by_id.get("pitfalls")
    if s and not 2 <= s["warn"] <= 4:
        err(path, f"#pitfalls 必須有 2–4 個 .callout--warn，實際 {s['warn']} 個")
    s = by_id.get("quiz")
    if s:
        if not 2 <= s["quiz"] <= 3:
            err(path, f"#quiz 必須有 2–3 題，實際 {s['quiz']} 題")
        for qi, q in enumerate(p.quizzes, 1):
            opts = q["options"]
            if not 3 <= len(opts) <= 4:
                err(path, f"第 {qi} 題必須有 3–4 個選項，實際 {len(opts)} 個")
            if len(set(opts)) != len(opts):
                err(path, f"第 {qi} 題 data-option 重複")
            if q["answer"] not in opts:
                err(path, f"第 {qi} 題 data-answer=\"{q['answer']}\" 不在選項中")
            if not q["explain"]:
                err(path, f"第 {qi} 題缺少 .quiz__explain 解析")
    s = by_id.get("refs")
    if s and not 2 <= s["refs"] <= 5:
        err(path, f"#refs 必須有 2–5 個連結，實際 {s['refs']} 個")

    img_dir = path.parent / "img"
    if img_dir.is_dir():
        for f in sorted(img_dir.iterdir()):
            if not IMG_RE.match(f.name) or not f.name.startswith(slug + "-"):
                err(f, f"圖片命名必須是 {slug}-<描述>.<webp|png|svg|jpg>（小寫、連字號）")
            if f.stat().st_size > MAX_IMG_BYTES:
                err(f, f"圖片超過 300 KB（{f.stat().st_size // 1024} KB）")


def check_folders(registered: set[str]) -> None:
    notes_dir = ROOT / "notes"
    if not notes_dir.is_dir():
        err("notes/", "找不到 notes 資料夾")
        return
    for d in sorted(notes_dir.iterdir()):
        if d.is_dir() and d.name not in registered:
            err(d, "資料夾存在但沒有登記在 data/notes.json")


def check_template() -> None:
    path = ROOT / "templates" / "note.html"
    if not path.exists():
        err("templates/note.html", "找不到模板")
        return
    p, _ = parse(path)
    ids = [s["id"] for s in p.sections]
    if ids != [sid for sid, _ in SECTIONS]:
        err(path, f"模板的區塊必須與 AGENTS.md 第 5 節一致，實際為 {ids}")


def check_top_pages() -> int:
    count = 0
    for path in sorted(ROOT.glob("*.html")):
        count += 1
        p, src = parse(path)
        check_common(path, p, src, ["assets/js/theme.js", "assets/js/main.js"])
        check_links(path, p, external_attrs=True)
        if p.body.get("data-root") != "./":
            err(path, '根目錄頁面的 <body> 必須有 data-root="./"')
        if p.body.get("data-page") not in ("home", "components"):
            err(path, "<body data-page> 必須是 home 或 components")
    return count


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    notes = check_registry()
    for n in notes:
        check_note(n)
    check_folders({n["slug"] for n in notes})
    check_template()
    pages = check_top_pages()

    if errors:
        print(f"✘ 發現 {len(errors)} 個問題：\n")
        for e in errors:
            print(f"  - {e}")
        print("\n請依 AGENTS.md 修正後重新執行。")
        return 1
    drafts = sum(1 for n in notes if n.get("draft"))
    print(f"✔ 檢查通過：{len(notes)} 篇筆記（草稿 {drafts} 篇）、{pages} 個根目錄頁面、模板結構正確。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
