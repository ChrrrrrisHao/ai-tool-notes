# AGENTS.md — AI 工具學習筆記站

> 這份文件寫給 **AI 代理**（Claude Code、Codex、Cursor、Copilot…）與所有協作者。
> 動手修改任何檔案前，請先讀完本文件。本文件與實際檔案衝突時，**以本文件為準**，並在回報中指出衝突。

---

## 0. 30 秒摘要（先讀這段）

1. 純靜態網站：HTML + CSS + 原生 JavaScript，**沒有建置步驟**，GitHub Pages 直接從 `main` 分支根目錄發布。
2. **一篇筆記 = 一個資料夾 `notes/<slug>/index.html` + `data/notes.json` 裡的一筆登記**，兩者缺一不可。
3. 新筆記一律從 `templates/note.html` 複製，**七個固定區塊不可增刪、不可換順序**（見第 5 節）。
4. 樣式只能用 `assets/css/style.css` 既有的元件 class（見第 7 節與 `components.html`），**不寫 inline style、不加 `<style>`、不引入框架**。
5. 改完一定執行 `python scripts/check_notes.py`，**零錯誤才算完成**。

---

## 1. 專案目的

| 項目 | 內容 |
|---|---|
| 網站名稱 | AI 工具學習筆記站（AI Tool Notes） |
| 一句話定位 | 用同一套規則寫成的 AI 工具筆記，每篇 10 分鐘內讀完，讀完就能動手。 |
| 目標讀者 | 剛開始接觸 AI 工具的大學生（包含未來的自己）。 |
| 內容範圍 | AI 工具的用法（工具）、背後的觀念（概念）、使用技巧（技巧）、完整工作流程（流程）。 |
| **不做** | 新聞快訊、未經驗證的傳聞、長篇論文整理、與 AI 無關的主題。 |

成功的筆記要讓讀者：看完「三個重點」就知道值不值得讀；照著「怎麼用」的步驟就能做出來；做完「小測驗」確認自己懂了。

---

## 2. 技術約束

- **只用** HTML5、CSS、原生 JavaScript（ES2020）。**禁止** npm、`package.json`、React/Vue、Tailwind、打包工具。
- **外部資源只允許 Google Fonts**。不引用任何 CDN 的 JS／CSS。
- **所有路徑都用相對路徑**。網站部署在子路徑 `/ai-tool-notes/` 下，`/assets/...` 這種開頭是 `/` 的絕對路徑會壞掉。
- 每個頁面的 `<body>` 必須有 `data-page` 與 `data-root`：
  - `data-page`：`home`｜`note`｜`components`
  - `data-root`：該頁回到網站根目錄的相對路徑（首頁 `./`，筆記頁 `../../`）
  - 筆記頁另加 `data-slug="<slug>"`
- 每頁只載入兩支 JS：`<head>` 內的 `assets/js/theme.js`（不加 defer，避免深色模式閃爍）與 `</body>` 前的 `assets/js/main.js`（加 defer）。
- `localStorage` 只能用來存「深淺色偏好」，且讀寫都要包 `try/catch`。
- 本機預覽必須開 HTTP 伺服器（首頁用 `fetch` 讀 JSON，直接雙擊 HTML 用 `file://` 會讀不到）：

```bash
python -m http.server 8000
# 開啟 http://localhost:8000
```

---

## 3. 資料夾結構

