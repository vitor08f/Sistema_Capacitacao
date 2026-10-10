from datetime import date, timedelta

from .settings import configuracoes


def domingo_de_pascoa(ano: int) -> date:
    """Calcula o domingo de Páscoa pelo algoritmo gregoriano."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


def feriados_do_ano(ano: int) -> set[date]:
    fixos = {
        (1, 1), (1, 25), (4, 21), (5, 1), (7, 9), (9, 7),
        (10, 12), (11, 2), (11, 15), (11, 20), (12, 25),
    }
    feriados = {date(ano, mes, dia) for mes, dia in fixos}
    pascoa = domingo_de_pascoa(ano)
    feriados.add(pascoa - timedelta(days=2))
    feriados.add(pascoa + timedelta(days=60))
    for data_configurada in configuracoes.feriados_empresa.split(","):
        try:
            feriado = date.fromisoformat(data_configurada.strip())
        except ValueError:
            continue
        if feriado.year == ano:
            feriados.add(feriado)
    return feriados


def dia_de_expediente(data: date) -> bool:
    return data.weekday() < 5 and data not in feriados_do_ano(data.year)
