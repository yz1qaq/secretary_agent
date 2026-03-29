from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE = "Asia/Shanghai"

WEEKDAY_LABELS = {
    1: "星期一",
    2: "星期二",
    3: "星期三",
    4: "星期四",
    5: "星期五",
    6: "星期六",
    7: "星期日",
}


def resolve_timezone(timezone: str | None = None) -> str:
    candidate = timezone or DEFAULT_TIMEZONE
    try:
        ZoneInfo(candidate)
        return candidate
    except ZoneInfoNotFoundError:
        return DEFAULT_TIMEZONE


def get_current_datetime_payload(timezone: str | None = None) -> dict[str, str]:
    resolved_timezone = resolve_timezone(timezone)
    now = datetime.now(ZoneInfo(resolved_timezone))
    tomorrow = now + timedelta(days=1)

    weekday = WEEKDAY_LABELS[now.isoweekday()]
    tomorrow_weekday = WEEKDAY_LABELS[tomorrow.isoweekday()]

    return {
        "iso_datetime": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M:%S"),
        "weekday": weekday,
        "timezone": resolved_timezone,
        "display_text": f"{now.year}年{now.month}月{now.day}日 {weekday} {now.strftime('%H:%M:%S')}",
        "tomorrow_date": tomorrow.date().isoformat(),
        "tomorrow_weekday": tomorrow_weekday,
    }


def build_time_context_text(timezone: str | None = None) -> str:
    payload = get_current_datetime_payload(timezone)
    return (
        "以下是当前时间上下文，请你在本次对话中严格以此为准：\n"
        f"- 当前时区：{payload['timezone']}\n"
        f"- 当前日期：{payload['date']}\n"
        f"- 当前时间：{payload['time']}\n"
        f"- 今天星期：{payload['weekday']}\n"
        f"- 当前显示时间：{payload['display_text']}\n"
        f"- 明天日期：{payload['tomorrow_date']}\n"
        f"- 明天星期：{payload['tomorrow_weekday']}\n"
        "涉及“现在几点 / 今天几号 / 今天星期几 / 明天是周几 / 今天 / 明天 / 本周”等时间相关判断时，"
        "必须以这份时间上下文或时间工具结果为准，不能凭记忆猜测。"
    )