```text
ai-tool-notes/
├── AGENTS.md                 ← 本文件：所有 AI 共用的專案規則（唯一規則來源）
├── CLAUDE.md                 ← Claude Code 入口：匯入 AGENTS.md ＋ Claude 專用補充
├── README.md                 ← 給人看的專案介紹
├── CHANGELOG.md              ← 變更紀錄（只能往下新增，不改舊紀錄）
├── index.html                ← 首頁：搜尋、分類篩選、筆記卡片（由 notes.json 產生）
├── components.html           ← 元件庫：所有可用元件的實際樣子與 HTML 寫法
├── .nojekyll                 ← 告訴 GitHub Pages 不要跑 Jekyll
├── data/
│   └── notes.json            ← 筆記登記表（metadata 的唯一來源）
├── notes/
│   └── <slug>/
│       ├── index.html        ← 一篇筆記（主檔名永遠是 index.html）
│       └── img/              ← 這篇筆記專用的圖片（沒有圖就不要建）
├── templates/
│   └── note.html             ← 新筆記模板（只能複製，不要直接改它來寫筆記）
├── assets/
│   ├── css/style.css         ← 全站唯一樣式表（設計 token ＋ 元件）
│   ├── js/theme.js           ← 深淺色初始化（<head> 載入）
│   ├── js/main.js            ← 首頁渲染、筆記頁 meta／目錄／上下篇／測驗／複製按鈕
│   └── img/                  ← 全站共用圖示（favicon 等）
├── scripts/
│   ├── new_note.py           ← 建立新筆記骨架並登記到 notes.json（SOP A 第 3、4、6 步）
│   └── check_notes.py        ← 規則檢查腳本（純 Python 標準函式庫）
├── .claude/commands/
│   └── new-note.md           ← Claude Code 指令：/new-note <主題>
└── .github/workflows/
    └── check.yml             ← 每次 push 自動跑 check_notes.py
```

### 「這個東西該放哪？」速查

| 要新增的東西 | 放在哪裡 |
|---|---|
| 一篇新筆記 | `notes/<slug>/index.html`，並登記到 `data/notes.json` |
| 某篇筆記專用的圖 | `notes/<slug>/img/` |
| 全站共用圖示 | `assets/img/` |
| 新的元件樣式 | `assets/css/style.css`（同步更新 `components.html` 與本文件第 7 節） |
| 新的互動功能 | `assets/js/main.js`（用 class 或 `data-*` 觸發，不在頁面內寫 `<script>`） |
| 新的頂層頁面 | 根目錄 `<name>.html`，`data-root="./"`，並加到頁首導覽列 |

---

## 4. 命名規則

| 對象 | 規則 | ✅ 正確 | ❌ 錯誤 |
|---|---|---|---|
| slug（資料夾名） | 小寫英文 + 連字號（kebab-case），2–4 個英文字，用主題名詞 | `claude-code-basics` | `ClaudeCode`、`claude_code`、`第一篇`、`2026-11-note` |
| 筆記主檔 | 永遠是 `index.html` | `notes/rag-intro/index.html` | `notes/rag-intro/rag.html` |
| 圖片 | `<slug>-<描述>.<webp\|png\|svg>`，小寫連字號 | `rag-intro-flow.webp` | `截圖1.PNG`、`image (2).png` |
| CSS class | `元件__子元素--變體`（BEM 風格） | `callout--warn`、`card__title` | `redBox`、`warning2` |
| 區塊 id | 固定七個，見第 5 節 | `tldr`、`how` | `summary`、`step` |

- 圖片寬度 ≤ 1600px、單張 ≤ 300 KB，`<img>` 必須寫 `alt`、`width`、`height`、`loading="lazy"`。
- GitHub Pages **區分大小寫**（Windows 不分），檔名一律小寫。

---

## 5. 筆記頁固定結構（最重要）

每篇筆記的 `<article>` 內，**依序**放這七個 `<section class="note-section">`，id 與標題文字都固定：

| # | `id` | `<h2>` 標題 | 內容要求 | 使用元件 |
|---|---|---|---|---|
| 1 | `tldr` | 三個重點 | **剛好 3 條**，每條 ≤ 30 字，讀完就知道這篇在講什麼 | `.keypoints` |
| 2 | `what` | 是什麼 | 2–3 段說明；可加 1 個比喻或對照表 | 段落、`.callout--note`、`.table` |
| 3 | `how` | 怎麼用 | **3–7 個步驟**，每步標題以動詞開頭 | `.steps` |
| 4 | `example` | 實際範例 | 至少 1 個可直接複製的程式碼或 Prompt | `pre.code` |
| 5 | `pitfalls` | 常見錯誤 | **2–4 個**容易踩的坑，每個都要寫「怎麼避免」 | `.callout--warn` |
| 6 | `quiz` | 小測驗 | **2–3 題單選**，每題 3–4 個選項，附解析 | `.quiz` |
| 7 | `refs` | 延伸閱讀 | **2–5 個連結**，優先官方文件，外部連結加 `target="_blank" rel="noopener"` | `.refs` |

