"""Main window — matches the Binance Payment History page layout."""

import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import Qt, QDate, QTimer, QThread, QSize
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QComboBox,
    QProgressDialog,
    QDateEdit,
    QHeaderView,
    QDialog,
    QFrame,
)

from config import (
    API_KEY,
    API_SECRET,
    PERIOD_OPTIONS,
    USDT_EGP_RATE,
)
from api import FetchWorker, fetch_ticker
from utils import (
    to_egypt_time,
    parse_order_ids,
    get_period_dates,
    conversion_rate,
    update_prices,
    EGYPT_TZ,
)
from theme import (
    svg_to_pixmap,
    ICON_SEARCH,
    ICON_EXPORT,
    ICON_CHART,
    ICON_DASHBOARD,
    ICON_CLEAR,
    ICON_FILTER,
    GREEN,
    RED,
    ACCENT,
    TEXT_SEC,
    TEXT,
    BG_PANEL,
    BG_CARD,
    BORDER,
)
from dialogs import ExportDialog, AdvancedFilterDialog, TransactionDetailDialog
from dashboard import DashboardWindow, ChartWindow
from export import export_to_pdf

log = logging.getLogger(__name__)

# Binance-style column mapping
TYPE_MAP = {"RECEIVE": "Received", "SEND": "Paid"}
TYPE_FILTER_MAP = {"Received": "RECEIVE", "Paid": "SEND"}

# Folder where exports are saved automatically
EXPORTS_DIR = Path(__file__).resolve().parent / "exports"


