"""Reusable dialog windows — export, column selection, advanced filters, details."""

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit,
    QFrame,
)

from theme import ACCENT, BG_PANEL, BG_CARD, BG_INPUT, BORDER, TEXT, TEXT_SEC, GREEN


# ── Export Dialog ──────────────────────────────────────────────────────────

class ExportDialog(QDialog):
    """Combined column selection + format picker for one-click export."""

    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Format ─────────────────────────────────────────────────────────
        fmt_grp = QGroupBox("Format")
        fmt_lay = QHBoxLayout(fmt_grp)
        self._fmt_group = QButtonGroup(self)
        self._rb_pdf = QRadioButton("PDF")
        self._rb_xlsx = QRadioButton("Excel (.xlsx)")
        self._rb_pdf.setChecked(True)
        self._fmt_group.addButton(self._rb_pdf)
        self._fmt_group.addButton(self._rb_xlsx)
        fmt_lay.addWidget(self._rb_pdf)
        fmt_lay.addWidget(self._rb_xlsx)
        layout.addWidget(fmt_grp)

        # ── Columns ────────────────────────────────────────────────────────
        col_grp = QGroupBox("Columns")
        col_lay = QVBoxLayout(col_grp)

        row = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_none = QPushButton("Deselect All")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_none.clicked.connect(lambda: self._set_all(False))
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        col_lay.addLayout(row)

        self._boxes: dict[str, QCheckBox] = {}
        for col in columns:
            cb = QCheckBox(col)
            cb.setChecked(True)
            self._boxes[col] = cb
            col_lay.addWidget(cb)

        layout.addWidget(col_grp)

        # ── OK / Cancel ────────────────────────────────────────────────────
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _set_all(self, checked: bool) -> None:
        for cb in self._boxes.values():
            cb.setChecked(checked)

    def selected_columns(self) -> list[str]:
        return [c for c, cb in self._boxes.items() if cb.isChecked()]

    def selected_format(self) -> str:
        """Return ``'pdf'`` or ``'xlsx'``."""
        return "pdf" if self._rb_pdf.isChecked() else "xlsx"


# ── Column Selection (kept for other uses) ─────────────────────────────────

class ColumnSelectionDialog(QDialog):
    """Let the user pick which table columns to include in an export."""

    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Columns")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_none = QPushButton("Deselect All")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_none.clicked.connect(lambda: self._set_all(False))
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        layout.addLayout(row)

        self._boxes: dict[str, QCheckBox] = {}
        for col in columns:
            cb = QCheckBox(col)
            cb.setChecked(True)
            self._boxes[col] = cb
            layout.addWidget(cb)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _set_all(self, checked: bool) -> None:
        for cb in self._boxes.values():
            cb.setChecked(checked)

    def selected_columns(self) -> list[str]:
        return [c for c, cb in self._boxes.items() if cb.isChecked()]


# ── Advanced Filters ───────────────────────────────────────────────────────

