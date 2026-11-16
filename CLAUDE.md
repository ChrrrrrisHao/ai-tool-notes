# CLAUDE.md

本專案的規則統一寫在 `AGENTS.md`（所有 AI 工具共用，避免兩份規則不同步）。
Claude Code 會透過下一行自動匯入完整規則：

@AGENTS.md

---

## Claude Code 專用補充

- **新增筆記**：使用 `/new-note <主題>`（定義在 `.claude/commands/new-note.md`），它會照 `AGENTS.md` 第 10 節 A 流程執行。
- **每次修改後**：執行 `python scripts/check_notes.py`，把結果附在回報裡。
- **本機預覽**：`python -m http.server 8000`，開啟 <http://localhost:8000>。
- **規則要改時**：只改 `AGENTS.md`，不要把規則寫進本檔，本檔只放 Claude Code 特有的操作方式。
- **AI 犯錯時**：如果同一種錯誤出現第二次，請提議在 `AGENTS.md` 補一條規則（並說明要補在哪一節），而不是只修這一次。