class MainWindow(QMainWindow):
    """Binance Payment History — desktop viewer."""

    COLUMNS = ["Time", "Type", "To/From", "Amount", "Currency", "Status", "Action"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binance Pay")
        self.setWindowIcon(QIcon("icons/binance_pay_icon.png"))
        self.resize(1200, 700)

        # State
        self.all_transactions: list[dict] = []
        self.filtered_transactions: list[dict] = []
        self.current_filters: dict = {}
        self._thread: QThread | None = None
        self._worker: FetchWorker | None = None
        self._validated_ids: list[str] = []
        self._usdt_egp: float = USDT_EGP_RATE
        self._updating_dates = False        # guard to prevent signal loops

        self._build_ui()

        # Auto-load history on startup
        QTimer.singleShot(300, self._auto_load)

    # ══════════════════════════════════════════════════════════════════════
    #  AUTO-LOAD
    # ══════════════════════════════════════════════════════════════════════

    def _auto_load(self):
        """Fetch recent transactions automatically on startup."""
        self._load_live_prices()
        self.period_combo.setCurrentText("Last 30 Days")
        if API_KEY and API_SECRET:
            self.perform_search()

    # ══════════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(24, 16, 24, 16)

        # ── Title ──────────────────────────────────────────────────────────
        title = QLabel("Payment History")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; padding: 8px 0 16px 0;")
        root.addWidget(title)

        # ── Filter bar (matches Binance) ───────────────────────────────────
        fb = QHBoxLayout()
        fb.setSpacing(10)

        lbl_type = QLabel("Type")
        lbl_type.setStyleSheet(f"color: {TEXT_SEC};")
        fb.addWidget(lbl_type)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Received", "Paid"])
        self.type_combo.setMinimumWidth(90)
        self.type_combo.currentIndexChanged.connect(
            lambda: self.populate_table(
                self.filtered_transactions or self.all_transactions
            )
        )
        fb.addWidget(self.type_combo)

        fb.addSpacing(20)

        start_default = datetime.now() - timedelta(days=29)
        self.start_date = QDateEdit(
            QDate(start_default.year, start_default.month, start_default.day)
        )
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setCalendarPopup(True)
        self.start_date.setReadOnly(False)
        self.start_date.dateChanged.connect(self._on_date_manually_changed)
        self.start_date.editingFinished.connect(self._on_date_manually_changed)
        fb.addWidget(self.start_date)

        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {TEXT_SEC}; padding: 0 4px;")
        fb.addWidget(arrow)

        today = datetime.now()
        self.end_date = QDateEdit(QDate(today.year, today.month, today.day))
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setCalendarPopup(True)
        self.end_date.setReadOnly(False)
        self.end_date.dateChanged.connect(self._on_date_manually_changed)
        self.end_date.editingFinished.connect(self._on_date_manually_changed)
        fb.addWidget(self.end_date)

        fb.addSpacing(10)

        self.period_combo = QComboBox()
        self.period_combo.addItems(PERIOD_OPTIONS)
        self.period_combo.setMinimumWidth(120)
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        fb.addWidget(self.period_combo)

        fb.addSpacing(16)

        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self._reset_filters)
        fb.addWidget(reset_btn)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("searchBtn")
        search_btn.clicked.connect(self.perform_search)
        fb.addWidget(search_btn)

        fb.addStretch()
        root.addLayout(fb)

        root.addSpacing(10)

        # ── Separator ──────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        root.addWidget(sep)

        root.addSpacing(6)

        # ── Tools bar ──────────────────────────────────────────────────────
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Quick search…")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self._apply_text_search)
        tb.addWidget(self.search_input)

        self.ids_input = QLineEdit()
        self.ids_input.setPlaceholderText("Order IDs (comma-separated)")
        self.ids_input.setMaximumWidth(300)
        tb.addWidget(self.ids_input)

        tb.addStretch()

        tool_style = (
            f"QPushButton {{ background: transparent; border: none; "
            f"color: {TEXT_SEC}; padding: 4px 10px; font-size: 9pt; }}"
            f"QPushButton:hover {{ color: {TEXT}; }}"
        )
        for text, icon, slot in [
            ("Export",    ICON_EXPORT,    self._export),
            ("Chart",     ICON_CHART,     self._show_chart),
            ("Dashboard", ICON_DASHBOARD, self._show_dashboard),
            ("Filters",   ICON_FILTER,    self._show_filters),
        ]:
            btn = QPushButton(text)
            btn.setIcon(QIcon(svg_to_pixmap(icon, 16)))
            btn.setIconSize(QSize(16, 16))
            btn.setStyleSheet(tool_style)
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        root.addLayout(tb)
        root.addSpacing(6)

        # ── Table ──────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        self.table.cellClicked.connect(self._on_cell_click)

        h = self.table.horizontalHeader()
        h.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # To/From
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Amount
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Currency
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Action
        h.setMinimumSectionSize(60)

        root.addWidget(self.table, stretch=1)

        # ── Footer / total ─────────────────────────────────────────────────
        self.total_label = QLabel("")
        self.total_label.setStyleSheet(
            f"color: {TEXT_SEC}; padding: 10px 0; font-size: 10pt;"
        )
        root.addWidget(self.total_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Default period
        self.period_combo.setCurrentText("Last 30 Days")

    # ══════════════════════════════════════════════════════════════════════
    #  PERIOD ↔ DATE SYNC
    # ══════════════════════════════════════════════════════════════════════

    def _on_period_changed(self):
        """When the user picks a preset period, update the date pickers.
        Date pickers are ALWAYS editable — presets just fill them in."""
        if self._updating_dates:
            return
        txt = self.period_combo.currentText()
        if txt != "Custom":
            s, e = get_period_dates(txt)
            if s and e:
                self._updating_dates = True
                self.start_date.setDate(QDate(s.year, s.month, s.day))
                self.end_date.setDate(QDate(e.year, e.month, e.day))
                self._updating_dates = False

    def _on_date_manually_changed(self):
        """When the user edits a date by hand, auto-detect the matching period
        or switch to 'Custom'."""
        if self._updating_dates:
            return

        s = self.start_date.date().toPyDate()
        e = self.end_date.date().toPyDate()

        # Try to match a preset period
        matched = "Custom"
        for label in PERIOD_OPTIONS:
            if label == "Custom":
                continue
            ps, pe = get_period_dates(label)
            if ps and pe and ps.date() == s and pe.date() == e:
                matched = label
                break

        self._updating_dates = True
        self.period_combo.setCurrentText(matched)
        self._updating_dates = False

    # ══════════════════════════════════════════════════════════════════════
    #  RESET
    # ══════════════════════════════════════════════════════════════════════

    def _reset_filters(self):
        """Reset **everything** back to defaults and re-fetch."""
        self.search_input.clear()
        self.ids_input.clear()
        self.type_combo.setCurrentText("All")
        self.filtered_transactions.clear()
        self.current_filters.clear()
        self.period_combo.setCurrentText("Last 30 Days")   # also updates dates
        self.perform_search()

    # ══════════════════════════════════════════════════════════════════════
    #  SEARCH
    # ══════════════════════════════════════════════════════════════════════

    def perform_search(self):
        if not API_KEY or not API_SECRET:
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Set API_KEY and API_SECRET in your .env file.",
            )
            return

        # Always read from the date pickers (they're always editable)
        s = datetime.strptime(
            self.start_date.date().toString("yyyy-MM-dd"), "%Y-%m-%d"
        )
        e = datetime.strptime(
            self.end_date.date().toString("yyyy-MM-dd"), "%Y-%m-%d"
        )
        e = e.replace(hour=23, minute=59, second=59)
        start_ms = int(s.timestamp() * 1000)
        end_ms = int(e.timestamp() * 1000)

        # Order IDs
        self._validated_ids = []
        ids_text = self.ids_input.text().strip()
        try:
            if ids_text:
                self._validated_ids = list(set(parse_order_ids(ids_text)))
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Input", str(exc))
            return

        # Reset table
        self.table.setRowCount(0)
        self.all_transactions.clear()
        self.filtered_transactions.clear()
        self.total_label.setText("")

        # Progress
        progress = QProgressDialog("Fetching transactions…", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Worker
        self._thread = QThread()
        self._worker = FetchWorker(API_KEY, API_SECRET, start_ms, end_ms)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(progress.close)
        self._worker.error.connect(
            lambda msg: QMessageBox.critical(self, "Error", msg)
        )
        self._worker.result.connect(self._on_result)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_result(self, data: list[dict]):
        self.all_transactions = data
        if not data:
            self.total_label.setText("No transactions found.")
            return

        if self._validated_ids:
            tx_map = {tx.get("orderId"): tx for tx in data}
            found = [tx_map[oid] for oid in self._validated_ids if oid in tx_map]
            missing = [oid for oid in self._validated_ids if oid not in tx_map]
            summary = f"Found {len(found)} of {len(self._validated_ids)} Order IDs."
            if missing:
                summary += f"\nNot found: {', '.join(missing)}"
            QMessageBox.information(self, "Search Results", summary)
            self.populate_table(found)
        else:
            self.populate_table(data)

    # ══════════════════════════════════════════════════════════════════════
    #  TEXT SEARCH (live)
    # ══════════════════════════════════════════════════════════════════════

    def _apply_text_search(self):
        query = self.search_input.text().lower()
        source = self.filtered_transactions or self.all_transactions
        if not query:
            self.populate_table(source)
            return
        matched = [
            tx
            for tx in source
            if any(
                query in f.lower()
                for f in [
                    tx.get("orderId", ""),
                    tx.get("note", ""),
                    str(tx.get("amount", "")),
                    tx.get("currency", ""),
                    tx.get("payerInfo", {}).get("name", ""),
                    tx.get("direction", ""),
                ]
            )
        ]
        self.populate_table(matched)

    # ══════════════════════════════════════════════════════════════════════
    #  TABLE — Binance-style columns
    # ══════════════════════════════════════════════════════════════════════

    def populate_table(self, transactions: list[dict]):
        type_filter = self.type_combo.currentText()      # All / Received / Paid
        required_dir = TYPE_FILTER_MAP.get(type_filter)   # None for "All"

        unique: dict[str, dict] = {}
        total = 0.0

        for tx in transactions:
            try:
                amt = float(tx.get("amount", 0))
            except (ValueError, TypeError):
                amt = 0.0

            direction = tx.get("direction", "")
            if not direction:
                direction = "RECEIVE" if amt >= 0 else "SEND"
            direction = direction.upper()
            tx["direction"] = direction

            if required_dir and direction != required_dir:
                continue

            oid = tx.get("orderId", "N/A")
            if oid not in unique:
                unique[oid] = tx
                total += amt

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(unique))

        for row, (oid, tx) in enumerate(unique.items()):
            try:
                amt = float(tx.get("amount", 0))
            except (ValueError, TypeError):
                amt = 0.0

            direction = tx.get("direction", "RECEIVE")
            tx_type = TYPE_MAP.get(direction, "Received")
            amt_str = f"+{amt}" if amt >= 0 else str(amt)
            name = tx.get("payerInfo", {}).get("name", "Unknown")
            status = tx.get("status", "Completed")

            # ── Time
            time_item = QTableWidgetItem(
                to_egypt_time(tx.get("transactionTime", 0))
            )
            time_item.setData(Qt.ItemDataRole.UserRole, tx)

            # ── Type
            type_item = QTableWidgetItem(tx_type)

            # ── To/From
            name_item = QTableWidgetItem(name)

            # ── Amount (coloured)
            amt_item = QTableWidgetItem(amt_str)
            amt_item.setForeground(QColor(GREEN if amt >= 0 else RED))

            # ── Currency
            cur_item = QTableWidgetItem(tx.get("currency", "N/A"))

            # ── Status (green)
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(GREEN))

            # ── Details (gold link)
            detail_item = QTableWidgetItem("Details")
            detail_item.setForeground(QColor(ACCENT))

            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, name_item)
            self.table.setItem(row, 3, amt_item)
            self.table.setItem(row, 4, cur_item)
            self.table.setItem(row, 5, status_item)
            self.table.setItem(row, 6, detail_item)

        self.table.setSortingEnabled(True)
        self.total_label.setText(
            f"{len(unique)} transactions  ·  Net: {total:+.2f}"
        )

    # ══════════════════════════════════════════════════════════════════════
    #  DETAILS DIALOG
    # ══════════════════════════════════════════════════════════════════════

    def _on_cell_click(self, row: int, col: int):
        if col != 6:  # Only react to the Action column
            return
        item = self.table.item(row, 0)
        if not item:
            return
        tx = item.data(Qt.ItemDataRole.UserRole)
        if tx:
            self._show_detail(tx)

    def _show_detail(self, tx: dict):
        try:
            amt = float(tx.get("amount", 0))
        except (ValueError, TypeError):
            amt = 0.0
        details = [
            ("Order ID",  tx.get("orderId", "N/A")),
            ("Time",      to_egypt_time(tx.get("transactionTime", 0))),
            ("Type",      TYPE_MAP.get(tx.get("direction", "RECEIVE"), "Received")),
            ("From / To", tx.get("payerInfo", {}).get("name", "Unknown")),
            ("Amount",    f"{amt:+.2f}"),
            ("Currency",  tx.get("currency", "N/A")),
            ("Status",    tx.get("status", "Completed")),
            ("Note",      tx.get("note", "") or "—"),
        ]
        dlg = TransactionDetailDialog(details, self)
        dlg.exec()

    # ══════════════════════════════════════════════════════════════════════
    #  EXPORT  →  exports/ folder
    # ══════════════════════════════════════════════════════════════════════

    def _export(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return

        all_cols = [
            "Time", "Type", "To/From", "Amount", "Currency", "Status",
            "Order ID", "Note",
        ]
        dlg = ExportDialog(all_cols, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        sel = dlg.selected_columns()
        fmt = dlg.selected_format()       # "pdf" or "xlsx"
        if not sel:
            QMessageBox.warning(self, "Warning", "Select at least one column.")
            return

        # Collect rows from underlying transaction data
        rows: list[list[str]] = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if not item:
                continue
            tx = item.data(Qt.ItemDataRole.UserRole)
            if not tx:
                continue
            row_data: list[str] = []
            for c in sel:
                if c == "Time":
                    row_data.append(to_egypt_time(tx.get("transactionTime", 0)))
                elif c == "Type":
                    row_data.append(TYPE_MAP.get(tx.get("direction", ""), "Received"))
                elif c == "To/From":
                    row_data.append(tx.get("payerInfo", {}).get("name", "Unknown"))
                elif c == "Amount":
                    row_data.append(str(tx.get("amount", "0")))
                elif c == "Currency":
                    row_data.append(tx.get("currency", "N/A"))
                elif c == "Status":
                    row_data.append(tx.get("status", "Completed"))
                elif c == "Order ID":
                    row_data.append(tx.get("orderId", "N/A"))
                elif c == "Note":
                    row_data.append(tx.get("note", ""))
            rows.append(row_data)

        # Auto-save to exports/ folder
        EXPORTS_DIR.mkdir(exist_ok=True)
        filename = f"BinancePay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        path = EXPORTS_DIR / filename

        try:
            if fmt == "pdf":
                export_to_pdf(str(path), sel, rows)
            else:
                pd.DataFrame(rows, columns=sel).to_excel(str(path), index=False)
            QMessageBox.information(
                self,
                "Exported",
                f"Saved to:\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Export failed:\n{exc}")

    # ══════════════════════════════════════════════════════════════════════
    #  TOOLBAR ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _show_chart(self):
        if not self.all_transactions:
            QMessageBox.warning(self, "Warning", "No data to chart.")
            return
        ChartWindow(self.all_transactions, self).show()

    def _show_dashboard(self):
        if not self.all_transactions:
            QMessageBox.information(self, "Info", "Fetch transactions first.")
            return
        src = self.filtered_transactions or self.all_transactions
        DashboardWindow(src, self).show()

    # ══════════════════════════════════════════════════════════════════════
    #  ADVANCED FILTERS
    # ══════════════════════════════════════════════════════════════════════

    def _show_filters(self):
        dlg = AdvancedFilterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.current_filters = dlg.filters()
            self._apply_filters()

    def _apply_filters(self):
        if not self.all_transactions:
            QMessageBox.information(self, "No Data", "Fetch transactions first.")
            return
        f = self.current_filters
        result: list[dict] = []
        for tx in self.all_transactions:
            try:
                amt = float(tx.get("amount", 0))
            except (ValueError, TypeError):
                amt = 0.0
            if f.get("use_min") and amt < f["min_val"]:
                continue
            if f.get("use_max") and amt > f["max_val"]:
                continue
            cur = tx.get("currency", "")
            if f.get("currency") != "All":
                if f["currency"] == "Other":
                    if cur in ("USDT", "BNB", "BTC"):
                        continue
                elif cur != f["currency"]:
                    continue
            if f.get("use_start") or f.get("use_end"):
                tx_dt = (
                    datetime.fromtimestamp(
                        tx.get("transactionTime", 0) / 1000, tz=timezone.utc
                    )
                    .astimezone(EGYPT_TZ)
                    .replace(tzinfo=None)
                )
                if f.get("use_start"):
                    if tx_dt < datetime.strptime(f["start"], "%Y-%m-%d"):
                        continue
                if f.get("use_end"):
                    ed = datetime.strptime(f["end"], "%Y-%m-%d").replace(
                        hour=23, minute=59, second=59
                    )
                    if tx_dt > ed:
                        continue
            if f.get("name"):
                name = tx.get("payerInfo", {}).get("name", "").lower()
                if f["name"].lower() not in name:
                    continue
            if f.get("note"):
                note = tx.get("note", "").lower()
                if f["note"].lower() not in note:
                    continue
            result.append(tx)
        self.filtered_transactions = result
        self.populate_table(result)

    # ══════════════════════════════════════════════════════════════════════
    #  LIVE PRICES
    # ══════════════════════════════════════════════════════════════════════

    def _load_live_prices(self):
        prices: dict[str, float] = {"USDT": 1.0}
        for sym, ticker in [("BNB", "BNBUSDT"), ("BTC", "BTCUSDT")]:
            p = fetch_ticker(ticker)
            if p:
                prices[sym] = p
        update_prices(prices)
        log.info("Price cache: %s", prices)
