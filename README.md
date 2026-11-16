# AI 工具學習筆記站（AI Tool Notes）

用同一套 `AGENTS.md` 規則寫成的 AI 工具筆記。每篇 10 分鐘內讀完：先看三個重點，再照步驟動手，最後用小測驗確認自己懂了。

- 🌐 網站：<https://chrrrrrishao.github.io/ai-tool-notes/>
- 📏 專案規則：[AGENTS.md](AGENTS.md)（Claude Code 透過 [CLAUDE.md](CLAUDE.md) 匯入）
- 🧩 元件庫：<https://chrrrrrishao.github.io/ai-tool-notes/components.html>

## 這個專案想解決什麼

一般 Vibe Coding 的重點是「把這一頁做出來」。這個專案的重點是**建立一套規則**，讓 AI 之後能用同樣的方式、很快地繼續長出新頁面，而且每一頁的結構、風格、品質都一致。

| 層 | 檔案 | 作用 |
|---|---|---|
| 規則 | `AGENTS.md` | 目的、結構、命名、七個固定區塊、寫作規範、SOP、要做／不要做 |
| 模板 | `templates/note.html` | 七個區塊排好，AI 只填內容 |
| 資料 | `data/notes.json` | 筆記 metadata 唯一來源，首頁與上下篇自動產生 |
| 元件 | `assets/css/style.css`、`components.html` | 只能用既有元件，風格不會跑掉 |
| 自動化 | `scripts/new_note.py` | 一行指令建立骨架並登記 |
| 檢查 | `scripts/check_notes.py`、GitHub Actions | 把規則變成程式，AI 做錯會被抓出來 |
| 指令 | `.claude/commands/new-note.md` | 在 Claude Code 輸入 `/new-note <主題>` 就跑完整流程 |

## 新增一篇筆記

**用 Claude Code：**

```text
/new-note RAG 入門
```

**用其他 AI 工具：** 請它「讀 AGENTS.md，依第 10 節 A 流程新增一篇主題為 RAG 入門的筆記」。

**手動：**

```bash
python scripts/new_note.py rag-intro "RAG 入門" "先查資料再回答，讓 AI 少說錯話。" --category concept --level 1 --minutes 7 --tags RAG,LLM
# 依 AGENTS.md 第 5 節填完 notes/rag-intro/index.html
python scripts/check_notes.py
```

## 本機預覽

```bash
python -m http.server 8000
# 開啟 http://localhost:8000
```

## 技術

純 HTML + CSS + 原生 JavaScript，無建置步驟；GitHub Pages 從 `main` 分支根目錄發布。外部資源只有 Google Fonts。