頁首（`<header class="note-header">`）只手寫 `<h1>` 標題與 `.note-header__summary` 摘要；分類、難度、閱讀時間、更新日期、標籤由 `main.js` 依 `notes.json` 自動填入，**不要手寫**。目錄（TOC）與上一篇／下一篇也由 `main.js` 自動產生。

`<title>` 格式固定為：`<筆記標題>｜AI 工具學習筆記站`（中間是全形直線 `｜`）。`<meta name="description">` 必須與摘要相同。

**字數怎麼算**（本文件所有「≤ N 字」都用這個算法，`check_notes.py` 也是）：中文字與全形標點各算 1；一個英文單字或一串數字算 1（例如 `Claude Code` 算 2、`AGENTS.md` 算 1）；半形空格不算。

---

## 6. 筆記登記表 `data/notes.json`

`notes.json` 是**筆記 metadata 的唯一來源**。首頁卡片、筆記頁 meta、上下篇順序全部從這裡讀。

```json
{
  "notes": [
    {
      "slug": "claude-code-basics",
      "title": "Claude Code 入門",
      "summary": "在終端機裡和 AI 一起讀程式、改檔案、跑指令。",
      "category": "tool",
      "level": 1,
      "minutes": 8,
      "updated": "2026-11-16",
      "tags": ["Claude Code", "CLI", "Agent"],
      "order": 1
    }
  ]
}
```

| 欄位 | 型別 | 規則 |
|---|---|---|
| `slug` | string | 與資料夾名完全相同 |
| `title` | string | ≤ 24 字，必須與頁面 `<h1>` 完全相同 |
| `summary` | string | ≤ 40 字、以全形句號結尾，必須與頁面 `.note-header__summary` 完全相同 |
| `category` | string | 只能是下表四個 key 之一 |
| `level` | number | `1` 入門、`2` 進階、`3` 深入 |
| `minutes` | number | 預估閱讀分鐘數，1–15 |
| `updated` | string | `YYYY-MM-DD`，內容有實質修改就更新 |
| `tags` | string[] | 1–4 個，專有名詞保持官方大小寫 |
| `order` | number | 不可重複；新筆記取「目前最大值 + 1」；決定首頁排序與上下篇 |
| `draft` | boolean | 選填。`true` 時首頁不顯示（下架用，不要刪檔） |

### 分類（category）

| key | 顯示名稱 | 放什麼 | 色票 token |
|---|---|---|---|
| `tool` | 工具 | 某個 AI 工具怎麼裝、怎麼用 | `--cat-tool` |
| `concept` | 概念 | 觀念、名詞、原理 | `--cat-concept` |
| `skill` | 技巧 | 讓 AI 更好用的方法（Prompt、除錯…） | `--cat-skill` |
| `workflow` | 流程 | 從頭到尾完成一件事的流程（發布、協作…） | `--cat-workflow` |

---

## 7. 元件庫（只能用這些）

完整實際樣子請開 `components.html`。以下是複製即用的寫法：

```html
<!-- 三個重點：剛好 3 條 -->
<ul class="keypoints">
  <li>第一個重點</li>
  <li>第二個重點</li>
  <li>第三個重點</li>
</ul>

<!-- 提示框：--note 補充說明、--tip 小技巧、--warn 注意／常見錯誤 -->
<aside class="callout callout--tip">
  <p class="callout__title">小技巧</p>
  <p>內容。</p>
</aside>

<!-- 步驟：每步 <strong> 以動詞開頭 -->
<ol class="steps">
  <li><strong>安裝工具</strong><p>說明。</p></li>
</ol>

<!-- 程式碼／Prompt：data-lang 會顯示在右上角，JS 自動加「複製」按鈕 -->
<pre class="code" data-lang="bash"><code>python -m http.server 8000</code></pre>
<pre class="code code--prompt" data-lang="Prompt"><code>請幫我……</code></pre>

<!-- 對照表 -->
<div class="table-wrap">
  <table class="table">
    <thead><tr><th>項目</th><th>A</th><th>B</th></tr></thead>
    <tbody><tr><td>…</td><td>…</td><td>…</td></tr></tbody>
  </table>
</div>

<!-- 小測驗：data-answer 填正確選項的 data-option -->
<div class="quiz" data-answer="b">
  <p class="quiz__q">1. 題目？</p>
  <ol class="quiz__options">
    <li><button type="button" data-option="a">選項 A</button></li>
    <li><button type="button" data-option="b">選項 B</button></li>
    <li><button type="button" data-option="c">選項 C</button></li>
  </ol>
  <p class="quiz__explain">解析：為什麼答案是 B。</p>
</div>

<!-- 延伸閱讀 -->
<ul class="refs">
  <li><a href="https://…" target="_blank" rel="noopener">連結標題</a><span>一句話說明</span></li>
</ul>

<!-- 圖片 -->
<figure class="figure">
  <img src="img/<slug>-xxx.webp" alt="描述圖片內容" width="1200" height="675" loading="lazy">
  <figcaption>圖說。</figcaption>
</figure>
```

