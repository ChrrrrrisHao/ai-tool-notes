---
description: 依 AGENTS.md 規則新增一篇筆記（建立骨架、填內容、登記、檢查）
argument-hint: <筆記主題，例如：MCP 入門>
---

請新增一篇主題為「$ARGUMENTS」的筆記，嚴格依照 `AGENTS.md` 執行：

1. 讀 `data/notes.json`，確認沒有重複主題；有重複就停下來告訴我。
2. 依 `AGENTS.md` 第 4、6 節決定 `slug`、`title`（≤ 24 字）、`summary`（≤ 40 字、以「。」結尾）、`category`、`level`、`minutes`、`tags`，先列出來給我看。
3. 執行骨架腳本建立頁面並登記：
   `python scripts/new_note.py <slug> "<title>" "<summary>" --category <category> --level <level> --minutes <minutes> --tags <tag1,tag2>`
4. 參考 `notes/claude-code-basics/index.html` 的語氣與密度，依 `AGENTS.md` 第 5 節填完七個區塊，只使用第 7 節的元件，遵守第 9 節寫作規範。
5. 延伸閱讀優先用官方文件；寫進頁面前確認網址真的存在。不確定的事實列在回報的「待人工確認」。
6. 執行 `python scripts/check_notes.py`，修到零錯誤。
7. 在 `CHANGELOG.md` 最下方新增一行：`- YYYY-MM-DD note: 新增 <slug>（<title>）`。
8. 回報：新增／修改的檔案、檢查結果、待人工確認事項。不要自動 commit，除非我要求。
