from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QFileDialog, QComboBox, QCheckBox, QProgressBar, QMessageBox,
)

from symphony.core.youtube import download_audio


class _DownloadWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, urls, output_dir, audio_format, download_playlists):
        super().__init__()
        self.urls = urls
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.download_playlists = download_playlists

    def run(self):
        def hook(info):
            state = info.get("status")
            if state == "downloading":
                total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
                current = info.get("downloaded_bytes", 0)
                percent = int(current * 100 / total) if total else 0
                self.progress.emit(percent, "Downloading…")
            elif state == "finished":
                self.progress.emit(100, "Converting audio…" if self.audio_format != "best"
                                   else "Finishing…")

        try:
            paths = download_audio(
                self.urls, self.output_dir, self.audio_format,
                self.download_playlists, hook,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(paths)


class YouTubeDownloadDialog(QDialog):
    files_ready = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Audio from YouTube")
        self.setMinimumWidth(520)
        self._thread = None
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        intro = QLabel(
            "Paste one or more YouTube video URLs below. Downloads are saved "
            "locally and added to the playlist when finished."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        root.addWidget(QLabel("Video URL(s), one per line:"))
        self.urls = QTextEdit()
        self.urls.setFixedHeight(72)
        self.urls.setPlaceholderText("https://www.youtube.com/watch?v=…")
        root.addWidget(self.urls)

        folder_row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Choose a download folder")
        choose_btn = QPushButton("BROWSE…")
        choose_btn.clicked.connect(self._choose_folder)
        folder_row.addWidget(self.output_dir, 1)
        folder_row.addWidget(choose_btn)
        root.addWidget(QLabel("Save to:"))
        root.addLayout(folder_row)

        options = QHBoxLayout()
        self.format_box = QComboBox()
        self.format_box.addItem("Best available audio", "best")
        self.format_box.addItem("MP3 (requires FFmpeg)", "mp3")
        self.format_box.addItem("M4A (requires FFmpeg)", "m4a")
        self.format_box.addItem("Opus (requires FFmpeg)", "opus")
        options.addWidget(QLabel("Format:"))
        options.addWidget(self.format_box, 1)
        self.playlists = QCheckBox("Download full YouTube playlists")
        options.addWidget(self.playlists)
        root.addLayout(options)

        self.status = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.status)
        root.addWidget(self.progress)

        buttons = QHBoxLayout()
        self.download_btn = QPushButton("DOWNLOAD")
        self.download_btn.clicked.connect(self._start_download)
        close_btn = QPushButton("CLOSE")
        close_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(self.download_btn)
        buttons.addWidget(close_btn)
        root.addLayout(buttons)

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.output_dir.setText(folder)

    def _start_download(self):
        urls = [
            line.strip() for line in self.urls.toPlainText().splitlines()
            if line.strip()
        ]
        if not urls:
            QMessageBox.warning(self, "No URL", "Paste at least one YouTube URL.")
            return
        output_dir = self.output_dir.text().strip()
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, "Choose download folder")
            if not output_dir:
                return
            self.output_dir.setText(output_dir)

        self.download_btn.setEnabled(False)
        self.urls.setEnabled(False)
        self.status.setText("Starting download…")
        self.progress.setValue(0)
        self._thread = QThread(self)
        self._worker = _DownloadWorker(
            urls, output_dir, self.format_box.currentData(), self.playlists.isChecked()
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_progress(self, value, message):
        self.progress.setValue(value)
        self.status.setText(message)

    def _on_finished(self, paths):
        self.download_btn.setEnabled(True)
        self.urls.setEnabled(True)
        self.status.setText(f"Finished — {len(paths)} audio file(s) ready.")
        self.files_ready.emit(paths)
        if not paths:
            QMessageBox.information(
                self, "No files downloaded",
                "yt-dlp did not return a local audio file for those URLs."
            )

    def _on_failed(self, message):
        self.download_btn.setEnabled(True)
        self.urls.setEnabled(True)
        self.status.setText("Download failed")
        QMessageBox.warning(self, "YouTube download failed", message)

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            QMessageBox.information(
                self, "Download in progress",
                "Wait for the current download to finish before closing this window."
            )
            event.ignore()
            return
        super().closeEvent(event)