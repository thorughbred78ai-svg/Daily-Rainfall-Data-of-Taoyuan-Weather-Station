# -
地面測站每日雨量資料

🌧️ 桃園地面測站每日雨量

使用 GitHub Actions 定時取得中央氣象署（CWA）地面測站每日雨量資料，並透過 Telegram Bot 發送通知。

本專案將原本 n8n Workflow 改為 GitHub Actions + Python，不需要維持 n8n 伺服器常駐。

功能

每 8 小時自動執行一次

使用台灣時區 Asia/Taipei

取得前一天的地面測站雨量資料

使用中央氣象署 Open Data API

支援指定桃園地區測站

透過 Telegram Bot 發送每日雨量

雨量達 350 mm 以上時額外發送警報

支援 GitHub Actions 手動執行

手動執行時可以指定測站

T（Trace，微量降雨）視為 0 mm

不需要 n8n

不需要自行維護伺服器

專案結構
.
├── .github/
│   └── workflows/
│       └── weather.yml
│
├── scripts/
│   └── weather.py
│
└── README.md

使用資料來源

本專案使用中央氣象署 Open Data API：

https://opendata.cwa.gov.tw/api/v1/rest/datastore/C-B0025-001


資料集：

C-B0025-001


主要使用：

DataType=stationObsTimes


查詢前一天的資料。

自動排程

GitHub Actions 使用：

on:
  schedule:
    - cron: "0 0,8,16 * * *"
      timezone: "Asia/Taipei"


因此排程時間為台灣時間：

台灣時間	執行
00:00	✅
08:00	✅
16:00	✅
其他時間	-

時區使用：

Asia/Taipei


不需要自行將台灣時間轉換成 UTC。

GitHub Actions 的排程可能因 GitHub 平台負載而產生些微延遲，因此不保證精確到秒。

查詢測站

目前設定的測站如下：

大溪永福

中大臨海站

觀音工業區

八德蔬果

新興坑尾

國二E009K

國一高架N063K

國三N072K

國三N063K

國一S072K

西濱S032K

中央大學

茶改場

東眼山

蘆竹

新屋

復興

八德

大溪

平鎮

楊梅

龍潭

龜山

竹圍

中德

水尾

四稜

桃園

觀音

中壢

預設 Telegram 查詢測站

自動排程預設發送：

新屋
八德
蘆竹
龜山
中壢


也就是：

DEFAULT_STATIONS = [
    "新屋",
    "八德",
    "蘆竹",
    "龜山",
    "中壢",
]


如果要修改自動通知的測站，可以修改：

scripts/weather.py


中的：

DEFAULT_STATIONS

🔐 GitHub Secrets

本專案需要三個 GitHub Secrets。

進入：

Repository
    ↓
Settings
    ↓
Secrets and variables
    ↓
Actions
    ↓
New repository secret


建立以下三個 Secret：

CWA_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

1. CWA_API_KEY

中央氣象署 Open Data API 授權碼。

Secret 名稱：

CWA_API_KEY


內容填入你的 CWA API Key。

例如：

CWA_API_KEY
└── CWA API 授權碼


不要直接把 API Key 寫在：

weather.py


或：

weather.yml


裡面。

2. TELEGRAM_BOT_TOKEN

Telegram Bot Token。

Secret 名稱：

TELEGRAM_BOT_TOKEN


例如：

123456789:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


不要把 Bot Token 提交到 Git。

3. TELEGRAM_CHAT_ID

Telegram 接收通知的 Chat ID。

Secret 名稱：

TELEGRAM_CHAT_ID


例如：

8683161103


建議同樣使用 GitHub Secret 保存，不要直接寫死在 Python 程式裡。

🤖 Telegram Bot

需要先建立一個 Telegram Bot。

取得 Bot Token 後，設定：

TELEGRAM_BOT_TOKEN


然後取得接收通知的 Chat ID：

TELEGRAM_CHAT_ID


完成後，GitHub Actions 就可以透過 Telegram Bot 發送訊息。

🌧️ 每日雨量通知

GitHub Actions 執行後會：

GitHub Actions
      │
      ▼
取得台灣目前日期
      │
      ▼
計算前一天日期
      │
      ▼
CWA API
      │
      ▼
C-B0025-001
      │
      ▼
篩選指定測站
      │
      ▼
產生雨量訊息
      │
      ▼
Telegram


例如：

🌧 降雨量資訊
📅 日期：2026-09-24

查詢測站：新屋、八德、蘆竹、龜山、中壢

📍 新屋
英文名稱：Xinwu
測站編號：467050
測站類型：署屬有人氣象站
🌧 降雨量：12.0 mm
────────────────

📍 八德
🌧 降雨量：8.0 mm
────────────────

📍 蘆竹
🌧 降雨量：15.5 mm
────────────────

📍 龜山
🌧 降雨量：3.0 mm
────────────────

📍 中壢
測站編號：C0C700
🌧 降雨量：4.0 mm
────────────────

📊 已取得 5 / 5 個測站資料

🚨 350 mm 雨量警報

本專案設定：

RAIN_THRESHOLD = 350.0


如果任何指定測站的前一天雨量達到：

350 mm


以上，就會額外發送 Telegram 警報。

例如：

🌧️ 桃園雨量警報

⚠️ 2026-09-24 累積雨量達 350 mm 以上

📍 測站：八德
📅 日期：2026-09-24
🌧️ 雨量：351 mm

📍 測站：龜山
📅 日期：2026-09-24
🌧️ 雨量：370.5 mm


如果沒有任何測站達到 350 mm：

ℹ️ 沒有測站達到 350 mm