行內元素：螢光筆重點 `<mark>`（每段最多 1 個）、指令與檔名 `<code>`、按鍵 `<kbd>`。

---

## 8. 視覺風格

**調性：「方格筆記本 + 螢光筆」**——米白方格紙底、深墨藍文字、紅橘色筆跡當強調、螢光黃畫重點、卡片頂端有一小段紙膠帶（顏色＝分類色）。

- **顏色只能用 CSS 變數**（定義在 `style.css` 的 `:root`），頁面與新元件不可直接寫色碼。

| token | 用途 |
|---|---|
| `--paper` / `--paper-2` / `--card` | 頁面底色／次要底色／卡片底色 |
| `--ink` / `--ink-2` / `--ink-3` | 主文字／次要文字／輔助文字 |
| `--line` | 邊框、分隔線 |
| `--accent` | 連結、主要強調 |
| `--highlight` | `<mark>` 螢光筆 |
| `--cat-tool` / `--cat-concept` / `--cat-skill` / `--cat-workflow` | 四個分類色 |

- 字體：內文 `Noto Sans TC`，程式碼 `JetBrains Mono`（皆 Google Fonts）。
- 版面：內文最大寬度約 70 字；桌機（≥ 1024px）右側固定目錄；手機單欄、左右留白 16px、不可出現橫向捲軸。
- 深色模式：自動跟隨系統，可用右上角按鈕切換；新元件必須在深色模式下也看得清楚。
- 標題不加 emoji；圖示用 CSS 或 inline SVG。

---

## 9. 寫作規範

- **繁體中文、臺灣用語**：程式（不是程序）、資料（不是數據）、檔案（不是文件）、影片（不是視頻）、軟體（不是軟件）。
- **全形標點**：，。、：；「」（）？！；引號用「」，不用 ""。
- **中英數之間加半形空格**：`用 Claude Code 寫 3 個頁面`。
- 專有名詞保持官方大小寫：GitHub、JavaScript、Claude Code、ChatGPT。
- 用第二人稱「你」，口語但精準；一句話盡量 ≤ 40 字；一段 ≤ 4 句。
- 指令、檔名、路徑用 `<code>`；按鍵用 `<kbd>`。
- **不確定的事實不要寫**。與版本有關的資訊加註「（截至 YYYY-MM）」。
- 不大段複製別人的文章；引用請改寫並在「延伸閱讀」附來源。

---

## 10. 標準作業流程（SOP）

### A. 新增一篇筆記

1. 讀 `data/notes.json`，確認主題沒有重複。
2. 決定 `slug`（第 4 節）、`title`、`summary`、`category`（第 6 節）、`level`、`minutes`、`tags`。
3. 建立資料夾並複製模板：`notes/<slug>/index.html` ← `templates/note.html`。
4. 取代模板中所有 `{{SLUG}}`、`{{TITLE}}`、`{{SUMMARY}}`，並刪掉模板開頭的說明註解。
5. 依第 5 節寫完七個區塊，刪掉所有 `TODO`。可以參考 `notes/claude-code-basics/` 的語氣與密度。
6. 在 `data/notes.json` 新增一筆（`order` = 目前最大值 + 1，`updated` = 今天）。
7. 執行 `python scripts/check_notes.py`，修到零錯誤。
8. 在 `CHANGELOG.md` 最下方新增一行。
9. 本機預覽首頁與新頁面，桌機與手機寬度都要看。

