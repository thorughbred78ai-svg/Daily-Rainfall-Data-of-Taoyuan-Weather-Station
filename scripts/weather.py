#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌤 Taoyuan Weather

桃園市 13 行政區天氣預報

功能：
- CWA F-D0047-005：未來 3 天逐 3 小時預報
- CWA F-D0047-007：未來 1 週逐日預報
- 桃園市 13 行政區
- 降雨機率 >= 70% 才觸發 Telegram
- Telegram 只顯示 >= 70% 的資料
- 支援 INPUT_DATE
- 支援 INPUT_LOCATIONS
- 支援 SEND_TELEGRAM
- Telegram 長訊息自動分割
- 使用 Python requests

環境變數：

CWA_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

INPUT_DATE
例如：
2026-09-25

INPUT_LOCATIONS
例如：
桃園區,中壢區,龜山區

SEND_TELEGRAM
true / false

Python：
3.10+
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


# ============================================================
# 設定
# ============================================================

POP_THRESHOLD = 70

CWA_3DAY_DATASET = "F-D0047-005"
CWA_7DAY_DATASET = "F-D0047-007"

CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

TELEGRAM_MAX_LENGTH = 3500


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
# 工具
# ============================================================

def log(message: str) -> None:
    """輸出 GitHub Actions Log。"""
    print(message, flush=True)


def get_env_bool(name: str, default: bool = False) -> bool:
    """取得 boolean 環境變數。"""

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


def get_input_date() -> str:
    """
    取得指定日期。

    INPUT_DATE 留空：
    使用 Asia/Taipei 當天日期。
    """

    value = os.getenv("INPUT_DATE", "").strip()

    if not value:
        return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"INPUT_DATE 格式錯誤：{value}，應為 YYYY-MM-DD"
        )

    return value


def get_input_locations() -> list[str]:
    """
    取得指定行政區。

    留空：
    使用全部 13 行政區。

    未知行政區：
    忽略。

    如果最後沒有有效行政區：
    直接停止。
    """

    value = os.getenv("INPUT_LOCATIONS", "").strip()

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
            log(f"⚠️ 忽略未知行政區：{district}")

    if not locations:
        raise ValueError(
            "INPUT_LOCATIONS 沒有任何有效的桃園行政區。"
        )

    return locations


def safe_int(value):
    """安全轉換整數。"""

    if value is None:
        return None

    if isinstance(value, int):
        return value

    text = str(value).strip()

    if not text:
        return None

    text = (
        text.replace("%", "")
        .replace("％", "")
        .strip()
    )

    try:
        return int(float(text))
    except ValueError:
        return None


def format_pop(value) -> str:
    """格式化降雨機率。"""

    number = safe_int(value)

    if number is None:
        return "?"

    return f"{number}%"


def get_pop(value) -> int | None:
    """取得降雨機率整數。"""

    return safe_int(value)


def split_telegram_message(
    message: str,
    max_length: int = TELEGRAM_MAX_LENGTH,
) -> list[str]:
    """
    Telegram 長訊息分割。

    優先以換行分割，
    避免切斷天氣資料。
    """

    if len(message) <= max_length:
        return [message]

    chunks = []
    current = ""

    for line in message.splitlines(keepends=True):

        if len(current) + len(line) <= max_length:
            current += line
            continue

        if current:
            chunks.append(current.rstrip())
            current = ""

        # 單行本身超過限制
        while len(line) > max_length:
            chunks.append(line[:max_length])
            line = line[max_length:]

        current = line

    if current:
        chunks.append(current.rstrip())

    return chunks


# ============================================================
# CWA API
# ============================================================

def get_cwa_api_key() -> str:
    """取得 CWA API Key。"""

    api_key = os.getenv("CWA_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "找不到 CWA_API_KEY，請設定環境變數或 GitHub Secret。"
        )

    return api_key


def fetch_cwa_dataset(
    dataset_id: str,
    api_key: str,
) -> dict:
    """
    呼叫 CWA API。
    """

    url = f"{CWA_BASE_URL}/{dataset_id}"

    params = {
        "Authorization": api_key,
        "format": "JSON",
    }

    log(f"🌐 呼叫 CWA Dataset：{dataset_id}")

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    log(
        f"HTTP {response.status_code} "
        f"- {dataset_id}"
    )

    response.raise_for_status()

    data = response.json()

    success = data.get("success")

    if success is False:
        raise RuntimeError(
            f"CWA API 回傳失敗：{data}"
        )

    return data


# ============================================================
# CWA JSON 解析
# ============================================================

