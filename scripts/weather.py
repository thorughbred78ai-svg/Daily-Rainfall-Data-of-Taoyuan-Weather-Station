🌤 Taoyuan Weather

桃園市 13 行政區天氣預報 GitHub Actions 專案。

目前版本：

v2.2.0

功能

桃園市 13 行政區天氣預報

未來 3 天逐 3 小時預報

未來 7 天逐日預報

使用中央氣象署 CWA API

Telegram Bot 推播

GitHub Actions 自動執行

可指定預報日期

可指定行政區

可設定是否推送 Telegram

Telegram 自動分割長訊息

使用 Node.js 內建 fetch()

降雨機率達門檻才進行 Telegram 推播

降雨推播規則

本專案目前的降雨推播門檻為：

降雨機率 >= 70%


規則如下：

降雨機率	Telegram 推播	Telegram 顯示
0% ～ 69%	❌	❌
70%	✅	✅
71% ～ 100%	✅	✅
推播條件

只要：

任一行政區、任一時段的降雨機率 >= 70%

就會觸發整次 Telegram 推播。

訊息內容

Telegram 訊息只會列出：

降雨機率 >= 70%


的資料。

因此：

60% → 不推播、不顯示
69% → 不推播、不顯示
70% → 推播、顯示
80% → 推播、顯示
100% → 推播、顯示


例如：

📍 桃園區

【未來3天・逐3小時】
12:00～15:00｜短暫雨｜降雨70%
15:00～18:00｜雨｜降雨80%


70% 本身會保留在 Telegram 訊息中。

如果所有行政區、所有預報時段的降雨機率都低於 70%，則：

不會發送 Telegram


也不會產生只有標題的空訊息。

CWA 資料集

本專案使用中央氣象署桃園市專屬資料集。

未來 3 天
F-D0047-005


用途：

桃園市未來 3 天逐 3 小時天氣預報

未來 1 週
F-D0047-007


用途：

桃園市未來 1 週天氣預報


本專案不再使用：

F-D0047-093


目前由：

F-D0047-005
+
F-D0047-007


兩個資料集分別取得資料後，再於程式中整理成 Telegram 訊息。

GitHub Secrets

進入：

Repository
→ Settings
→ Secrets and variables
→ Actions


建立以下 GitHub Actions Secrets：

CWA_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

CWA_API_KEY

中央氣象署 API 金鑰。

TELEGRAM_BOT_TOKEN

Telegram Bot Token。

TELEGRAM_CHAT_ID

接收天氣通知的 Telegram Chat ID。

GitHub Actions

可以從 GitHub Actions 手動執行。

進入：

Actions
→ Taoyuan Weather
→ Run workflow

Workflow 參數
input_date

指定預報日期。

例如：

2026-09-25


留空：

使用台灣當天日期


程式會使用：

Asia/Taipei


時區取得日期。

input_locations

指定要處理的桃園行政區。

例如：

桃園區


或：

桃園區,中壢區,龜山區


留空：

桃園市 13 行政區全部處理


未知的行政區名稱會被忽略。

如果最後沒有任何有效行政區，程式會直接停止並回報錯誤。

send_telegram

控制是否推送 Telegram。

設定：

true


代表：

取得 CWA 資料
+
解析資料
+
符合降雨門檻時推送 Telegram


設定：

false


代表：

取得 CWA 資料
+
解析資料
+
輸出 GitHub Actions Log


但：

不推送 Telegram

Telegram 推播流程

程式執行後會依照以下流程：

CWA API
   ↓
取得 F-D0047-005
   ↓
取得 F-D0047-007
   ↓
解析桃園各行政區
   ↓
檢查降雨機率
   ↓
是否有任一筆 >= 70%？
   ↓
 ┌───────────────┐
 │               │
否               是
 │               │
 ↓               ↓
不推播          建立訊息
                 ↓
          只保留 >= 70%
                 ↓
          Telegram 推播

3 小時預報

F-D0047-005 用於建立逐 3 小時資料。

例如 CWA 資料：

09:00  40%
12:00  70%
15:00  80%
18:00  60%


Telegram 只會顯示：

12:00～15:00｜短暫雨｜降雨70%
15:00～18:00｜雨｜降雨80%

7 天預報

