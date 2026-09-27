#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌤 Taoyuan Weather

桃園市 13 行政區天氣預報

資料來源：
- CWA F-D0047-005：未來 3 天逐 3 小時
- CWA F-D0047-007：未來 1 週逐日

功能：
- 桃園市 13 行政區
- INPUT_DATE 指定預報日期
- INPUT_LOCATIONS 指定行政區
- SEND_TELEGRAM 控制 Telegram
- 降雨機率 >= 70% 才推播
- Telegram 只顯示 >= 70% 的資料
- Telegram 長訊息自動分割
- 無符合資料時不發送 Telegram

Environment Variables:
    CWA_API_KEY
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
    INPUT_DATE
    INPUT_LOCATIONS
    SEND_TELEGRAM
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


# ============================================================
# 設定
# ============================================================

CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

DATASET_3DAY = "F-D0047-005"
DATASET_7DAY = "F-D0047-007"

POP_THRESHOLD = 70

TELEGRAM_MAX_LENGTH = 3500

TAIWAN_TZ = ZoneInfo("Asia/Taipei")


# ============================================================
# 桃園 13 行政區
# ============================================================

DISTRICTS = [
    "桃園區",
    "中壢區",
    "龜山區",
    "八德區",
    "蘆竹區",
    "大園區",
    "觀音區",
    "新屋區",
    "楊梅區",
    "平鎮區",
    "復興區",
    "龍潭區",
    "大溪區",
]


# ============================================================
# 基本工具
# ============================================================

def log(message: str = "") -> None:
    """輸出 GitHub Actions Log。"""
    print(message, flush=True)


def get_bool_env(name: str, default: bool = False) -> bool:
    """取得 Boolean 環境變數。"""

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
        "on",
    }


def get_api_key() -> str:
    """取得 CWA API Key。"""

    value = os.getenv("CWA_API_KEY", "").strip()

    if not value:
        raise RuntimeError(
            "找不到 CWA_API_KEY。"
        )

    return value


def get_input_date() -> str:
    """
    INPUT_DATE 留空時，
    使用 Asia/Taipei 當天日期。
    """

    value = os.getenv("INPUT_DATE", "").strip()

    if not value:
        return datetime.now(
            TAIWAN_TZ
        ).strftime("%Y-%m-%d")

    try:
        datetime.strptime(
            value,
            "%Y-%m-%d",
        )
    except ValueError:
        raise ValueError(
            "INPUT_DATE 格式錯誤，"
            "請使用 YYYY-MM-DD，例如 2026-09-25"
        )

    return value


def get_locations() -> list[str]:
    """
    取得 INPUT_LOCATIONS。

    留空：
        使用全部 13 行政區。

    指定：
        桃園區,中壢區,龜山區

    未知行政區：
        忽略。

    最後沒有有效行政區：
        直接錯誤。
    """

    value = os.getenv(
        "INPUT_LOCATIONS",
        "",
    ).strip()

    if not value:
        return DISTRICTS.copy()

    locations = []

    for item in value.split(","):

        district = item.strip()

        if not district:
            continue

        if district in DISTRICTS:

            if district not in locations:
                locations.append(district)

        else:
            log(
                f"⚠️ 忽略未知行政區：{district}"
            )

    if not locations:
        raise ValueError(
            "INPUT_LOCATIONS 沒有任何有效行政區。"
        )

    return locations


def parse_number(value):
    """將 CWA 數值轉成 int。"""

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()

    if not text:
        return None

    text = (
        text
        .replace("%", "")
        .replace("％", "")
        .strip()
    )

    try:
        return int(float(text))
    except ValueError:
        return None


def parse_datetime(value: str):
    """解析 CWA ISO 日期時間。"""

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).astimezone(TAIWAN_TZ)

    except ValueError:
        return None


# ============================================================
# CWA API
# ============================================================

