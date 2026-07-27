# MOCK ADAPTER — no production credentials available.
# Production swap: a sanctions/PEP screening vendor (OFAC / UN / MAS lists).
from .. import demo_world


def screen(names: list[str]) -> list[str]:
    """Return the subset of names that hit the (synthetic) sanctions lists."""
    listed = {n.lower() for n in demo_world.SANCTIONS_LIST}
    return [n for n in names if n.lower() in listed]