class AdvancedFilterDialog(QDialog):
    """Filter transactions by amount, date range, user name, or note text."""

    # ── per-dialog stylesheet (layered on top of the global theme) ────────
    _DIALOG_CSS = f"""
        AdvancedFilterDialog {{
            background-color: {BG_PANEL};
        }}

        /* Group boxes */
        QGroupBox {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 6px;
            margin-top: 20px;
            padding: 16px 12px 10px 12px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 8px;
            color: {ACCENT};
            font-size: 10pt;
        }}

        /* Labels inside grids */
        QLabel {{
            color: {TEXT_SEC};
            background: transparent;
            font-size: 10pt;
            min-width: 90px;
        }}

        /* Inputs */
        QDoubleSpinBox, QDateEdit, QComboBox, QLineEdit {{
            background-color: {BG_INPUT};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 6px 10px;
            color: {TEXT};
            min-height: 22px;
        }}
        QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus, QLineEdit:focus {{
            border-color: {ACCENT};
        }}
        QDoubleSpinBox:disabled, QDateEdit:disabled {{
            color: #474d57;
            background-color: #1e2329;
        }}

        /* Checkboxes */
        QCheckBox {{
            spacing: 6px;
            color: {TEXT_SEC};
            font-size: 9pt;
        }}
        QCheckBox::indicator {{
            width: 16px; height: 16px;
            border-radius: 3px;
            border: 1px solid #474d57;
            background: {BG_INPUT};
        }}
        QCheckBox::indicator:hover {{
            border-color: {ACCENT};
        }}
        QCheckBox::indicator:checked {{
            background: {ACCENT};
            border-color: {ACCENT};
        }}

        /* Bottom buttons */
        QPushButton#filterApplyBtn {{
            background-color: {ACCENT};
            color: {BG_PANEL};
            font-weight: bold;
            border: none;
            border-radius: 4px;
            padding: 8px 24px;
        }}
        QPushButton#filterApplyBtn:hover {{
            background-color: #d4a20a;
        }}
        QPushButton#filterCloseBtn {{
            background-color: {BG_INPUT};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 20px;
        }}
        QPushButton#filterCloseBtn:hover {{
            border-color: #3b4149;
            color: {TEXT};
        }}
        QPushButton#filterResetBtn {{
            background: transparent;
            border: 1px solid {BORDER};
            color: {TEXT_SEC};
            border-radius: 4px;
            padding: 8px 16px;
        }}
        QPushButton#filterResetBtn:hover {{
            color: {TEXT};
            border-color: #3b4149;
        }}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Filters")
        self.setMinimumWidth(520)
        self.setStyleSheet(self._DIALOG_CSS)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        self._build_amount_group(root)
        self._build_date_group(root)
        self._build_text_group(root)

        # ── Custom button row (instead of QDialogButtonBox) ──────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("filterResetBtn")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("filterCloseBtn")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("filterApplyBtn")
        apply_btn.clicked.connect(self.accept)
        btn_row.addWidget(apply_btn)

        root.addLayout(btn_row)

    def _build_amount_group(self, parent):
        grp = QGroupBox("Amount")
        gl = QGridLayout(grp)
        gl.setHorizontalSpacing(12)
        gl.setVerticalSpacing(10)

        gl.addWidget(QLabel("Min:"), 0, 0)
        self.min_amount = QDoubleSpinBox()
        self.min_amount.setRange(-1_000_000, 1_000_000)
        self.min_amount.setEnabled(False)
        gl.addWidget(self.min_amount, 0, 1)
        self.use_min = QCheckBox("Enable")
        self.use_min.toggled.connect(self.min_amount.setEnabled)
        gl.addWidget(self.use_min, 0, 2)

        gl.addWidget(QLabel("Max:"), 1, 0)
        self.max_amount = QDoubleSpinBox()
        self.max_amount.setRange(-1_000_000, 1_000_000)
        self.max_amount.setValue(1000)
        self.max_amount.setEnabled(False)
        gl.addWidget(self.max_amount, 1, 1)
        self.use_max = QCheckBox("Enable")
        self.use_max.toggled.connect(self.max_amount.setEnabled)
        gl.addWidget(self.use_max, 1, 2)

        gl.addWidget(QLabel("Currency:"), 2, 0)
        self.currency_cb = QComboBox()
        self.currency_cb.addItems(["All", "USDT", "BNB", "BTC", "Other"])
        gl.addWidget(self.currency_cb, 2, 1)

        parent.addWidget(grp)

    def _build_date_group(self, parent):
        grp = QGroupBox("Date Range")
        gl = QGridLayout(grp)
        gl.setHorizontalSpacing(12)
        gl.setVerticalSpacing(10)

        gl.addWidget(QLabel("From:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setEnabled(False)
        gl.addWidget(self.start_date, 0, 1)
        self.use_start = QCheckBox("Enable")
        self.use_start.toggled.connect(self.start_date.setEnabled)
        gl.addWidget(self.use_start, 0, 2)

        gl.addWidget(QLabel("To:"), 1, 0)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        gl.addWidget(self.end_date, 1, 1)
        self.use_end = QCheckBox("Enable")
        self.use_end.toggled.connect(self.end_date.setEnabled)
        gl.addWidget(self.use_end, 1, 2)

        parent.addWidget(grp)

    def _build_text_group(self, parent):
        grp = QGroupBox("Text Filters")
        gl = QGridLayout(grp)
        gl.setHorizontalSpacing(12)
        gl.setVerticalSpacing(10)

        gl.addWidget(QLabel("Name contains:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Filter by user name")
        gl.addWidget(self.name_input, 0, 1)

        gl.addWidget(QLabel("Note contains:"), 1, 0)
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Filter by note text")
        gl.addWidget(self.note_input, 1, 1)

        parent.addWidget(grp)

    def _reset(self):
        self.use_min.setChecked(False)
        self.use_max.setChecked(False)
        self.min_amount.setValue(0)
        self.max_amount.setValue(1000)
        self.currency_cb.setCurrentText("All")
        self.use_start.setChecked(False)
        self.use_end.setChecked(False)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())
        self.name_input.clear()
        self.note_input.clear()

    def filters(self) -> dict:
        return {
            "use_min":   self.use_min.isChecked(),
            "min_val":   self.min_amount.value(),
            "use_max":   self.use_max.isChecked(),
            "max_val":   self.max_amount.value(),
            "currency":  self.currency_cb.currentText(),
            "use_start": self.use_start.isChecked(),
            "start":     self.start_date.date().toString("yyyy-MM-dd"),
            "use_end":   self.use_end.isChecked(),
            "end":       self.end_date.date().toString("yyyy-MM-dd"),
            "name":      self.name_input.text(),
            "note":      self.note_input.text(),
        }


# ── Transaction Detail ─────────────────────────────────────────────────────

class TransactionDetailDialog(QDialog):
    """Show all details for a single transaction (like Binance 'Details')."""

    def __init__(self, details: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Details")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Transaction Details")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #eaecef; padding-bottom: 8px;"
        )
        layout.addWidget(title)

        for label, value in details:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}")
            lbl.setStyleSheet(
                "color: #848e9c; min-width: 80px; font-size: 10pt;"
            )
            lbl.setFixedWidth(90)

            val = QLabel(str(value))
            val.setStyleSheet("color: #eaecef; font-size: 10pt;")
            val.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            val.setWordWrap(True)

            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)

        layout.addSpacing(8)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f0b90b; color: #181a20; "
            "font-weight: bold; border: none; border-radius: 4px; padding: 8px 24px; }"
            "QPushButton:hover { background-color: #d4a20a; }"
        )
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
