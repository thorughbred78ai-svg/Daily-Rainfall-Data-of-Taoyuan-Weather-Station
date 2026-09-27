# -🌤 Taoyuan Weather

桃園市 13 行政區天氣預報 GitHub Actions 專案。

本專案使用中央氣象署（CWA）公開資料，取得桃園市未來 3 天及未來 1 週天氣預報，並依照降雨機率門檻決定是否透過 Telegram Bot 推播。

目前版本

v2.3.0

功能

桃園市 13 行政區天氣預報

未來 3 天預報

未來 3 天逐時段降雨機率

未來 7 天逐日預報

使用中央氣象署 CWA API

使用 CWA F-D0047-005

使用 CWA F-D0047-007

Telegram Bot 推播

GitHub Actions 自動執行

GitHub Actions 手動執行

可指定預報日期

可指定行政區

可設定是否推送 Telegram

Telegram 長訊息自動分割

降雨機率達門檻才進行 Telegram 推播

Python 3.12

使用 requests 呼叫 API

🌧️ 降雨推播規則

本專案目前的降雨推播門檻：

降雨機率 >= 70%


判斷方式：

pop >= 70


因此 70% 本身會觸發推播。

推播規則
降雨機率	Telegram 推播	Telegram 顯示
0% ～ 69%	❌	❌
70%	✅	✅
71% ～ 100%	✅	✅

例如：

60% → 不推播、不顯示
69% → 不推播、不顯示
70% → 推播、顯示
80% → 推播、顯示
100% → 推播、顯示

觸發條件

只要：

任一行政區
+
任一預報時段
+
降雨機率 >= 70%


就會觸發整次 Telegram 推播。

📱 Telegram 訊息內容

Telegram 只會顯示降雨機率 >= 70% 的資料。

例如 CWA 資料：

09:00  40%
12:00  70%
15:00  80%
18:00  60%


Telegram 只顯示：

12:00～15:00｜短暫雨｜降雨70%
15:00～18:00｜雨｜降雨80%


其中：

70%


會保留在 Telegram 訊息中。

如果所有行政區、所有預報資料都低於 70%：

不發送 Telegram


也不會產生只有標題的空訊息。

🗺️ 桃園 13 行政區

本專案處理以下桃園市行政區：

桃園區
中壢區
龜山區
八德區
蘆竹區
大園區
觀音區
新屋區
楊梅區
平鎮區
復興區
龍潭區
大溪區

🌦️ CWA 資料集

本專案使用中央氣象署桃園市專屬資料集。

未來 3 天
F-D0047-005


用途：

桃園市未來 3 天天氣預報


主要用於取得較短時間尺度的預報資料。

未來 1 週
F-D0047-007


用途：

桃園市未來 1 週天氣預報


主要用於建立逐日預報資料。

已停止使用

本專案不再使用：

F-D0047-093


目前使用：

F-D0047-005
+
F-D0047-007


兩個資料集分別呼叫 CWA API，再於 Python 程式中整理資料。

📂 專案結構
Daily-Rainfall-Data-of-Taoyuan-Weather-Station/
│
├── .github/
│   └── workflows/
│       └── weather.yml
│
├── scripts/
│   └── weather.py
│
├── requirements.txt
│
├── README.md
│
└── .gitignore

🐍 Python

本專案目前使用：

Python 3.12


GitHub Actions 使用：

python-version: "3.12"


Python 程式：

scripts/weather.py

📦 Python Dependency

本專案使用：

requests


安裝依賴：

python -m pip install -r requirements.txt


requirements.txt：

requests>=2.31,<3

🔐 GitHub Secrets

進入：

Repository
→ Settings
→ Secrets and variables
→ Actions


建立以下 Repository Secrets：

CWA_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

🔑 CWA_API_KEY

中央氣象署 Open Data API 金鑰。

請勿直接寫入：

scripts/weather.py


也不要寫入：

.github/workflows/weather.yml


應使用：

GitHub Secrets

🤖 TELEGRAM_BOT_TOKEN

Telegram Bot Token。

請勿直接提交到 GitHub Repository。

應使用：

GitHub Secrets

💬 TELEGRAM_CHAT_ID

Telegram Bot 接收訊息的 Chat ID。

同樣建議使用：

GitHub Secrets

⚙️ GitHub Actions

Workflow：

.github/workflows/weather.yml


Workflow 名稱：

Taoyuan Weather


GitHub Actions 支援：

自動排程

手動執行

指定日期

指定行政區

控制 Telegram 推播

⏰ 自動排程

目前 Workflow：

schedule:
  - cron: "0 * * * *"


代表：

每小時執行一次


GitHub Actions 的 cron 使用 UTC。

因此：

