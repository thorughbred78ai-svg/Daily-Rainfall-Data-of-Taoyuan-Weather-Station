#!/usr/bin/env python3

import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# 設定
# ============================================================

CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/C-B0025-001"

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

RAIN_THRESHOLD = 350.0

DEFAULT_STATIONS = [
    "新屋",
    "八德",
    "蘆竹",
    "龜山",
    "中壢",
]

TARGET_STATIONS = [
    "大溪永福",
    "中大臨海站",
    "觀音工業區",
    "八德蔬果",
    "新興坑尾",
    "國二E009K",
    "國一高架N063K",
    "國三N072K",
    "國三N063K",
    "國一S072K",
    "西濱S032K",
    "中央大學",
    "茶改場",
    "東眼山",
    "蘆竹",
    "新屋",
    "復興",
    "八德",
    "大溪",
    "平鎮",
    "楊梅",
    "龍潭",
    "龜山",
    "竹圍",
    "中德",
    "水尾",
    "四稜",
    "桃園",
    "觀音",
    "中壢",
]


# ============================================================
# Telegram
# ============================================================

def telegram_send(chat_id: str, message: str):
    token = os.environ.get(
        "TELEGRAM_BOT_TOKEN",
        ""
    ).strip()

    if not token:
        raise RuntimeError(
            "缺少 TELEGRAM_BOT_TOKEN GitHub Secret"
        )

    if not chat_id:
        raise RuntimeError(
            "缺少 TELEGRAM_CHAT_ID GitHub Secret"
        )

    url = (
        f"https://api.telegram.org/bot{token}/sendMessage"
    )

    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {result}"
        )


# ============================================================
# CWA API
# ============================================================

def fetch_cwa_data(target_date: str):

    api_key = os.environ.get(
        "CWA_API_KEY",
        ""
    ).strip()

    if not api_key:
        raise RuntimeError(
            "缺少 CWA_API_KEY GitHub Secret"
        )

    params = {
        "format": "JSON",
        "DataType": "stationObsTimes",
        "timeFrom": target_date,
        "timeTo": target_date,
    }

    url = (
        CWA_API_URL
        + "?"
        + urllib.parse.urlencode(params)
    )

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": api_key,
            "User-Agent": "GitHubActions-WeatherBot/1.0",
        },
    )

    print(f"CWA URL: {CWA_API_URL}")
    print(f"查詢日期: {target_date}")

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:

        body = response.read().decode("utf-8")

    data = json.loads(body)

    if str(data.get("success")).lower() != "true":
        raise RuntimeError(
            f"CWA API 回傳錯誤: {data}"
        )

    return data


# ============================================================
# 解析 CWA 資料
# ============================================================

def parse_stations(data, target_date):

    locations = (
        data
        .get("records", {})
        .get("location", [])
    )

    results = []

    for location in locations:

        station = location.get(
            "station",
            {}
        )

        station_name = station.get(
            "StationName"
        )

        if station_name not in TARGET_STATIONS:
            continue

        obs_times = (
            location
            .get("stationObsTimes", {})
            .get("stationObsTime", [])
        )

        for obs in obs_times:

            date = obs.get("Date")

            if date != target_date:
                continue

            weather_elements = obs.get(
                "weatherElements",
                {}
            )

            raw = weather_elements.get(
                "Precipitation"
            )

            precipitation = parse_precipitation(
                raw
            )

            results.append({
                "StationID": station.get(
                    "StationID",
                    ""
                ),
                "StationName": station_name,
                "StationNameEN": station.get(
                    "StationNameEN",
                    ""
                ),
                "StationAttribute": station.get(
                    "StationAttribute",
                    ""
                ),
                "Date": date,
                "Precipitation": precipitation,
                "PrecipitationRaw": raw,
            })

    return results


# ============================================================
# 雨量轉數字
# ============================================================