def extract_locations(data: dict) -> list[dict]:
    """
    取得 CWA locations。

    CWA 資料結構可能因資料集版本略有不同，
    因此這裡做多種格式相容。
    """

    records = data.get("records", {})

    if isinstance(records, list):
        return records

    if not isinstance(records, dict):
        return []

    locations = records.get("Locations")

    if isinstance(locations, list):
        result = []

        for item in locations:
            if not isinstance(item, dict):
                continue

            if "Location" in item:
                location = item["Location"]

                if isinstance(location, list):
                    result.extend(location)

                elif isinstance(location, dict):
                    result.append(location)

            else:
                result.append(item)

        return result

    locations = records.get("locations")

    if isinstance(locations, list):
        return locations

    return []


def extract_location_name(location: dict) -> str:
    """
    取得行政區名稱。
    """

    return (
        location.get("LocationName")
        or location.get("locationName")
        or location.get("Name")
        or ""
    ).strip()


def extract_weather_elements(location: dict) -> list[dict]:
    """
    取得 weather element。
    """

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


def element_name(element: dict) -> str:
    return (
        element.get("ElementName")
        or element.get("elementName")
        or element.get("Name")
        or ""
    ).strip()


def find_element(
    location: dict,
    names: list[str],
) -> dict | None:
    """
    找尋指定 WeatherElement。
    """

    elements = extract_weather_elements(location)

    for element in elements:
        name = element_name(element)

        for target in names:
            if name == target:
                return element

    return None


def extract_times(element: dict) -> list[dict]:
    """
    取得 Time。
    """

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


def extract_value(value):
    """
    CWA Value 相容處理。
    """

    if isinstance(value, dict):
        for key in (
            "value",
            "Value",
            "百分比",
            "ProbabilityOfPrecipitation",
        ):
            if key in value:
                return value[key]

        return None

    return value


# ============================================================
# 3 小時資料
# ============================================================

def parse_3day_location(location: dict) -> list[dict]:
    """
    解析 F-D0047-005。
    """

    result = []

    district = extract_location_name(location)

    if not district:
        return result

    pop_element = find_element(
        location,
        [
            "PoP6h",
            "PoP",
            "ProbabilityOfPrecipitation",
            "降雨機率",
        ],
    )

    weather_element = find_element(
        location,
        [
            "Wx",
            "WeatherDescription",
            "天氣現象",
            "天氣預報綜合描述",
        ],
    )

    if not pop_element:
        return result

    pop_times = extract_times(pop_element)
    weather_times = (
        extract_times(weather_element)
        if weather_element
        else []
    )

    for index, time_data in enumerate(pop_times):

        start_time = (
            time_data.get("StartTime")
            or time_data.get("startTime")
            or ""
        )

        end_time = (
            time_data.get("EndTime")
            or time_data.get("endTime")
            or ""
        )

        value = (
            time_data.get("ElementValue")
            or time_data.get("elementValue")
            or time_data.get("Value")
            or time_data.get("value")
        )

        if isinstance(value, list) and value:
            value = value[0]

        pop = None

        if isinstance(value, dict):
            pop = (
                value.get("ProbabilityOfPrecipitation")
                or value.get("PoP")
                or value.get("value")
                or value.get("Value")
            )
        else:
            pop = value

        pop = get_pop(pop)

        if pop is None:
            continue

        weather = ""

        if index < len(weather_times):

            weather_data = weather_times[index]

            weather_value = (
                weather_data.get("ElementValue")
                or weather_data.get("elementValue")
                or weather_data.get("Value")
                or weather_data.get("value")
            )

            if isinstance(weather_value, list) and weather_value:
                weather_value = weather_value[0]

            if isinstance(weather_value, dict):
                weather = (
                    weather_value.get("Weather")
                    or weather_value.get("weather")
                    or weather_value.get("value")
                    or weather_value.get("Value")
                    or ""
                )
            elif weather_value is not None:
                weather = str(weather_value)

        if pop < POP_THRESHOLD:
            continue

        result.append(
            {
                "district": district,
                "start": start_time,
                "end": end_time,
                "weather": weather or "降雨",
                "pop": pop,
            }
        )

    return result


def format_time_range(
    start: str,
    end: str,
) -> str:
    """
    將 CWA 時間格式轉成：

    12:00～15:00
    """

    def format_one(value: str) -> str:

        if not value:
            return ""

        try:
            dt = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            return dt.astimezone(
                TAIPEI_TZ
            ).strftime("%H:%M")

        except Exception:
            return value[-5:] if len(value) >= 5 else value

    start_text = format_one(start)
    end_text = format_one(end)

    if start_text and end_text:
        return f"{start_text}～{end_text}"

    return start_text or end_text