00:00 UTC = 台灣 08:00
01:00 UTC = 台灣 09:00
02:00 UTC = 台灣 10:00
...


程式本身使用：

Asia/Taipei


處理預報日期。

▶️ 手動執行

進入：

GitHub Repository
→ Actions
→ Taoyuan Weather
→ Run workflow


可以設定：

input_date
input_locations
send_telegram

📅 input_date

指定預報日期。

例如：

2026-09-25


格式：

YYYY-MM-DD


例如：

2026-09-25


如果留空：

使用 Asia/Taipei 當天日期


程式會使用：

datetime.now(ZoneInfo("Asia/Taipei"))


取得日期。

📍 input_locations

指定要處理的桃園行政區。

例如：

桃園區


或：

桃園區,中壢區,龜山區


也可以指定多個：

桃園區,中壢區,龜山區,八德區,蘆竹區


如果留空：

桃園市 13 行政區全部處理

⚠️ 未知行政區

例如：

桃園區,台北市,中壢區


程式會：

桃園區 → 有效
台北市 → 忽略
中壢區 → 有效


GitHub Actions Log 會顯示：

⚠️ 忽略未知行政區：台北市


如果最後完全沒有有效行政區：

程式直接停止

📲 send_telegram

控制是否發送 Telegram。

true

設定：

send_telegram = true


代表：

取得 CWA 資料
      ↓
解析資料
      ↓
檢查降雨機率
      ↓
有 >= 70%
      ↓
建立 Telegram 訊息
      ↓
發送 Telegram

false

設定：

send_telegram = false


代表：

取得 CWA 資料
      ↓
解析資料
      ↓
檢查降雨機率
      ↓
輸出 GitHub Actions Log
      ↓
不發送 Telegram


這個模式適合測試。

🧪 建議第一次測試方式

第一次執行 GitHub Actions 時，建議：

input_date：

留空

input_locations：

留空

send_telegram：

false


這樣可以先確認：

CWA API
↓
資料取得
↓
資料解析
↓
13 行政區
↓
降雨機率
↓
Telegram 預覽


確認 Log 正常後，再設定：

send_telegram = true

💻 本機測試
系統需求
Python 3.10+


建議：

Python 3.12

📦 安裝套件

進入 Repository：

cd Daily-Rainfall-Data-of-Taoyuan-Weather-Station


安裝：

python -m pip install -r requirements.txt

▶️ 一般執行

Linux / macOS：

CWA_API_KEY="你的KEY" \
TELEGRAM_BOT_TOKEN="你的TOKEN" \
TELEGRAM_CHAT_ID="你的CHAT_ID" \
python scripts/weather.py

🧪 只測試 CWA，不發 Telegram
CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
python scripts/weather.py


程式會：

呼叫 CWA API
↓
取得資料
↓
解析資料
↓
檢查降雨機率
↓
輸出 Telegram 預覽


但不會真的發送 Telegram。

📅 指定日期

例如：

CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
INPUT_DATE="2026-09-25" \
python scripts/weather.py

📍 指定行政區

例如：

CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
INPUT_LOCATIONS="桃園區,中壢區,龜山區" \
python scripts/weather.py

📅📍 指定日期 + 行政區
CWA_API_KEY="你的KEY" \
SEND_TELEGRAM=false \
INPUT_DATE="2026-09-25" \
INPUT_LOCATIONS="桃園區,中壢區,龜山區" \
python scripts/weather.py

📱 Telegram 推播流程

完整流程：

                CWA API
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   F-D0047-005       F-D0047-007
    未來 3 天           未來 7 天
          │                 │
          └────────┬────────┘
                   ▼
            Python 解析資料
                   │
                   ▼
             桃園 13 行政區
                   │
                   ▼
             檢查降雨機率
                   │
                   ▼
             是否 >= 70%？
              /          \
            否            是
            │              │
            ▼              ▼
        不推播        建立訊息
                           │
                           ▼
                    只保留 >= 70%
                           │
                           ▼
                   Telegram Bot

🌧️ 3 小時資料

F-D0047-005 用於建立短時間尺度的降雨資料。

例如：

09:00～12:00｜降雨40%
12:00～15:00｜降雨70%
15:00～18:00｜降雨80%
18:00～21:00｜降雨60%


Telegram 只顯示：

12:00～15:00｜短暫雨｜降雨70%
15:00～18:00｜雨｜降雨80%

📆 7 天資料

F-D0047-007 用於建立逐日資料。

例如：

2026-09-25｜降雨40%
2026-09-26｜降雨70%
2026-09-27｜降雨80%
2026-09-28｜降雨50%


Telegram 只顯示：

2026-09-26 週六｜短暫雨｜降雨70%
2026-09-27 週日｜雨｜降雨80%