def fetch_dataset(
    dataset_id: str,
    api_key: str,
) -> dict:
    """取得 CWA Dataset。"""

    url = (
        f"{CWA_BASE_URL}/{dataset_id}"
    )

    params = {
        "Authorization": api_key,
        "format": "JSON",
    }

    log(
        f"🌐 CWA API：{dataset_id}"
    )

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    log(
        f"HTTP {response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    if data.get("success") is False:
        raise RuntimeError(
            f"CWA API 回傳失敗：{data}"
        )

    return data


# ============================================================
# CWA 結構解析
# ============================================================

def get_locations_from_records(
    records,
) -> list[dict]:
    """
    相容 CWA Locations 結構。
    """

    if not isinstance(records, dict):
        return []

    locations = records.get("Locations")

    if isinstance(locations, list):

        result = []

        for group in locations:

            if not isinstance(group, dict):
                continue

            items = group.get("Location")

            if isinstance(items, list):
                result.extend(items)

            elif isinstance(items, dict):
                result.append(items)

        return result

    locations = records.get("locations")

    if isinstance(locations, list):
        return locations

    return []


def get_location_list(
    data: dict,
) -> list[dict]:
    """取得行政區資料。"""

    records = data.get("records")

    if not isinstance(records, dict):
        return []

    return get_locations_from_records(records)


def get_location_name(
    location: dict,
) -> str:
    """取得行政區名稱。"""

    return str(
        location.get("LocationName")
        or location.get("locationName")
        or ""
    ).strip()


def get_weather_elements(
    location: dict,
) -> list[dict]:
    """取得 WeatherElement。"""

    elements = (
        location.get("WeatherElement")
        or location.get("weatherElement")
        or []
    )

    if isinstance(elements, dict):
        return [elements]

    if isinstance(elements, list):
        return elements

    return []


def get_element_name(
    element: dict,
) -> str:
    return str(
        element.get("ElementName")
        or element.get("elementName")
        or ""
    ).strip()


def find_element(
    location: dict,
    names: list[str],
) -> dict | None:
    """依 ElementName 找資料。"""

    elements = get_weather_elements(
        location
    )

    for element in elements:

        name = get_element_name(element)

        if name in names:
            return element

    return None


def get_times(
    element: dict | None,
) -> list[dict]:
    """取得 WeatherElement 的 Time。"""

    if not element:
        return []

    times = (
        element.get("Time")
        or element.get("time")
        or []
    )

    if isinstance(times, dict):
        return [times]

    if isinstance(times, list):
        return times

    return []


def get_element_value(
    time_item: dict,
):
    """
    取得 ElementValue。

    CWA 可能是：
        ElementValue
        elementValue
    """

    value = (
        time_item.get("ElementValue")
        or time_item.get("elementValue")
        or []
    )

    if isinstance(value, list):

        if not value:
            return {}

        return value[0]

    if isinstance(value, dict):
        return value

    return {}


# ============================================================
# 降雨機率
# ============================================================

def get_pop_from_value(
    value: dict,
) -> int | None:
    """從 ElementValue 取得降雨機率。"""

    if not isinstance(value, dict):
        return None

    candidates = [
        "ProbabilityOfPrecipitation",
        "PoP",
        "POP",
        "Value",
        "value",
    ]

    for key in candidates:

        if key not in value:
            continue

        number = parse_number(
            value[key]
        )

        if number is not None:
            return number

    return None


# ============================================================
# 天氣描述
# ============================================================

def get_weather_from_value(
    value: dict,
) -> str:
    """取得天氣描述。"""

    if not isinstance(value, dict):
        return ""

    candidates = [
        "Weather",
        "weather",
        "WeatherDescription",
        "weatherDescription",
        "Value",
        "value",
    ]

    for key in candidates:

        if key not in value:
            continue

        result = value[key]

        if result is None:
            continue

        text = str(result).strip()

        if text:
            return text

    return ""


# ============================================================
# 3 天逐 3 小時
# ============================================================

def parse_3day_location(
    location: dict,
) -> list[dict]:
    """
    F-D0047-005。

    只保留：
        PoP >= 70
    """

    district = get_location_name(
        location
    )

    if not district:
        return []

    pop_element = find_element(
        location,
        [
            "PoP6h",
            "PoP",
            "ProbabilityOfPrecipitation",
        ],
    )

    weather_element = find_element(
        location,
        [
            "Wx",
            "WeatherDescription",
        ],
    )

    if not pop_element:
        return []

    pop_times = get_times(
        pop_element
    )

    weather_times = get_times(
        weather_element
    )

    result = []

    for index, item in enumerate(
        pop_times
    ):

        start = (
            item.get("StartTime")
            or item.get("startTime")
            or ""
        )

        end = (
            item.get("EndTime")
            or item.get("endTime")
            or ""
        )

        value = get_element_value(
            item
        )

        pop = get_pop_from_value(
            value
        )

        if pop is None:
            continue

        if pop < POP_THRESHOLD:
            continue

        weather = ""

        if index < len(weather_times):

            weather_value = (
                get_element_value(
                    weather_times[index]
                )
            )

            weather = (
                get_weather_from_value(
                    weather_value
                )
            )

        result.append(
            {
                "district": district,
                "start": start,
                "end": end,
                "weather": weather or "降雨",
                "pop": pop,
            }
        )

    return result


# ============================================================
# 7 天逐日
# ============================================================

def parse_7day_location(
    location: dict,
) -> list[dict]:
    """
    F-D0047-007。

    只保留：
        PoP >= 70
    """

    district = get_location_name(
        location
    )

    if not district:
        return []

    pop_element = find_element(
        location,
        [
            "PoP12h",
            "PoP",
            "ProbabilityOfPrecipitation",
        ],
    )

    weather_element = find_element(
        location,
        [
            "Wx",
            "WeatherDescription",
        ],
    )

    if not pop_element:
        return []

    pop_times = get_times(
        pop_element
    )

    weather_times = get_times(
        weather_element
    )

    result = []

    for index, item in enumerate(
        pop_times
    ):

        start = (
            item.get("StartTime")
            or item.get("startTime")
            or ""
        )

        end = (
            item.get("EndTime")
            or item.get("endTime")
            or ""
        )

        value = get_element_value(
            item
        )

        pop = get_pop_from_value(
            value
        )

        if pop is None:
            continue

        if pop < POP_THRESHOLD:
            continue

        weather = ""

        if index < len(weather_times):

            weather_value = (
                get_element_value(
                    weather_times[index]
                )
            )

            weather = (
                get_weather_from_value(
                    weather_value
                )
            )

        result.append(
            {
                "district": district,
                "start": start,
                "end": end,
                "weather": weather or "降雨",
                "pop": pop,
            }
        )

    return result


# ============================================================
# 日期 / 時間格式
# ============================================================

def format_time_range(
    start: str,
    end: str,
) -> str:
    """格式化 3 小時區間。"""

    start_dt = parse_datetime(start)
    end_dt = parse_datetime(end)

    if start_dt and end_dt:

        return (
            f"{start_dt.strftime('%H:%M')}"
            f"～"
            f"{end_dt.strftime('%H:%M')}"
        )

    return (
        f"{start[-5:] if start else ''}"
        f"～"
        f"{end[-5:] if end else ''}"
    )


def format_daily_date(
    value: str,
) -> str:
    """格式化每日日期。"""

    weekdays = [
        "週一",
        "週二",
        "週三",
        "週四",
        "週五",
        "週六",
        "週日",
    ]

    dt = parse_datetime(value)

    if not dt:
        return value[:10]

    return (
        f"{dt.strftime('%Y-%m-%d')} "
        f"{weekdays[dt.weekday()]}"
    )


# ============================================================
# Telegram 訊息
# ============================================================

def build_message(
    input_date: str,
    districts: list[str],
    hourly_data: list[dict],
    daily_data: list[dict],
) -> str | None:
    """建立 Telegram 訊息。"""

    if not hourly_data and not daily_data:
        return None

    lines = [
        "🌤 桃園市降雨預報",
        f"📅 預報日期：{input_date}",
        f"🌧 降雨機率門檻：{POP_THRESHOLD}%",
        "",
    ]

    for district in districts:

        hourly = [
            item
            for item in hourly_data
            if item["district"] == district
        ]

        daily = [
            item
            for item in daily_data
            if item["district"] == district
        ]

        if not hourly and not daily:
            continue

        lines.append(
            f"📍 {district}"
        )

        if hourly:

            lines.append(
                "【未來3天・逐3小時】"
            )

            for item in hourly:

                time_range = format_time_range(
                    item["start"],
                    item["end"],
                )

                lines.append(
                    f"{time_range}"
                    f"｜{item['weather']}"
                    f"｜降雨{item['pop']}%"
                )

        if daily:

            lines.append(
                "【未來7天・逐日】"
            )

            for item in daily:

                date_text = format_daily_date(
                    item["start"]
                )

                lines.append(
                    f"{date_text}"
                    f"｜{item['weather']}"
                    f"｜降雨{item['pop']}%"
                )

        lines.append("")

    message = "\n".join(lines).strip()

    return message or None


def split_message(
    message: str,
) -> list[str]:
    """
    Telegram 長訊息分割。

    優先依換行切割。
    """

    if len(message) <= TELEGRAM_MAX_LENGTH:
        return [message]

    chunks = []
    current = ""

    for line in message.splitlines():

        candidate = (
            f"{current}\n{line}"
            if current
            else line
        )

        if len(candidate) <= TELEGRAM_MAX_LENGTH:

            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(line) <= TELEGRAM_MAX_LENGTH:

            current = line

        else:

            while len(line) > TELEGRAM_MAX_LENGTH:

                chunks.append(
                    line[:TELEGRAM_MAX_LENGTH]
                )

                line = line[
                    TELEGRAM_MAX_LENGTH:
                ]

            current = line

    if current:
        chunks.append(current)

    return chunks


# ============================================================
# Telegram API
# ============================================================

def send_telegram(
    message: str,
) -> None:
    """發送 Telegram。"""

    bot_token = os.getenv(
        "TELEGRAM_BOT_TOKEN",
        "",
    ).strip()

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID",
        "",
    ).strip()

    if not bot_token:
        raise RuntimeError(
            "找不到 TELEGRAM_BOT_TOKEN。"
        )

    if not chat_id:
        raise RuntimeError(
            "找不到 TELEGRAM_CHAT_ID。"
        )

    url = (
        "https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    chunks = split_message(message)

    log(
        f"📨 Telegram 將發送 {len(chunks)} 則訊息"
    )

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": chunk,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API 錯誤：{data}"
            )

        log(
            f"✅ Telegram "
            f"{index}/{len(chunks)} 發送完成"
        )


