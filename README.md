# AI 工具學習筆記站

我學 AI 工具時整理的筆記網站。每篇都照同一個格式寫：重點、說明、步驟、範例、常見錯誤、小測驗、延伸閱讀。

- 網站：<https://chrrrrrishao.github.io/ai-tool-notes/>
- 規則：[AGENTS.md](AGENTS.md)（Claude Code 透過 [CLAUDE.md](CLAUDE.md) 讀同一份）
- 元件庫：<https://chrrrrrishao.github.io/ai-tool-notes/components.html>

## 為什麼這樣做

之前用 AI 做網頁，通常是這一頁做完就結束，下一頁又要重新跟 AI 講一次要什麼。這次我先把規則寫成 `AGENTS.md`，再讓 AI 照著規則寫，所以之後要加新筆記，只要給主題就好，格式和風格都會跟前面一樣。

## 專案裡有什麼

| 檔案 | 用途 |
|---|---|
| `AGENTS.md` | 給 AI 看的規則：結構、命名、每篇的固定段落、寫作方式、新增步驟、不能做的事 |
| `templates/note.html` | 筆記模板，段落已經排好 |
| `data/notes.json` | 每篇筆記的標題、分類、日期，首頁從這裡讀 |
| `data/site.json` | 站名、英文副標、GitHub repo |
| `assets/css/style.css`、`components.html` | 樣式和可以用的元件 |
| `scripts/new_note.py` | 建立新筆記的骨架並登記 |
| `scripts/rename_site.py` | 換主題時，一次改掉所有頁面的站名和連結 |
| `scripts/check_notes.py` | 檢查有沒有照規則寫，push 時 GitHub Actions 也會跑 |
| `.claude/commands/new-note.md` | Claude Code 的 `/new-note` 指令 |

## 新增一篇筆記

用 Claude Code：

```text
/new-note MCP 入門
```

用其他 AI 工具：請它讀 `AGENTS.md`，照第 10 節 A 的步驟新增一篇。

自己手動：

```bash
python scripts/new_note.py mcp-intro "MCP 入門" "讓 AI 連上外部工具和資料的共通規格。" --category concept --level 2 --minutes 7 --tags MCP,Agent
# 照 AGENTS.md 第 5 節把 notes/mcp-intro/index.html 填完
python scripts/check_notes.py
```

前 4 篇是一開始建站時一起做的。第 5 篇 [RAG 入門](notes/rag-intro/index.html) 是規則寫好之後，照 `/new-note` 的流程加進來的（見 commit `note: 新增 rag-intro`），格式和前面 4 篇一樣，檢查腳本也直接通過。

## 換成別的主題

這套架構也可以拿來做課程講義或讀書筆記。換站名、副標和 GitHub 連結只要一行：

```bash
python scripts/rename_site.py --name "資料結構講義站" --sub "DS Lessons" --repo 帳號/ds-lessons
```

分類、每頁段落、配色要改哪些地方，寫在 `AGENTS.md` 第 14 節。

## 在自己電腦上看

```bash
python -m http.server 8000
# 開 http://localhost:8000
```

純 HTML、CSS、JavaScript，不用安裝套件，也沒有建置步驟。
