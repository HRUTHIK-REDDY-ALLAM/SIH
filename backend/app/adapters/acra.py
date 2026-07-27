# MOCK ADAPTER — no production credentials available.
# Production swap: ACRA (Singapore business registry) entity search API plus a
# trade-credit bureau. Same interface; only the data source changes.
from .. import demo_world


def lookup_company(uen: str) -> dict | None:
    return demo_world.ACRA_COMPANIES.get(uen)