> **捷徑：** 第 3、4、6 步可以用一行指令完成，接著直接做第 5 步：
>
> ```bash
> python scripts/new_note.py rag-intro "RAG 入門" "先查資料再回答，讓 AI 少說錯話。" --category concept --level 1 --minutes 7 --tags RAG,LLM
> ```
>
> 在 Claude Code 裡可以直接用 `/new-note RAG 入門`，整個流程會自動跑完。

### B. 修改既有筆記

1. 只改需要改的區塊，保留七區塊結構。
2. 內容有實質修改 → 更新 `notes.json` 的 `updated`。
3. 改了標題或摘要 → `notes.json` 與頁面兩處同步。
4. 執行檢查腳本、更新 `CHANGELOG.md`。

### C. 下架筆記

不要刪除資料夾。在 `notes.json` 該筆加上 `"draft": true`，並寫進 `CHANGELOG.md`。

### D. 新增分類（四處要同步）

1. 本文件第 6 節分類表
2. `assets/js/main.js` 的 `CATEGORIES`
3. `assets/css/style.css` 的 `--cat-<key>` token（淺色＋深色）與 `.tag--<key>`、`.card--<key>`
4. `scripts/check_notes.py` 的 `CATEGORIES`

### E. 新增元件（三處要同步）

1. `assets/css/style.css`（只用 token，不寫死色碼）
2. `components.html` 加一個展示區塊
3. 本文件第 7 節加上寫法

---

## 11. AI 修改規則

**要做：**
- 動手前先說明要改哪些檔案；只改和任務有關的檔案。
- 新筆記先參考一篇現有筆記，保持語氣與密度一致。
- 事實不確定時，在回報中列出「待人工確認」，不要編造指令、網址或版本號。
- 外部連結寫進頁面前，確認網址真的存在。
- 完成後回報：改了哪些檔案、檢查腳本結果、還有什麼沒做。

**不要做：**
- 不要修改 `templates/`、`assets/`、`scripts/`，除非任務明確要求。
- 不要刪除既有筆記（用 `draft` 下架）。
- 不要新增 `package.json`、建置工具或任何框架。
- 不要在頁面寫 inline style、`<style>` 或 `<script>` 區塊。
- 不要手寫筆記頁的分類、難度、日期等 meta（由 `main.js` 產生）。
- 不要放 API key、密碼、個人資料。

---

## 12. Git 規則

- `main` 分支 = 線上網站，push 後約 1–2 分鐘生效。
- commit 訊息格式：`<類型>: <說明>`

| 類型 | 用途 | 範例 |
|---|---|---|
| `note` | 新增／修改筆記內容 | `note: 新增 rag-intro 筆記` |
| `feat` | 新功能、新元件 | `feat: 新增 .compare 元件` |
| `fix` | 修錯 | `fix: 修正首頁搜尋無法比對標籤` |
| `style` | 純視覺調整 | `style: 調整深色模式卡片邊框` |
| `docs` | 修改 AGENTS.md／README | `docs: 補充圖片命名規則` |
| `chore` | 雜項 | `chore: 更新 GitHub Actions 版本` |

- 一篇筆記一個 commit；push 前檢查腳本必須通過（GitHub Actions 也會再跑一次）。

---

## 13. 完成前檢查清單

- [ ] `python scripts/check_notes.py` 零錯誤
- [ ] 新筆記已登記在 `data/notes.json`，`title`／`summary` 與頁面一致
- [ ] 七個區塊齊全、順序正確，數量符合第 5 節
- [ ] 沒有 `{{…}}`、`TODO`、inline style、絕對路徑
- [ ] 繁體中文、全形標點、中英數之間有空格
- [ ] 外部連結可開啟，且有 `target="_blank" rel="noopener"`
- [ ] 首頁卡片、篩選、搜尋正常；筆記頁目錄與上下篇正常
- [ ] 手機寬度（375px）沒有橫向捲軸；深色模式看得清楚
- [ ] `CHANGELOG.md` 已新增紀錄
