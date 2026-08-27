from fastapi import Header, Query


def get_language(
    x_language: str | None = Header(None, alias="X-Language"),
    language: str | None = Query(None),
) -> str:
    lang = x_language or language or "EN"
    return lang.upper() if lang.upper() in ("EN", "FR") else "EN"
