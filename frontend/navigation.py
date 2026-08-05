"""Navigation labels and route keys for the Streamlit shell."""

TOPBAR_NAV_ITEMS = [
    ("Overview", "Explorer"),
    ("Research Workshop", "Workshop"),
    ("Browse Media", "Media"),
    ("About", "About"),
    ("Request Access", "GetAccess"),
]

ALLOWED_PAGES = {"Nordicamo", "Explorer", "Workshop", "Media", "About", "GetAccess"}

LEGACY_PAGE_ALIASES = {
    "Platform": "Nordicamo",
    "Countries": "Explorer",
    "Analysis": "Explorer",
    "Overview": "Explorer",
    "Browse Media": "Media",
    "About": "About",
    "Request Access": "GetAccess",
    "Full Data Access": "GetAccess",
}
