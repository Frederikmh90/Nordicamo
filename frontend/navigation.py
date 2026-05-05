"""Navigation labels and route keys for the Streamlit shell."""

TOPBAR_NAV_ITEMS = [
    ("Platform", "Nordicamo"),
    ("Countries", "Explorer"),
    ("Request Access", "GetAccess"),
]

ALLOWED_PAGES = {"Nordicamo", "Explorer", "Media", "About", "GetAccess"}

LEGACY_PAGE_ALIASES = {
    "Platform": "Nordicamo",
    "Countries": "Explorer",
    "Request Access": "GetAccess",
    "Full Data Access": "GetAccess",
}