F-D0047-007 用於建立逐日資料。

例如：

2026-09-25  40%
2026-09-26  70%
2026-09-27  80%
2026-09-28  50%


Telegram 只會顯示：

2026-09-26 週六｜短暫雨｜降雨70%
2026-09-27 週日｜雨｜降雨80%

本機測試
系統需求

Node.js：

22 以上


本專案使用 Node.js 內建：

fetch()


因此不需要：

axios
node-fetch


等 runtime dependency。

安裝
npm ci

一般執行
CWA_API_KEY="你的KEY" \
TELEGRAM_BOT_TOKEN="你的TOKEN" \
TELEGRAM_CHAT_ID="你的CHAT_ID" \
npm run weather

只測試 CWA、不推 Telegram
CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
npm run weather


此模式會：

呼叫 CWA API

解析資料

顯示資料摘要

顯示 Telegram 預覽相關 Log

不實際傳送 Telegram

指定日期

例如：

CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
INPUT_DATE="2026-09-25" \
npm run weather

指定行政區

例如：

CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
INPUT_LOCATIONS="桃園區,中壢區,龜山區" \
npm run weather

指定日期 + 指定行政區
CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
INPUT_DATE="2026-09-25" \
INPUT_LOCATIONS="桃園區,中壢區,龜山區" \
npm run weather

專案結構
taoyuan-weather/
├── .github/
│   └── workflows/
│       └── weather.yml
├── src/
│   ├── districts.js
│   └── weather.js
├── .gitignore
├── README.md
├── package.json
└── package-lock.json

主要檔案
src/weather.js

主要天氣處理程式。

負責：

CWA API 呼叫

CWA JSON 解析

桃園行政區篩選

3 小時預報整理

7 天預報整理

降雨機率門檻判斷

Telegram 訊息建立

Telegram 推播

目前降雨門檻：

const POP_THRESHOLD =
  70;


判斷方式：

pop >= POP_THRESHOLD


因此 70% 會被視為符合條件。

src/districts.js

桃園市 13 行政區設定。

用於：

行政區名稱

行政區資料

API 資料篩選

INPUT_LOCATIONS 驗證

.github/workflows/weather.yml

GitHub Actions 工作流程。

負責：

排程執行

手動執行

傳入 Workflow Inputs

設定 GitHub Secrets

安裝 Node.js

執行 npm run weather

Telegram 長訊息

Telegram 單則訊息有長度限制。

本專案會在約：

3500 字元


的位置進行保守分割。

因此即使同一次推播包含大量行政區與預報資料，也會自動分成多則 Telegram 訊息。

Node.js Dependency

本專案使用 Node.js 內建：

fetch()


因此不需要：

axios
node-fetch


等 runtime dependency。

package-lock.json 仍建議提交到 GitHub，讓 GitHub Actions 可以使用：

npm ci

注意事項
1. CWA API Key

請勿直接把 CWA API Key 寫入：

weather.js


或：

weather.yml


建議使用 GitHub Secrets。

2. Telegram Token

請勿將：

TELEGRAM_BOT_TOKEN


提交到 GitHub Repository。

應使用：

GitHub Secrets

3. 降雨機率不是降雨量

本專案使用的是：

降雨機率（Probability of Precipitation）


不是：

降雨量 mm


例如：

降雨機率 70%


代表預報資料中的降雨機率達到 70%，並不代表一定會下 70 mm 的雨。

版本
v2.2.0

主要修改：

修正原本 F-D0047-093 HTTP 404 問題

改用 F-D0047-005

改用 F-D0047-007

3 天逐 3 小時資料改由 F-D0047-005 取得

7 天逐日資料改由 F-D0047-007 取得

兩個 CWA 資料集分開取得後再整合

新增降雨機率 >= 70% 推播門檻

只有任一行政區、任一時段達 70% 才觸發 Telegram

Telegram 只顯示降雨機率 >= 70% 的資料

70% 本身會顯示在 Telegram

所有資料低於 70% 時不推播

沒有符合條件的行政區不顯示

避免產生空的 Telegram 推播

資料來源

中央氣象署（CWA）

本專案的天氣資料來自中央氣象署公開資料服務。

License

本專案依 Repository 實際設定的 License 為準。