def parse_precipitation(value):

    if value is None:
        return 0.0

    if value == "":
        return 0.0

    if str(value).upper() == "T":
        # Trace
        return 0.0

    try:
        return float(value)

    except (TypeError, ValueError):
        return 0.0


# ============================================================
# 格式化數字
# ============================================================

def format_mm(value):

    if value is None:
        return "0"

    value = float(value)

    if value.is_integer():
        return str(int(value))

    return f"{value:.1f}"


# ============================================================
# 產生一般雨量訊息
#
# 沒有對應氣象資料的測站：
#   - 不輸出
#
# 所有測站都沒有資料：
#   - 回傳 None
#   - main() 將不發送 Telegram
# ============================================================

def build_weather_message(
    results,
    requested_stations,
    target_date,
):

    # 建立測站名稱 → 資料的對照表
    result_map = {
        item["StationName"]: item
        for item in results
    }

    # --------------------------------------------------------
    # 只保留有資料的測站
    # --------------------------------------------------------

    available_results = [
        result_map[station_name]
        for station_name in requested_stations
        if station_name in result_map
    ]

    # --------------------------------------------------------
    # 如果全部測站都沒有資料
    # --------------------------------------------------------

    if not available_results:
        return None

    # --------------------------------------------------------
    # 開始建立訊息
    # --------------------------------------------------------

    lines = []

    lines.append("🌧 降雨量資訊")

    lines.append(
        f"📅 日期：{target_date}"
    )

    lines.append("")

    lines.append(
        "查詢測站："
        + "、".join(
            item["StationName"]
            for item in available_results
        )
    )

    lines.append("")

    # --------------------------------------------------------
    # 輸出有資料的測站
    # --------------------------------------------------------

    for data in available_results:

        lines.append(
            f"📍 {data['StationName']}"
        )

        if data.get("StationNameEN"):

            lines.append(
                f"英文名稱："
                f"{data['StationNameEN']}"
            )

        if data.get("StationID"):

            lines.append(
                f"測站編號："
                f"{data['StationID']}"
            )

        if data.get("StationAttribute"):

            lines.append(
                f"測站類型："
                f"{data['StationAttribute']}"
            )

        lines.append(
            f"🌧 降雨量："
            f"{format_mm(data['Precipitation'])} mm"
        )

        lines.append(
            "────────────────"
        )

    # --------------------------------------------------------
    # 統計
    # --------------------------------------------------------

    lines.append("")

    lines.append(
        f"📊 已取得 "
        f"{len(available_results)} / "
        f"{len(requested_stations)} "
        f"個測站資料"
    )

    return "\n".join(lines)


# ============================================================
# 產生 350 mm 警報
# ============================================================

def build_alert_message(
    results,
    target_date,
):

    triggered = [
        item
        for item in results
        if item["Precipitation"]
        >= RAIN_THRESHOLD
    ]

    if not triggered:
        return None

    lines = [
        "🌧️ 桃園雨量警報",
        "",
        (
            f"⚠️ {target_date} "
            f"累積雨量達 "
            f"{format_mm(RAIN_THRESHOLD)} mm 以上"
        ),
        "",
    ]

    for station in triggered:

        lines.append(
            f"📍 測站："
            f"{station['StationName']}"
        )

        lines.append(
            f"📅 日期："
            f"{station['Date']}"
        )

        lines.append(
            f"🌧️ 雨量："
            f"{format_mm(station['Precipitation'])} mm"
        )

        lines.append("")

    return "\n".join(lines)


# ============================================================
# 解析手動輸入測站
# ============================================================