✂️ Telegram 長訊息

Telegram 單則訊息有長度限制。

本專案採用約：

3500 字元


作為保守分割長度。

當一次推播包含大量：

行政區
+
3 天資料
+
7 天資料


程式會自動分割成多則 Telegram 訊息。

🔒 安全注意事項
1. CWA API Key

不要把：

CWA_API_KEY


直接寫入 Python 程式。

不要提交：

CWA_API_KEY="..."


到 GitHub。

2. Telegram Bot Token

不要把：

TELEGRAM_BOT_TOKEN


提交到 Repository。

3. Telegram Chat ID

建議同樣使用 GitHub Secrets。

📄 requirements.txt

目前只有：

requests>=2.31,<3


安裝：

python -m pip install -r requirements.txt

📄 主要檔案
scripts/weather.py

主要負責：

CWA API 呼叫

F-D0047-005 資料取得

F-D0047-007 資料取得

CWA JSON 解析

桃園行政區篩選

3 天資料整理

7 天資料整理

降雨機率判斷

Telegram 訊息建立

Telegram 長訊息分割

Telegram 推播

目前門檻：

POP_THRESHOLD = 70


判斷：

pop >= POP_THRESHOLD


因此：

70% → 符合
71% → 符合
80% → 符合
100% → 符合
69% → 不符合

.github/workflows/weather.yml

負責：

GitHub Actions

自動排程

手動執行

Python 3.12

安裝 requirements

GitHub Secrets

Workflow Inputs

執行 scripts/weather.py

requirements.txt

Python runtime dependency：

requests

🛠️ 常見錯誤
ModuleNotFoundError: No module named 'requests'

代表沒有安裝 Python dependency。

執行：

python -m pip install -r requirements.txt


GitHub Actions 則會自動執行：

python -m pip install -r requirements.txt

CWA_API_KEY 不存在

確認：

Repository
→ Settings
→ Secrets and variables
→ Actions


是否存在：

CWA_API_KEY

TELEGRAM_BOT_TOKEN 不存在

確認：

TELEGRAM_BOT_TOKEN


是否設定。

TELEGRAM_CHAT_ID 不存在

確認：

TELEGRAM_CHAT_ID


是否設定。

所有資料都低於 70%

這不是錯誤。

程式會：

所有降雨機率 < 70%
↓
不建立推播訊息
↓
不發送 Telegram


GitHub Actions Job 仍會正常完成。

🔎 降雨機率說明

本專案使用的是：

降雨機率
Probability of Precipitation


不是：

降雨量 mm


例如：

降雨機率 70%


代表預報資料中的降雨機率達到 70%。

並不代表：

會下 70 mm 的雨


兩者是不同的天氣資訊。

📊 資料流程
CWA F-D0047-005
        │
        ▼
未來 3 天資料
        │
        ├── 桃園區
        ├── 中壢區
        ├── 龜山區
        ├── 八德區
        ├── 蘆竹區
        ├── 大園區
        ├── 觀音區
        ├── 新屋區
        ├── 楊梅區
        ├── 平鎮區
        ├── 復興區
        ├── 龍潭區
        └── 大溪區

CWA F-D0047-007
        │
        ▼
未來 7 天資料
        │
        └── 桃園 13 行政區

                ↓

         Python 整合資料

                ↓

       檢查降雨機率 >= 70%

                ↓

       ┌────────┴────────┐
       │                 │
      否                 是
       │                 │
       ▼                 ▼
    不推播          建立 Telegram
                         │
                         ▼
                  只保留 >= 70%
                         │
                         ▼
                    Telegram Bot

📝 版本
v2.3.0

主要修改：

Python 版本正式化

修正 scripts/weather.py

新增 requirements.txt

GitHub Actions 改用 Python 3.12

GitHub Actions 自動安裝 Python dependencies

使用 requests

使用 F-D0047-005

使用 F-D0047-007

停止使用 F-D0047-093

新增降雨機率 >= 70% 推播門檻

70% 本身會觸發推播

Telegram 只顯示 >= 70%

所有資料低於 70% 時不推播

支援指定日期

支援指定行政區

支援 send_telegram

Telegram 長訊息自動分割

使用 Asia/Taipei 處理台灣日期與時間

📡 資料來源

本專案天氣資料來自：

中央氣象署（CWA）公開資料服務

使用資料集：

F-D0047-005
F-D0047-007

📜 License

本專案依 Repository 實際設定的 License 為準。

:::

這份 README 已經和目前的 **Python 版檔案結構、`requests`、Python 3.12、`python scripts/weather.py`、70% 門檻、GitHub Actions Inputs/Secrets** 對齊，可以直接放進 Repository。