# ============================================================
# 7 天資料
# ============================================================

def parse_7day_location(location: dict) -> list[dict]:
    """
    解析 F-D0047-007。

    只保留 >= 70% 的資料。
    """

    result = []

    district = extract_location_name(location)

    if not district:
        return result

    pop_element = find_element(
        location,
        [
            "PoP12h",
            "PoP",
            "ProbabilityOfPrecipitation",
            "降雨機率",
        ],
    )

    weather_element = find_element(
        location,
        [
            "Wx",
            "WeatherDescription",
            "天氣現象",
            "天氣預報綜合描述",
        ],
    )

    if not pop_element:
        return result

    pop_times = extract_times(pop_element)

    weather_times = (
        extract_times(weather_element)
        if weather_element
        else []
    )

    for index, time_data in enumerate(pop_times):

        start_time = (
            time_data.get("StartTime")
            or time_data.get("startTime")
            or ""
        )

        end_time = (
            time_data.get("EndTime")
            or time_data.get("endTime")
            or ""
        )

        value = (
            time_data.get("ElementValue")
            or time_data.get("elementValue")
            or time_data.get("Value")
            or time_data.get("value")
        )

        if isinstance(value, list) and value:
            value = value[0]

        pop = None

        if isinstance(value, dict):
            pop = (
                value.get("ProbabilityOfPrecipitation")
                or value.get("PoP")
                or value.get("value")
                or value.get("Value")
            )
        else:
            pop = value

        pop = get_pop(pop)

        if pop is None:
            continue

        if pop < POP_THRESHOLD:
            continue

        weather = ""

        if index < len(weather_times):

            weather_data = weather_times[index]

            weather_value = (
                weather_data.get("ElementValue")
                or weather_data.get("elementValue")
                or weather_data.get("Value")
                or weather_data.get("value")
            )

            if isinstance(weather_value, list) and weather_value:
                weather_value = weather_value[0]

            if isinstance(weather_value, dict):
                weather = (
                    weather_value.get("Weather")
                    or weather_value.get("weather")
                    or weather_value.get("value")
                    or weather_value.get("Value")
                    or ""
                )
            elif weather_value is not None:
                weather = str(weather_value)

        result.append(
            {
                "district": district,
                "start": start_time,
                "end": end_time,
                "weather": weather or "降雨",
                "pop": pop,
            }
        )

    return result


# ============================================================
# Telegram 訊息
# ============================================================

def build_message(
    input_date: str,
    selected_districts: list[str],
    hourly_data: list[dict],
    daily_data: list[dict],
) -> str | None:
    """
    建立 Telegram 訊息。

    如果所有資料都 < 70%，
    回傳 None。
    """

    if not hourly_data and not daily_data:
        return None

    lines = []

    lines.append("🌤 桃園市降雨預報")
    lines.append(
        f"📅 預報日期：{input_date}"
    )
    lines.append(
        f"🌧 降雨機率門檻：{POP_THRESHOLD}%"
    )
    lines.append("")

    for district in selected_districts:

        district_hourly = [
            item
            for item in hourly_data
            if item["district"] == district
        ]

        district_daily = [
            item
            for item in daily_data
            if item["district"] == district
        ]

        if not district_hourly and not district_daily:
            continue

        lines.append(f"📍 {district}")

        if district_hourly:

            lines.append("")
            lines.append("【未來3天・逐3小時】")

            for item in district_hourly:

                time_range = format_time_range(
                    item["start"],
                    item["end"],
                )

                lines.append(
                    f"{time_range}"
                    f"｜{item['weather']}"
                    f"｜降雨{item['pop']}%"
                )

        if district_daily:

            lines.append("")
            lines.append("【未來7天・逐日】")

            for item in district_daily:

                date_text = format_date_with_weekday(
                    item["start"]
                )

                lines.append(
                    f"{date_text}"
                    f"｜{item['weather']}"
                    f"｜降雨{item['pop']}%"
                )

        lines.append("")

    message = "\n".join(lines).strip()

    if not message:
        return None

    return message


def format_date_with_weekday(value: str) -> str:
    """
    日期格式：

    2026-09-27 週日
    """

    weekdays = [
        "週一",
        "週二",
        "週三",
        "週四",
        "週五",
        "週六",
        "週日",
    ]

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        dt = dt.astimezone(TAIPEI_TZ)

        return (
            f"{dt.strftime('%Y-%m-%d')} "
            f"{weekdays[dt.weekday()]}"
        )

    except Exception:

        if len(value) >= 10:
            return value[:10]

        return value


