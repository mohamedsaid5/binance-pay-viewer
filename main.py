"""Binance Pay Transaction Viewer — entry point."""

import sys
import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor, QPen, QLinearGradient
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget

from theme import apply_theme, ACCENT, BG_PANEL, BG_CARD, TEXT, TEXT_SEC


class SplashScreen(QSplashScreen):
    """Binance-themed splash screen with a progress bar."""

    WIDTH, HEIGHT = 420, 280

    def __init__(self):
        pixmap = QPixmap(self.WIDTH, self.HEIGHT)
        pixmap.fill(QColor(BG_PANEL))
        super().__init__(pixmap)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # ── Central widget layout ─────────────────────────────────────────
        container = QWidget(self)
        container.setGeometry(0, 0, self.WIDTH, self.HEIGHT)
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 36, 40, 28)
        layout.setSpacing(6)

        # ── Logo icon ─────────────────────────────────────────────────────
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "binance_pay_icon.png")
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(icon_path):
            logo_px = QPixmap(icon_path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(logo_px)
        layout.addWidget(logo_label)
        layout.addSpacing(8)

        # ── Title ─────────────────────────────────────────────────────────
        title = QLabel("Binance Pay")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        # ── Subtitle ──────────────────────────────────────────────────────
        subtitle = QLabel("Transaction Viewer")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {TEXT_SEC}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # ── Progress bar ──────────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_CARD};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self._progress)

        # ── Status label ──────────────────────────────────────────────────
        self._status = QLabel("Loading…")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFont(QFont("Segoe UI", 8))
        self._status.setStyleSheet(f"color: {TEXT_SEC}; background: transparent;")
        layout.addWidget(self._status)

        self._value = 0

    # ── Paint a subtle border + accent line at top ────────────────────────
    def drawContents(self, painter: QPainter):
        # Border
        painter.setPen(QPen(QColor(ACCENT), 2))
        painter.drawLine(0, 0, self.WIDTH, 0)  # gold accent line at top
        painter.setPen(QPen(QColor(BG_CARD), 1))
        painter.drawRect(0, 0, self.WIDTH - 1, self.HEIGHT - 1)

    def set_progress(self, value: int, status: str = ""):
        self._value = value
        self._progress.setValue(value)
        if status:
            self._status.setText(status)
        QApplication.processEvents()


def main():
    app = QApplication(sys.argv)
    apply_theme(app)

    # ── Show splash ───────────────────────────────────────────────────────
    splash = SplashScreen()
    splash.show()
    QApplication.processEvents()

    # ── Simulated load steps ──────────────────────────────────────────────
    splash.set_progress(20, "Loading configuration…")
    import config  # noqa: F401

    splash.set_progress(40, "Preparing API module…")
    import api  # noqa: F401

    splash.set_progress(60, "Building interface…")
    from main_window import MainWindow

    splash.set_progress(80, "Initializing window…")
    window = MainWindow()

    splash.set_progress(100, "Ready!")

    # ── Small delay so the user sees "Ready!" then fade out ───────────────
    QTimer.singleShot(400, lambda: _finish_splash(splash, window))

    sys.exit(app.exec())


def _finish_splash(splash: SplashScreen, window):
    """Close splash and show the main window."""
    window.show()
    splash.finish(window)


if __name__ == "__main__":
    main()
