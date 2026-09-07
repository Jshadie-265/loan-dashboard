"""
ui_theme.py — Shared styling and theme helpers for Loan Manager.

Provides apply_common_styles() which injects global CSS to style:
1. Deploy button & toolbar: completely hidden.
2. Anti-flicker: disables stale opacity flashing (.stElementContainer dimming)
   and transition animations on page navigation, making transitions seamless.
3. Sidebar & icons: branded sidebar with icons on every option; when minimized,
   collapses into a single-column icon-only rail displaying ONLY the icons, with
   exactly ONE toggle button (>> to expand, << to collapse).
4. Tab buttons: prominent, highly visible, clickable segmented button controls
   (targeting Streamlit 1.63+ stTabs/stTab and react-aria tabs).
5. Cards, tables, forms, buttons: polished desktop styling.
"""

import streamlit as st

COMMON_CSS = """
<style>
/* ===================================================================
   0. HIDE DEPLOY BUTTON & DEVELOPER TOOLBAR
   =================================================================== */
[data-testid="stAppDeployButton"],
.stAppDeployButton,
button[data-testid="stAppDeployButton"],
div[data-testid="stToolbarActions"],
div[data-testid="stDecoration"] {
    display: none !important;
}


/* ===================================================================
   1. ANTI-FLICKER — COMPLETELY ELIMINATE OPACITY DROP & RELOAD FLASH
   =================================================================== */
/* Streamlit applies wu = { opacity: 0.33, transition: 'opacity ...' }
   to .stElementContainer whenever a script runs (such as on navigation).
   This dims every element into a washed-out ghost, creating a jarring
   flash/flicker that looks like a full-window reload.
   Forcing opacity: 1 and transition: none completely eliminates the flash. */
.stElementContainer,
[data-testid="stElementContainer"],
.element-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
.stApp [data-testid="stVerticalBlock"],
.stApp [data-testid="stHorizontalBlock"],
.stMain,
[data-testid="stMain"],
[data-testid="stLayoutWrapper"],
section[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stTabs"],
.stTabs {
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}

[data-testid="stElementContainer"] > *,
.stElementContainer > * {
    opacity: 1 !important;
    transition: none !important;
}

/* Hide the top-right running spinner/widget that pops in during reruns */
[data-testid="stStatusWidget"] {
    display: none !important;
    visibility: hidden !important;
}

/* Disable transitions on layout containers to prevent reflow jitter */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
.main {
    transition: none !important;
    animation: none !important;
}


/* ===================================================================
   2. TAB BUTTONS — PROMINENT, CLICKABLE, HIGH VISIBILITY
   =================================================================== */

/* Container wrapper for the tab group */
[data-testid="stTabs"],
.stTabs {
    margin-top: 0.6rem !important;
    margin-bottom: 1.5rem !important;
}

/* Tab bar track / segmented button bar */
[data-testid="stTabs"] [role="tablist"],
div[data-baseweb="tab-list"],
.stTabs [role="tablist"] {
    background-color: #ECE7DE !important;
    border-radius: 12px !important;
    padding: 6px !important;
    gap: 8px !important;
    border: 1.5px solid #D5CEBF !important;
    display: inline-flex !important;
    align-items: center !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.06) !important;
    width: auto !important;
    max-width: 100% !important;
}

/* Hide Streamlit's default thin underline indicator */
[data-testid="stTabs"] [role="tablist"]::after,
[data-testid="stTabs"] .react-aria-SelectionIndicator,
div[data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"] {
    display: none !important;
    opacity: 0 !important;
    height: 0 !important;
    width: 0 !important;
}

/* Base Tab Button — INACTIVE / UNSELECTED STATE */
[data-testid="stTab"],
button[data-testid="stTab"],
button[data-baseweb="tab"],
[role="tab"] {
    background-color: #FAF8F5 !important;
    color: #2D3732 !important;
    border: 1.5px solid #C8C1B3 !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    height: auto !important;
    min-height: 42px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    cursor: pointer !important;
    transition: all 0.16s ease-in-out !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    outline: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    text-decoration: none !important;
    letter-spacing: 0.01em !important;
}

/* Inactive Tab text styling */
[data-testid="stTab"] p,
[data-testid="stTab"] span,
[data-testid="stTab"] div,
button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span {
    color: #2D3732 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}

/* Tab button HOVER state */
[data-testid="stTab"]:hover,
button[data-testid="stTab"]:hover,
button[data-baseweb="tab"]:hover,
[role="tab"]:hover {
    background-color: #E2DBD0 !important;
    border-color: #146356 !important;
    color: #146356 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12) !important;
}

[data-testid="stTab"]:hover p,
[data-testid="stTab"]:hover span,
button[data-baseweb="tab"]:hover p,
button[data-baseweb="tab"]:hover span {
    color: #146356 !important;
}

/* ACTIVE / SELECTED TAB BUTTON — PROMINENT BRAND GREEN FILL */
[data-testid="stTab"][aria-selected="true"],
button[data-testid="stTab"][aria-selected="true"],
button[data-baseweb="tab"][aria-selected="true"],
[role="tab"][aria-selected="true"] {
    background-color: #146356 !important;
    border: 1.5px solid #146356 !important;
    color: #FFFFFF !important;
    box-shadow: 0 3px 10px rgba(20, 99, 86, 0.35) !important;
    transform: translateY(-1px) !important;
}

/* Crisp white bold text for selected tab */
[data-testid="stTab"][aria-selected="true"] p,
[data-testid="stTab"][aria-selected="true"] span,
[data-testid="stTab"][aria-selected="true"] div,
button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span,
button[data-baseweb="tab"][aria-selected="true"] div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}


/* ===================================================================
   3. SIDEBAR NAVIGATION & MINIMIZED ICON-ONLY RAIL
   =================================================================== */

/* Gradient background for sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F4F44 0%, #1A6B5A 45%, #EFEBE3 100%) !important;
    transition: none !important;
}

/* Expanded Sidebar Links */
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
    background-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 8px !important;
    margin: 3px 8px !important;
    padding: 10px 14px !important;
    transition: background-color 0.15s ease, border-color 0.15s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    display: flex !important;
    align-items: center !important;
}

section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
    background-color: rgba(255, 255, 255, 0.24) !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
}

/* Active sidebar link (expanded mode) */
section[data-testid="stSidebar"][aria-expanded="true"] a[data-testid="stSidebarNavLink"][aria-current="page"] {
    background-color: rgba(255, 255, 255, 0.32) !important;
    border-left: 4px solid #FFFFFF !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
}

/* Icon size inside sidebar links */
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span:first-child {
    font-size: 1.25rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Sidebar text is clean white */
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {
    color: #FFFFFF !important;
}

/* Collapse button — ALWAYS VISIBLE (override Streamlit's hover-only visibility) */
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    opacity: 1 !important;
}

/* Collapse button in expanded sidebar header (<<) — styled in white */
section[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarCollapseButton"] button {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarCollapseButton"] svg,
section[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarCollapseButton"] span {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}


/* --- MINIMIZED SIDEBAR: ICON-ONLY RAIL ---
   When the user collapses/minimizes the sidebar:
   1. Lock width to 68px without jitter.
   2. Keep stSidebarCollapseButton visible at the top of the rail, but ROTATE
      its button 180 degrees so << becomes >> (pointing right to expand!).
   3. Hide the outside stExpandSidebarButton in stHeader so there is only ever ONE button.
   4. Hide text labels and keep ONLY the icons visible and centered. */
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 68px !important;
    max-width: 68px !important;
    width: 68px !important;
    transform: none !important;
    margin-left: 0 !important;
    visibility: visible !important;
    transition: none !important;
}

/* Header container in collapsed state: center the toggle button */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarHeader"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    padding: 10px 0 6px 0 !important;
    width: 100% !important;
    height: auto !important;
}

section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stLogoSpacer"] {
    display: none !important;
}

/* Center the collapse/expand toggle button at the top of the rail */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    margin: 0 !important;
}

/* In collapsed state: rotate button 180deg so << becomes >> (pointing right to expand!) */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] button {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 8px !important;
    background: rgba(255, 255, 255, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    cursor: pointer !important;
    transform: rotate(180deg) !important;
    transition: background-color 0.15s ease !important;
    outline: none !important;
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] button:hover {
    background: rgba(255, 255, 255, 0.28) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] span {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

/* Always hide redundant outside expand button in stHeader */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* Rail content: smooth scroll without horizontal scrollbar */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarContent"] {
    width: 68px !important;
    min-width: 68px !important;
    padding: 6px 0 1rem 0 !important;
    overflow-x: hidden !important;
}

/* In minimized state, center the icon button */
section[data-testid="stSidebar"][aria-expanded="false"] a[data-testid="stSidebarNavLink"] {
    margin: 4px 8px !important;
    padding: 10px 0 !important;
    justify-content: center !important;
    text-align: center !important;
    border-radius: 10px !important;
}

/* In minimized state, active icon gets a clean badge */
section[data-testid="stSidebar"][aria-expanded="false"] a[data-testid="stSidebarNavLink"][aria-current="page"] {
    background-color: rgba(255, 255, 255, 0.3) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.45) !important;
    border-left: 1.5px solid rgba(255, 255, 255, 0.45) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}

/* In minimized state, hide text labels and keep ONLY the icons visible */
section[data-testid="stSidebar"][aria-expanded="false"] a[data-testid="stSidebarNavLink"] > span:last-child {
    display: none !important;
}

/* In minimized state, ensure icons are prominent and centered */
section[data-testid="stSidebar"][aria-expanded="false"] a[data-testid="stSidebarNavLink"] > span:first-child {
    font-size: 1.35rem !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Hide any duplicate floating collapsed control */
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}


/* ===================================================================
   4. PAGE TITLES & HEADINGS
   =================================================================== */
h1 {
    padding-bottom: 0.2rem !important;
    border-bottom: 3px solid #146356 !important;
    margin-bottom: 0.4rem !important;
}

[data-testid="stCaptionContainer"] p {
    color: #6B7C75 !important;
    font-size: 0.88rem !important;
}


/* ===================================================================
   5. METRIC CARDS — ELEVATED DESKTOP CARDS
   =================================================================== */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E0DDD6 !important;
    border-radius: 10px !important;
    padding: 16px 18px 14px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
    transition: box-shadow 0.15s ease !important;
}

[data-testid="stMetric"]:hover {
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08) !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    color: #146356 !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    color: #7A8A82 !important;
    font-weight: 600 !important;
}


/* ===================================================================
   6. FORMS & INPUTS
   =================================================================== */
[data-testid="stForm"] {
    border: 1px solid #DDD9D0 !important;
    border-radius: 10px !important;
    padding: 20px 24px !important;
    background-color: #FDFCFA !important;
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    border-radius: 8px !important;
}

[data-testid="stAlert"] {
    border-radius: 8px !important;
}


/* ===================================================================
   7. BUTTONS & EXPANDERS
   =================================================================== */
button[data-testid="stBaseButton-primary"],
button[kind="primary"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 2px 6px rgba(20, 99, 86, 0.25) !important;
}

button[data-testid="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
    box-shadow: 0 4px 10px rgba(20, 99, 86, 0.35) !important;
    transform: translateY(-1px) !important;
}

button[data-testid="stBaseButton-secondary"],
button[kind="secondary"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}

[data-testid="stExpander"] {
    border: 1px solid #DDD9D0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    font-weight: 600 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 8px !important;
    overflow: hidden !important;
    border: 1px solid #E4E0D8 !important;
}

hr {
    border-color: #E4E0D8 !important;
    opacity: 0.7 !important;
}
</style>
"""


def apply_common_styles() -> None:
    """Inject global CSS rules to ensure consistent UI across all pages."""
    st.markdown(COMMON_CSS, unsafe_allow_html=True)