# ============================================================
# 主程式
# ============================================================

def main() -> int:

    log("=" * 60)
    log("🌤 Taoyuan Weather")
    log("=" * 60)

    try:

        api_key = get_api_key()

        input_date = get_input_date()

        districts = get_locations()

        send_telegram_enabled = (
            get_bool_env(
                "SEND_TELEGRAM",
                True,
            )
        )

        log(
            f"📅 預報日期：{input_date}"
        )

        log(
            "📍 行政區："
            + ", ".join(districts)
        )

        log(
            f"🌧 降雨門檻："
            f"{POP_THRESHOLD}%"
        )

        log(
            "📨 Telegram："
            + (
                "啟用"
                if send_telegram_enabled
                else "停用"
            )
        )

        # ----------------------------------------------------
        # 取得 3 天資料
        # ----------------------------------------------------

        data_3day = fetch_dataset(
            DATASET_3DAY,
            api_key,
        )

        locations_3day = (
            get_location_list(
                data_3day
            )
        )

        log(
            f"📊 F-D0047-005 "
            f"行政區數："
            f"{len(locations_3day)}"
        )

        hourly_data = []

        for location in locations_3day:

            district = get_location_name(
                location
            )

            if district not in districts:
                continue

            hourly_data.extend(
                parse_3day_location(
                    location
                )
            )

        # ----------------------------------------------------
        # 取得 7 天資料
        # ----------------------------------------------------

        data_7day = fetch_dataset(
            DATASET_7DAY,
            api_key,
        )

        locations_7day = (
            get_location_list(
                data_7day
            )
        )

        log(
            f"📊 F-D0047-007 "
            f"行政區數："
            f"{len(locations_7day)}"
        )

        daily_data = []

        for location in locations_7day:

            district = get_location_name(
                location
            )

            if district not in districts:
                continue

            daily_data.extend(
                parse_7day_location(
                    location
                )
            )

        # ----------------------------------------------------
        # 結果
        # ----------------------------------------------------

        log("")
        log("=" * 60)
        log("📊 結果")
        log("=" * 60)

        log(
            f"3 小時符合 >= "
            f"{POP_THRESHOLD}%："
            f"{len(hourly_data)} 筆"
        )

        log(
            f"7 天符合 >= "
            f"{POP_THRESHOLD}%："
            f"{len(daily_data)} 筆"
        )

        total = (
            len(hourly_data)
            + len(daily_data)
        )

        # ----------------------------------------------------
        # 沒有達門檻
        # ----------------------------------------------------

        if total == 0:

            log("")
            log(
                f"☀️ 沒有任何降雨機率 "
                f">= {POP_THRESHOLD}%"
            )

            log(
                "📨 不發送 Telegram"
            )

            return 0

        # ----------------------------------------------------
        # 建立訊息
        # ----------------------------------------------------

        message = build_message(
            input_date=input_date,
            districts=districts,
            hourly_data=hourly_data,
            daily_data=daily_data,
        )

        if not message:

            log(
                "⚠️ 無法建立 Telegram 訊息"
            )

            return 0

        log("")
        log("=" * 60)
        log("📨 Telegram 預覽")
        log("=" * 60)
        log(message)
        log("=" * 60)

        # ----------------------------------------------------
        # Telegram
        # ----------------------------------------------------

        if send_telegram_enabled:

            send_telegram(message)

        else:

            log(
                "ℹ️ SEND_TELEGRAM=false"
            )

            log(
                "ℹ️ 僅輸出預覽，不發送 Telegram"
            )

        log("")
        log("✅ Weather 完成")

        return 0

    except requests.RequestException as error:

        log("")
        log("❌ CWA / Telegram HTTP 錯誤")
        log(str(error))

        return 1

    except Exception as error:

        log("")
        log("❌ 執行失敗")
        log(
            f"{type(error).__name__}: {error}"
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())
