"""
Video Splitter Pro
--------------------
Windows desktop app to split video files into equal-length clips
(10s / 15s / 20s / custom) without re-encoding (fast, lossless cuts).

Run:
    pip install -r requirements.txt
    python main.py
"""

import os
import sys
import math
import subprocess
import json

from PySide6.QtCore import Qt, QUrl, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QDial, QSlider, QSplashScreen,
    QFrame, QSizePolicy, QMessageBox, QProgressBar, QSpinBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

APP_NAME = "Video Splitter Pro"

# ---------------------------------------------------------------------
# THEME - Dark Ocean Blue (matches Audio Splitter Pro)
# ---------------------------------------------------------------------
BG_DARK = "#061821"
BG_PANEL = "#0c2733"
BG_PANEL_2 = "#0f3140"
ACCENT = "#2bd4c8"
ACCENT_2 = "#1e9bb5"
TEXT_MAIN = "#dff6f5"
TEXT_DIM = "#7ea9b0"
DANGER = "#ff6b6b"

STYLE_SHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}}
QFrame#panel {{
    background-color: {BG_PANEL};
    border-radius: 10px;
    border: 1px solid {BG_PANEL_2};
}}
QPushButton {{
    background-color: {BG_PANEL_2};
    color: {TEXT_MAIN};
    border: 1px solid {ACCENT_2};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {ACCENT_2};
    color: {BG_DARK};
}}
QPushButton:pressed {{
    background-color: {ACCENT};
    color: {BG_DARK};
}}
QPushButton#primary {{
    background-color: {ACCENT};
    color: {BG_DARK};
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {ACCENT_2};
}}
QPushButton#export {{
    background-color: {ACCENT_2};
    color: {BG_DARK};
    font-weight: 700;
    border-radius: 18px;
    padding: 8px 20px;
}}
QLabel#title {{
    color: {ACCENT};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#dim {{
    color: {TEXT_DIM};
}}
QDial {{
    background-color: {BG_PANEL_2};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BG_PANEL_2};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_2};
    border-radius: 3px;
}}
QProgressBar {{
    background-color: {BG_PANEL_2};
    border-radius: 6px;
    text-align: center;
    color: {TEXT_MAIN};
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 6px;
}}
QSpinBox {{
    background-color: {BG_PANEL_2};
    border: 1px solid {ACCENT_2};
    border-radius: 6px;
    padding: 4px;
}}
"""


def resource_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


_bundled_ffmpeg = resource_path("ffmpeg.exe")
_bundled_ffprobe = resource_path("ffprobe.exe")
FFMPEG = _bundled_ffmpeg if os.path.exists(_bundled_ffmpeg) else "ffmpeg"
FFPROBE = _bundled_ffprobe if os.path.exists(_bundled_ffprobe) else "ffprobe"

_SUBPROCESS_FLAGS = 0
if os.name == "nt":
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def get_duration_seconds(path: str) -> float:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", path],
        capture_output=True, text=True, creationflags=_SUBPROCESS_FLAGS
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(980, 560)

        self.video_path = None
        self.duration_sec = 0
        self.split_seconds = 10

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.export_btn = QPushButton("⬆  Export Clips")
        self.export_btn.setObjectName("export")
        self.export_btn.clicked.connect(self.export_clips)
        self.export_btn.setEnabled(False)
        header.addWidget(self.export_btn)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, 1)

        left = QFrame()
        left.setObjectName("panel")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(18, 18, 18, 18)
        left_l.setSpacing(14)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("dim")
        self.file_label.setWordWrap(True)

        open_btn = QPushButton("📂  Select Video File")
        open_btn.setObjectName("primary")
        open_btn.clicked.connect(self.select_file)

        left_l.addWidget(open_btn)
        left_l.addWidget(self.file_label)

        play_row = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(46, 46)
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setEnabled(False)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("dim")
        play_row.addWidget(self.play_btn)
        play_row.addWidget(self.time_label)
        play_row.addStretch()
        left_l.addLayout(play_row)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self.seek)
        left_l.addWidget(self.seek_slider)

        left_l.addSpacing(10)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color:{BG_PANEL_2};")
        left_l.addWidget(divider)
        left_l.addSpacing(6)

        dial_label = QLabel("Split Interval (seconds)")
        dial_label.setObjectName("dim")
        left_l.addWidget(dial_label)

        dial_row = QHBoxLayout()
        self.dial = QDial()
        self.dial.setRange(5, 120)
        self.dial.setNotchesVisible(True)
        self.dial.setValue(10)
        self.dial.setFixedSize(120, 120)
        self.dial.valueChanged.connect(self.on_dial_changed)

        dial_col = QVBoxLayout()
        self.dial_value_label = QLabel("10 sec")
        self.dial_value_label.setAlignment(Qt.AlignCenter)
        self.dial_value_label.setStyleSheet(f"color:{ACCENT}; font-size:18px; font-weight:700;")
        self.spin = QSpinBox()
        self.spin.setRange(5, 3600)
        self.spin.setValue(10)
        self.spin.setSuffix(" sec")
        self.spin.valueChanged.connect(self.on_spin_changed)
        dial_col.addWidget(self.dial_value_label)
        dial_col.addWidget(self.spin)

        dial_row.addWidget(self.dial)
        dial_row.addSpacing(10)
        dial_row.addLayout(dial_col)
        left_l.addLayout(dial_row)

        self.ok_btn = QPushButton("OK — Preview Split")
        self.ok_btn.clicked.connect(self.preview_split)
        self.ok_btn.setEnabled(False)
        left_l.addWidget(self.ok_btn)

        self.preview_label = QLabel("")
        self.preview_label.setObjectName("dim")
        self.preview_label.setWordWrap(True)
        left_l.addWidget(self.preview_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_l.addWidget(self.progress_bar)

        left_l.addStretch()
        body.addWidget(left, 1)

        right = QFrame()
        right.setObjectName("panel")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(14, 14, 14, 14)
        wf_title = QLabel("Preview")
        wf_title.setObjectName("dim")
        right_l.addWidget(wf_title)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet(f"background-color:{BG_PANEL_2}; border-radius:8px;")
        self.player.setVideoOutput(self.video_widget)
        right_l.addWidget(self.video_widget, 1)
        body.addWidget(right, 2)

        self.ui_timer = QTimer()
        self.ui_timer.setInterval(200)
        self.ui_timer.timeout.connect(self.update_ui_timer)
        self.ui_timer.start()

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All Files (*)"
        )
        if not path:
            return
        self.load_file(path)

    def load_file(self, path):
        try:
            self.duration_sec = get_duration_seconds(path)
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                  f"Could not read this video.\n\n{e}")
            return

        self.video_path = path
        self.file_label.setText(os.path.basename(path))
        self.play_btn.setEnabled(True)
        self.ok_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        self.preview_label.setText("")

        self.player.setSource(QUrl.fromLocalFile(path))
        self.preview_split()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def on_duration_changed(self, dur):
        self.seek_slider.setRange(0, dur)

    def on_position_changed(self, pos):
        self.seek_slider.blockSignals(True)
        self.seek_slider.setValue(pos)
        self.seek_slider.blockSignals(False)
        self.time_label.setText(f"{self.fmt(pos)} / {self.fmt(self.player.duration())}")

    def seek(self, pos):
        self.player.setPosition(pos)

    def update_ui_timer(self):
        if self.player.playbackState() != QMediaPlayer.PlayingState:
            self.play_btn.setText("▶")

    @staticmethod
    def fmt(ms):
        s = int(ms / 1000)
        return f"{s // 60:02d}:{s % 60:02d}"

    def on_dial_changed(self, value):
        self.split_seconds = value
        self.dial_value_label.setText(f"{value} sec")
        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)

    def on_spin_changed(self, value):
        self.split_seconds = value
        self.dial_value_label.setText(f"{value} sec")
        if value <= 120:
            self.dial.blockSignals(True)
            self.dial.setValue(value)
            self.dial.blockSignals(False)

    def preview_split(self):
        if not self.video_path:
            return
        n_clips = math.ceil(self.duration_sec / self.split_seconds)
        mins = int(self.duration_sec // 60)
        secs = int(self.duration_sec % 60)
        self.preview_label.setText(
            f"Video length: {mins:02d}:{secs:02d}  ->  "
            f"Will create {n_clips} clip(s) of {self.split_seconds}s each.\n"
            f"(No re-encoding - clips may start at the nearest keyframe.)"
        )
        self.export_btn.setEnabled(True)

    def export_clips(self):
        if not self.video_path:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Clips")
        if not folder:
            return

        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        ext = os.path.splitext(self.video_path)[1] or ".mp4"
        n_clips = math.ceil(self.duration_sec / self.split_seconds)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, n_clips)
        self.progress_bar.setValue(0)

        try:
            for i in range(n_clips):
                start = i * self.split_seconds
                out_path = os.path.join(folder, f"{base_name}_part{i+1:03d}{ext}")
                cmd = [
                    FFMPEG, "-y", "-ss", str(start), "-i", self.video_path,
                    "-t", str(self.split_seconds),
                    "-c", "copy", "-avoid_negative_ts", "make_zero",
                    out_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True,
                                         creationflags=_SUBPROCESS_FLAGS)
                if result.returncode != 0:
                    raise RuntimeError(result.stderr[-800:])
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))
            return
        finally:
            self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "Done",
            f"Exported {n_clips} clip(s) to:\n{folder}"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)

    splash = QSplashScreen()
    splash.setFixedSize(QSize(420, 220))
    splash.setStyleSheet(f"background-color: {BG_PANEL}; border: 2px solid {ACCENT};")
    splash.showMessage(
        f"\n\n{APP_NAME}\n\nLoading...",
        Qt.AlignCenter, QColor(ACCENT)
    )
    font = QFont("Segoe UI", 16, QFont.Bold)
    splash.setFont(font)
    splash.show()
    app.processEvents()

    win = MainWindow()

    def show_main():
        splash.close()
        win.show()

    QTimer.singleShot(1400, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
