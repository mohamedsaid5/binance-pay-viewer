"""Dashboard (stat cards + charts) and standalone Chart window."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QTabWidget,
    QMessageBox,
)
from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
    QDateTimeAxis,
    QPieSeries,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
)

from utils import to_egypt_time

# Binance palette constants
_GREEN = "#0ecb81"
_RED   = "#f6465d"
_GOLD  = "#f0b90b"
_BG    = "#181a20"
_CARD  = "#1e2329"
_SEC   = "#848e9c"
_TXT   = "#eaecef"
_GRID  = "#2b3139"


# ── Helpers ────────────────────────────────────────────────────────────────

def _dark_chart(chart: QChart) -> None:
    chart.setBackgroundVisible(False)
    chart.setBackgroundBrush(QColor(_BG))
    chart.setTitleBrush(QColor(_TXT))
    chart.legend().setLabelColor(QColor(_TXT))


def _dark_axis(axis) -> None:
    axis.setLabelsColor(QColor(_TXT))
    axis.setTitleBrush(QColor(_TXT))
    axis.setGridLineColor(QColor(_GRID))


def _direction_of(tx: dict) -> str:
    d = tx.get("direction", "")
    if d:
        return d.upper()
    try:
        return "RECEIVE" if float(tx.get("amount", 0)) >= 0 else "SEND"
    except (ValueError, TypeError):
        return "RECEIVE"


# ── Chart Window ───────────────────────────────────────────────────────────

class ChartWindow(QMainWindow):
    """Standalone window: transaction amounts over time."""

    def __init__(self, transactions: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transactions Over Time")
        self.resize(850, 500)

        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setCentralWidget(view)

        if not transactions:
            QMessageBox.information(self, "No Data", "Nothing to plot.")
            return

        series = QLineSeries()
        series.setName("Amount")
        series.setColor(QColor(_GOLD))
        for tx in transactions:
            ms = tx.get("transactionTime", 0)
            try:
                series.append(float(ms), float(tx.get("amount", 0)))
            except (ValueError, TypeError):
                continue

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Transaction Amounts")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        _dark_chart(chart)

        ax = QDateTimeAxis()
        ax.setFormat("yyyy-MM-dd HH:mm")
        ax.setTitleText("Time")
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(ax)
        _dark_axis(ax)

        ay = QValueAxis()
        ay.setTitleText("Amount")
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(ay)
        _dark_axis(ay)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        view.setChart(chart)


# ── Dashboard Window ───────────────────────────────────────────────────────

class DashboardWindow(QMainWindow):
    """Summary statistics and three tabbed charts."""

    def __init__(self, transactions: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dashboard")
        self.resize(1000, 650)
        self._tx = transactions

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ── Stats header ──
        stats = self._calc_stats()
        header = QWidget()
        header.setStyleSheet(f"QWidget {{ background: {_CARD}; border-radius: 6px; }}")
        hl = QVBoxLayout(header)

        title = QLabel("Transaction Dashboard")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {_TXT};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(title)

        cards = QHBoxLayout()
        self._card(cards, "Transactions", str(stats["count"]), _GOLD)
        self._card(cards, "Received", f"{stats['received']:.2f}", _GREEN)
        self._card(cards, "Sent", f"{stats['sent']:.2f}", _RED)
        net_c = _GREEN if stats["net"] >= 0 else _RED
        self._card(cards, "Net", f"{stats['net']:.2f}", net_c)
        hl.addLayout(cards)
        root.addWidget(header)

        # ── Tabs ──
        tabs = QTabWidget()
        tabs.addTab(self._time_tab(), "Over Time")
        tabs.addTab(self._direction_tab(), "Direction")
        tabs.addTab(self._users_tab(), "Top Users")
        root.addWidget(tabs, stretch=1)

    def _calc_stats(self) -> dict:
        s = {"count": len(self._tx), "received": 0.0, "sent": 0.0,
             "net": 0.0, "recv_n": 0, "sent_n": 0}
        for tx in self._tx:
            try:
                amt = float(tx.get("amount", 0))
            except (ValueError, TypeError):
                continue
            if _direction_of(tx) == "RECEIVE":
                s["received"] += amt
                s["recv_n"] += 1
            else:
                s["sent"] += abs(amt)
                s["sent_n"] += 1
        s["net"] = s["received"] - s["sent"]
        return s

    @staticmethod
    def _card(layout, title: str, value: str, color: str):
        f = QFrame()
        f.setStyleSheet(
            f"QFrame {{ background: {_BG}; border-radius: 6px; "
            f"border: 1px solid {_GRID}; padding: 12px; }}"
        )
        vl = QVBoxLayout(f)
        t = QLabel(title)
        t.setStyleSheet(f"color: {_SEC}; font-size: 11px;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        vl.addWidget(t)
        vl.addWidget(v)
        layout.addWidget(f)

    # ── Charts ─────────────────────────────────────────────────────────────

    def _time_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        lay.addWidget(view)

        recv_s = QLineSeries()
        recv_s.setName("Received")
        recv_s.setColor(QColor(_GREEN))
        sent_s = QLineSeries()
        sent_s.setName("Sent")
        sent_s.setColor(QColor(_RED))

        for tx in sorted(self._tx, key=lambda t: t.get("transactionTime", 0)):
            ms = tx.get("transactionTime", 0)
            try:
                amt = float(tx.get("amount", 0))
            except (ValueError, TypeError):
                continue
            target = recv_s if _direction_of(tx) == "RECEIVE" else sent_s
            target.append(float(ms), abs(amt))

        chart = QChart()
        chart.addSeries(recv_s)
        chart.addSeries(sent_s)
        chart.setTitle("Amounts Over Time")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        _dark_chart(chart)

        ax = QDateTimeAxis()
        ax.setFormat("yyyy-MM-dd")
        ax.setTitleText("Date")
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        recv_s.attachAxis(ax)
        sent_s.attachAxis(ax)
        _dark_axis(ax)

        ay = QValueAxis()
        ay.setTitleText("Amount")
        ay.setLabelFormat("%.2f")
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        recv_s.attachAxis(ay)
        sent_s.attachAxis(ay)
        _dark_axis(ay)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        view.setChart(chart)
        return w

    def _direction_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        lay.addWidget(view)

        stats = self._calc_stats()
        series = QPieSeries()
        if stats["recv_n"]:
            sl = series.append(f"Received ({stats['recv_n']})", stats["recv_n"])
            sl.setBrush(QColor(_GREEN))
            sl.setLabelVisible(True)
            sl.setLabelColor(QColor(_TXT))
        if stats["sent_n"]:
            sl = series.append(f"Sent ({stats['sent_n']})", stats["sent_n"])
            sl.setBrush(QColor(_RED))
            sl.setLabelVisible(True)
            sl.setLabelColor(QColor(_TXT))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Direction Distribution")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        _dark_chart(chart)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        view.setChart(chart)
        return w

    def _users_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        lay.addWidget(view)

        totals: dict[str, float] = {}
        for tx in self._tx:
            name = tx.get("payerInfo", {}).get("name", "Unknown")
            if name == "Unknown":
                continue
            try:
                totals[name] = totals.get(name, 0) + abs(float(tx.get("amount", 0)))
            except (ValueError, TypeError):
                continue

        top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
        if not top:
            chart = QChart()
            chart.setTitle("No user data available")
            _dark_chart(chart)
            view.setChart(chart)
            return w

        bar_set = QBarSet("Volume")
        bar_set.setColor(QColor(_GOLD))
        names: list[str] = []
        for name, amt in top:
            names.append(name)
            bar_set.append(amt)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Top Users by Volume")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        _dark_chart(chart)

        cat_ax = QBarCategoryAxis()
        cat_ax.append(names)
        chart.addAxis(cat_ax, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(cat_ax)
        _dark_axis(cat_ax)

        val_ax = QValueAxis()
        val_ax.setTitleText("Volume")
        val_ax.setLabelFormat("%.2f")
        chart.addAxis(val_ax, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(val_ax)
        _dark_axis(val_ax)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        view.setChart(chart)
        return w