# ============================================================
# Telegram
# ============================================================

def send_telegram_message(
    message: str,
) -> None:
    """
    傳送 Telegram。

    Telegram 訊息會自動分割。
    """

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
        f"https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    chunks = split_telegram_message(message)

    log(
        f"📨 Telegram 訊息共 {len(chunks)} 則"
    )

    for index, chunk in enumerate(chunks, start=1):

        payload = {
            "chat_id": chat_id,
            "text": chunk,
        }

        response = requests.post(
            url,
            json=payload,
            timeout=30,
        )

        log(
            f"Telegram {index}/{len(chunks)} "
            f"HTTP {response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API 失敗：{data}"
            )


# ============================================================
# 主程式
# ============================================================

def main() -> int:

    log("=" * 60)
    log("🌤 Taoyuan Weather")
    log("=" * 60)

    try:

        input_date = get_input_date()

        selected_districts = (
            get_input_locations()
        )

        send_telegram = get_env_bool(
            "SEND_TELEGRAM",
            default=True,
        )

        api_key = get_cwa_api_key()

        log(f"📅 INPUT_DATE：{input_date}")

        log(
            "📍 行政區："
            + ", ".join(selected_districts)
        )

        log(
            f"📨 SEND_TELEGRAM："
            f"{send_telegram}"
        )

        log(
            f"🌧 降雨門檻："
            f"{POP_THRESHOLD}%"
        )

        # ----------------------------------------------------
        # F-D0047-005
        # ----------------------------------------------------

        data_3day = fetch_cwa_dataset(
            CWA_3DAY_DATASET,
            api_key,
        )

        locations_3day = extract_locations(
            data_3day
        )

        log(
            f"📊 F-D0047-005 行政區資料："
            f"{len(locations_3day)}"
        )

        hourly_data = []

        for location in locations_3day:

            district = extract_location_name(
                location
            )

            if district not in selected_districts:
                continue

            items = parse_3day_location(
                location
            )

            hourly_data.extend(items)

        # ----------------------------------------------------
        # F-D0047-007
        # ----------------------------------------------------

        data_7day = fetch_cwa_dataset(
            CWA_7DAY_DATASET,
            api_key,
        )

        locations_7day = extract_locations(
            data_7day
        )

        log(
            f"📊 F-D0047-007 行政區資料："
            f"{len(locations_7day)}"
        )

        daily_data = []

        for location in locations_7day:

            district = extract_location_name(
                location
            )

            if district not in selected_districts:
                continue

            items = parse_7day_location(
                location
            )

            daily_data.extend(items)

        # ----------------------------------------------------
        # 統計
        # ----------------------------------------------------

        log("")
        log("=" * 60)
        log("📊 降雨門檻檢查")
        log("=" * 60)

        log(
            f"3 小時符合資料："
            f"{len(hourly_data)}"
        )

        log(
            f"7 天符合資料："
            f"{len(daily_data)}"
        )

        total = (
            len(hourly_data)
            + len(daily_data)
        )

        if total == 0:

            log("")
            log(
                f"✅ 所有資料降雨機率 "
                f"< {POP_THRESHOLD}%"
            )

            log(
                "📨 不發送 Telegram"
            )

            return 0

        # ----------------------------------------------------
        # 建立 Telegram
        # ----------------------------------------------------

        message = build_message(
            input_date=input_date,
            selected_districts=selected_districts,
            hourly_data=hourly_data,
            daily_data=daily_data,
        )

        if not message:

            log(
                "ℹ️ 沒有符合條件的 Telegram 訊息"
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

        if send_telegram:

            log("📨 開始發送 Telegram...")

            send_telegram_message(
                message
            )

            log(
                "✅ Telegram 發送完成"
            )

        else:

            log(
                "ℹ️ SEND_TELEGRAM=false"
            )

            log(
                "ℹ️ 不實際發送 Telegram"
            )

        log("")
        log("✅ Weather job 完成")

        return 0

    except requests.RequestException as exc:

        log("")
        log("❌ HTTP Request 錯誤")
        log(str(exc))

        return 1

    except Exception as exc:

        log("")
        log("❌ 執行失敗")
        log(f"{type(exc).__name__}: {exc}")

        return 1


if __name__ == "__main__":
    sys.exit(main())

