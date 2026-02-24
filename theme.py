"""Binance-style dark theme, SVG icons, and styling utilities."""

from PyQt6.QtCore import Qt, QSize, QByteArray
from PyQt6.QtGui import QPalette, QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication
from PyQt6.QtSvg import QSvgRenderer


# ── Binance Colour Palette ─────────────────────────────────────────────────

BG_BODY    = "#0b0e11"   # page background
BG_PANEL   = "#181a20"   # panels / cards
BG_CARD    = "#1e2329"   # table header, inputs
BG_INPUT   = "#2b3139"   # input fields
BORDER     = "#2b3139"
TEXT        = "#eaecef"   # primary text
TEXT_SEC    = "#848e9c"   # secondary / muted text
ACCENT     = "#f0b90b"   # Binance yellow
GREEN      = "#0ecb81"   # positive / success
RED        = "#f6465d"   # negative / error
HOVER      = "#2b3139"


# ── SVG Icons ──────────────────────────────────────────────────────────────

ICON_SEARCH = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
</svg>"""

ICON_REFRESH = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <path d="M21.5 2v6h-6M2.5 22v-6h6M2 12c0-4.4 3.6-8 8-8 3.4 0 6.3
  2.1 7.4 5M22 12c0 4.4-3.6 8-8 8-3.4 0-6.3-2.1-7.4-5"/>
</svg>"""

ICON_EXPORT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
  <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
</svg>"""

ICON_CHART = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
  <line x1="6" y1="20" x2="6" y2="14"/>
</svg>"""

ICON_DASHBOARD = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/>
  <rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>
</svg>"""

ICON_CLEAR = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
</svg>"""

ICON_FILTER = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#848e9c" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round">
  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
</svg>"""


def svg_to_pixmap(svg_str: str, size: int = 20) -> QPixmap:
    """Convert an inline SVG string to a *QPixmap*."""
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


# ── Stylesheet ─────────────────────────────────────────────────────────────

_CSS = f"""
/* ── Base ─────────────────────────────────── */
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    color: {TEXT};
    background-color: {BG_PANEL};
}}
QMainWindow, QDialog {{ background-color: {BG_PANEL}; }}

/* ── Inputs ───────────────────────────────── */
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
    border: 1px solid {ACCENT};
}}

/* ── Default Buttons ──────────────────────── */
QPushButton {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 14px;
    color: {TEXT_SEC};
    min-height: 20px;
}}
QPushButton:hover {{ color: {TEXT}; border-color: #3b4149; }}
QPushButton:pressed {{ background-color: #1e2329; }}
QPushButton:disabled {{ color: #474d57; }}
QPushButton:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: {BG_PANEL};
    font-weight: bold;
}}

/* ── Primary (yellow) button ──────────────── */
QPushButton#searchBtn {{
    background-color: {ACCENT};
    color: {BG_PANEL};
    font-weight: bold;
    border: none;
    padding: 8px 28px;
    border-radius: 4px;
}}
QPushButton#searchBtn:hover {{ background-color: #d4a20a; }}
QPushButton#searchBtn:pressed {{ background-color: #b8900a; }}

/* ── Reset (link-style) button ────────────── */
QPushButton#resetBtn {{
    background: transparent;
    border: none;
    color: {TEXT_SEC};
    padding: 8px 12px;
}}
QPushButton#resetBtn:hover {{ color: {TEXT}; }}

/* ── Labels ───────────────────────────────── */
QLabel {{ background: transparent; }}

/* ── Table ────────────────────────────────── */
QTableWidget {{
    background-color: {BG_PANEL};
    border: none;
    gridline-color: transparent;
    selection-background-color: #2b3139;
    outline: none;
}}
QTableWidget::item {{
    padding: 10px 16px;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:selected {{
    background-color: #2b3139;
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_SEC};
    padding: 10px 16px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: normal;
    font-size: 10pt;
}}

/* ── Scrollbars ───────────────────────────── */
QScrollBar:vertical {{
    background: transparent; width: 6px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: #474d57; min-height: 24px; border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{ background: #5e6673; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 6px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: #474d57; min-width: 24px; border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Combos ───────────────────────────────── */
QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: {BG_PANEL};
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 24px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: #3b4149;
    color: {TEXT};
}}

/* ── Radio buttons ────────────────────────── */
QRadioButton {{ spacing: 6px; }}
QRadioButton::indicator {{
    width: 16px; height: 16px; border-radius: 8px;
    border: 1px solid #474d57;
}}
QRadioButton::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

/* ── Groups ───────────────────────────────── */
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 18px;
    font-weight: bold;
    padding-top: 14px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {ACCENT};
}}

/* ── Tabs ─────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background-color: {BG_CARD};
    border-radius: 4px;
}}
QTabBar::tab {{
    background: {BG_PANEL}; padding: 8px 16px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    margin-right: 2px; color: {TEXT_SEC};
}}
QTabBar::tab:selected {{ background: {ACCENT}; color: {BG_PANEL}; font-weight: bold; }}
QTabBar::tab:hover:!selected {{ color: {TEXT}; }}

/* ── Checkboxes ───────────────────────────── */
QCheckBox {{ spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 3px;
    border: 1px solid #474d57;
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

/* ── Calendar ─────────────────────────────── */
QCalendarWidget QToolButton {{
    color: {TEXT}; background: {BG_CARD}; border-radius: 4px;
}}
QCalendarWidget QAbstractItemView:enabled {{
    color: {TEXT}; background: {BG_CARD};
    selection-background-color: {ACCENT};
}}

/* ── Message boxes ────────────────────────── */
QMessageBox {{ background-color: {BG_CARD}; }}
QMessageBox QPushButton {{ min-width: 90px; }}

/* ── Progress dialog ──────────────────────── */
QProgressDialog {{ background-color: {BG_CARD}; }}
"""


# ── Apply ──────────────────────────────────────────────────────────────────

def apply_theme(app: QApplication) -> None:
    """Set Fusion style with the Binance dark palette."""
    app.setStyle("Fusion")

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(BG_PANEL))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    p.setColor(QPalette.ColorRole.Base,            QColor(BG_CARD))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_INPUT))
    p.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    p.setColor(QPalette.ColorRole.Button,          QColor(BG_INPUT))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_PANEL))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor(BG_CARD))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor(TEXT))
    app.setPalette(p)

    app.setStyleSheet(_CSS)