def parse_requested_stations():

    # GitHub Actions workflow_dispatch
    # 會將輸入放在環境變數 REQUESTED_STATIONS

    value = os.environ.get(
        "REQUESTED_STATIONS",
        ""
    ).strip()

    # 沒有輸入 → 使用預設測站
    if not value:
        return DEFAULT_STATIONS

    # --------------------------------------------------------
    # 支援：
    #
    # 新屋,八德,蘆竹
    #
    # 新屋、八德、蘆竹
    #
    # 新屋 八德 蘆竹
    # --------------------------------------------------------

    value = value.replace(
        "、",
        ","
    )

    value = value.replace(
        "，",
        ","
    )

    value = value.replace(
        " ",
        ","
    )

    stations = [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]

    # --------------------------------------------------------
    # 只接受 TARGET_STATIONS
    # --------------------------------------------------------

    valid = [
        station
        for station in stations
        if station in TARGET_STATIONS
    ]

    return valid


# ============================================================
# 主程式
# ============================================================

def main():

    # --------------------------------------------------------
    # 台灣時間
    # --------------------------------------------------------

    now = datetime.now(
        TAIPEI_TZ
    )

    # --------------------------------------------------------
    # 查詢昨天
    # --------------------------------------------------------

    yesterday = (
        now - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    # --------------------------------------------------------
    # Telegram Chat ID
    # --------------------------------------------------------

    chat_id = os.environ.get(
        "TELEGRAM_CHAT_ID",
        ""
    ).strip()

    # --------------------------------------------------------
    # 解析指定測站
    # --------------------------------------------------------

    requested_stations = (
        parse_requested_stations()
    )

    # 如果使用者輸入了無效測站
    # 改回預設測站

    if not requested_stations:

        print(
            "⚠️ 沒有指定有效測站，"
            "改用預設測站。"
        )

        requested_stations = (
            DEFAULT_STATIONS
        )

    # --------------------------------------------------------
    # Console 標題
    # --------------------------------------------------------

    print(
        "========================================"
    )

    print(
        "桃園地面測站每日雨量"
    )

    print(
        "========================================"
    )

    print(
        f"現在時間：{now.isoformat()}"
    )

    print(
        f"查詢日期：{yesterday}"
    )

    print(
        "查詢測站："
        + "、".join(requested_stations)
    )

    print(
        "========================================"
    )

    # ========================================================
    # CWA
    # ========================================================

    data = fetch_cwa_data(
        yesterday
    )

    results = parse_stations(
        data,
        yesterday
    )

    print(
        f"CWA 回傳目標測站資料："
        f"{len(results)} 筆"
    )

    # ========================================================
    # 一般雨量訊息
    # ========================================================

    weather_message = (
        build_weather_message(
            results,
            requested_stations,
            yesterday,
        )
    )

    print("")

    if weather_message:

        print(weather_message)

    else:

        print(
            "⚠️ 所有指定測站皆「尚無對應氣象資料」。"
        )

    # ========================================================
    # Telegram 一般雨量訊息
    #
    # 只有至少一個測站有資料才發送
    # ========================================================

    if weather_message:

        telegram_send(
            chat_id,
            weather_message
        )

        print(
            "✅ 一般雨量訊息已發送"
        )

    else:

        print(
            "⚠️ 所有指定測站皆無氣象資料，"
            "略過 Telegram 一般雨量訊息。"
        )

    # ========================================================
    # 350 mm 警報
    #
    # 只有至少一個測站有資料才檢查
    # ========================================================

    if results:

        alert_message = (
            build_alert_message(
                results,
                yesterday,
            )
        )

        if alert_message:

            print("")
            print(alert_message)

            telegram_send(
                chat_id,
                alert_message
            )

            print(
                "🚨 350 mm 警報已發送"
            )

        else:

            print(
                "ℹ️ 沒有測站達到 "
                f"{format_mm(RAIN_THRESHOLD)} mm"
            )

    else:

        print(
            "⚠️ 所有指定測站皆無氣象資料，"
            "略過 350 mm 警報。"
        )

    # ========================================================
    # 完成
    # ========================================================

    print("")
    print("完成。")


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print(
            f"❌ 執行失敗：{exc}",
            file=sys.stderr
        )

        raise

