from datetime import date, timedelta
from .settings import settings


def easter_sunday(year: int) -> date:
    """Gregorian computus (Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def holidays_for_year(year: int) -> set[date]:
    fixed = {(1, 1), (1, 25), (4, 21), (5, 1), (7, 9), (9, 7),
             (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)}
    result = {date(year, month, day) for month, day in fixed}
    easter = easter_sunday(year)
    result.add(easter - timedelta(days=2))  
    result.add(easter + timedelta(days=60)) 
    for raw in settings.business_holidays.split(","):
        try:
            custom = date.fromisoformat(raw.strip())
        except ValueError:
            continue
        if custom.year == year:
            result.add(custom)
    return result


def is_business_day(day: date) -> bool:
    return day.weekday() < 5 and day not in holidays_for_year(day.year)