不會另外發送警報訊息。

🌧️ T 雨量值

中央氣象署資料中的：

T


代表 Trace，也就是微量降雨。

程式會將：

T


視為：

0 mm


例如：

{
  "Precipitation": "T"
}


會轉換為：

0.0 mm

▶️ 手動執行

除了自動排程，也可以從 GitHub 手動執行。

進入：

GitHub Repository
    ↓
Actions
    ↓
桃園地面測站每日雨量
    ↓
Run workflow


可以在：

stations


輸入測站。

例如：

新屋,八德,蘆竹,龜山,中壢


也支援：

新屋、八德、蘆竹


或者：

新屋 八德 蘆竹


程式會自動解析。

🧪 測試

第一次建立完成後，建議先手動執行。

進入：

Actions
    ↓
桃園地面測站每日雨量
    ↓
Run workflow


使用：

新屋,八德,蘆竹,龜山,中壢


執行後可以查看：

Actions
    ↓
Workflow Run
    ↓
Run weather bot


如果正常，Log 會看到類似：

========================================
桃園地面測站每日雨量
========================================

現在時間：2026-09-25T08:00:00+08:00
查詢日期：2026-09-24

查詢測站：新屋、八德、蘆竹、龜山、中壢

CWA 回傳目標測站資料：5 筆

✅ 一般雨量訊息已發送
ℹ️ 沒有測站達到 350 mm

完成。

🔒 安全性

請勿將以下資料直接寫入 Git：

CWA API Key
Telegram Bot Token
Telegram Chat ID


錯誤示範：

CWA_API_KEY = "xxxxxxxxxxxxxxxx"


或：

TELEGRAM_BOT_TOKEN: "123456789:xxxxxxxx"


正確方式是使用 GitHub Secrets：

env:
  CWA_API_KEY: ${{ secrets.CWA_API_KEY }}
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

🛠️ 修改雨量警報門檻

預設：

RAIN_THRESHOLD = 350.0


如果需要改成 200 mm：

RAIN_THRESHOLD = 200.0


改成 500 mm：

RAIN_THRESHOLD = 500.0

🛠️ 修改自動通知測站

修改：

DEFAULT_STATIONS = [
    "新屋",
    "八德",
    "蘆竹",
    "龜山",
    "中壢",
]


例如改成：

DEFAULT_STATIONS = [
    "新屋",
    "中壢",
    "楊梅",
    "龍潭",
]

🛠️ 修改執行時間

目前：

schedule:
  - cron: "0 0,8,16 * * *"
    timezone: "Asia/Taipei"


代表：

台灣時間 00:00
台灣時間 08:00
台灣時間 16:00


例如每天 06:00 執行：

schedule:
  - cron: "0 6 * * *"
    timezone: "Asia/Taipei"


每天 06:00、12:00、18:00 執行：

schedule:
  - cron: "0 6,12,18 * * *"
    timezone: "Asia/Taipei"

⚠️ GitHub Actions 排程注意事項

GitHub Actions 的 schedule 不是保證精準執行時間的服務。

即使設定：

cron: "0 8 * * *"
timezone: "Asia/Taipei"


實際執行仍可能因 GitHub Actions 平台負載而稍微延遲。

因此本專案適合：

每日資料取得

每數小時資料更新

雨量通知

一般自動化任務

如果需求是：

精確到秒

高頻率執行

24 小時即時 Telegram Bot

Telegram 即時指令

則建議使用常駐服務，而不是單純依賴 GitHub Actions。

📱 Telegram 即時查詢的限制

原本 n8n Workflow 有：

Telegram Trigger
       ↓
使用者輸入
       ↓
判斷測站
       ↓
查詢資料
       ↓
Telegram 回覆


GitHub Actions 則是：

Schedule
   ↓
執行 Python
   ↓
結束


因此 GitHub Actions 本身不會一直等待 Telegram 訊息。

目前版本將原本 Telegram Trigger 的功能改為：

GitHub Actions
      ↓
Run workflow
      ↓
輸入測站
      ↓
查詢 CWA
      ↓
Telegram 回覆


如果需要真正保留：

使用者 → Telegram Bot → 即時查詢 → Telegram 回覆


需要另外建立 Telegram Bot Webhook 或常駐 Bot 服務。

📁 主要檔案
.github/workflows/weather.yml

負責：

GitHub Actions 排程

Asia/Taipei 台灣時區

手動執行

GitHub Secrets

啟動 Python

scripts/weather.py

負責：

CWA API

前一天日期計算

測站篩選

雨量解析

Telegram 訊息

350 mm 警報

手動測站輸入

📌 GitHub Secrets 清單

完成設定後應該有：

Settings
└── Secrets and variables
    └── Actions
        ├── CWA_API_KEY
        ├── TELEGRAM_BOT_TOKEN
        └── TELEGRAM_CHAT_ID

📌 最終執行架構
                    GitHub Actions
                         │
            ┌────────────┴────────────┐
            │                         │
      Schedule                  workflow_dispatch
            │                         │
    Asia/Taipei                手動指定測站
            │                         │
            └────────────┬────────────┘
                         │
                         ▼
                  scripts/weather.py
                         │
                         ▼
                計算台灣昨日日期
                         │
                         ▼
                       CWA
                         │
                         ▼
                  C-B0025-001
                         │
                         ▼
                    篩選測站
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
          每日雨量               >= 350 mm
              │                     │
              ▼                     ▼
          Telegram              Telegram
             通知                  警報

📜 License

此專案主要用於個人自動化與氣象資料通知。

中央氣象署資料之使用與授權，請依中央氣象署 Open Data 相關規範辦理。
