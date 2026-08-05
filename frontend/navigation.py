"""Navigation labels and route keys for the Streamlit shell."""

TOPBAR_NAV_ITEMS = [
    ("Platform", "Nordicamo"),
    ("Analysis", "Explorer"),
    ("Browse Media", "Media"),
    ("About", "About"),
    ("Request Access", "GetAccess"),
]

ALLOWED_PAGES = {"Nordicamo", "Explorer", "Workshop", "Media", "About", "GetAccess"}

LEGACY_PAGE_ALIASES = {
    "Platform": "Nordicamo",
    "Countries": "Explorer",
    "Analysis": "Explorer",
    "Browse Media": "Media",
    "About": "About",
    "Request Access": "GetAccess",
    "Full Data Access": "GetAccess",
}
