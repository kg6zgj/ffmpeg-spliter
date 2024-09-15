import sys
import os
import shutil
import re
from PyQt5 import QtWidgets, QtGui, QtCore
import vlc
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QLabel,
                             QHBoxLayout, QSlider, QPlainTextEdit, QProgressBar, QMessageBox, QFrame, QSizePolicy,
                             QSplitter)
from PyQt5.QtCore import Qt, QProcess, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.create_ui()
        self.is_paused = False

    def create_ui(self):
        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setAutoFillBackground(True)
        self.video_frame.setBackgroundRole(QPalette.Window)
        self.palette = self.video_frame.palette()
        self.palette.setColor(QPalette.Window, QtGui.QColor(0, 0, 0))
        self.video_frame.setPalette(self.palette)
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Playback controls
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)

        # Time slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setToolTip("Position")
        self.position_slider.setMaximum(1000)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.time_label = QLabel("00:00:00 / 00:00:00")

        # Volume control
        self.volume_label = QLabel("Volume")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.mediaplayer.audio_set_volume(50)
        self.volume_slider.valueChanged.connect(self.set_volume)

        # Audio delay control
        self.audio_delay_label = QLabel("Audio Delay (ms)")
        self.audio_delay_slider = QSlider(Qt.Horizontal)
        self.audio_delay_slider.setMinimum(-5000)
        self.audio_delay_slider.setMaximum(5000)
        self.audio_delay_slider.setSingleStep(50)
        self.audio_delay_slider.setValue(0)
        self.audio_delay_slider.setToolTip("Audio Delay (ms)")
        self.audio_delay_slider.valueChanged.connect(self.set_audio_delay)
        self.current_audio_delay_label = QLabel("0 ms")

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_frame)

        time_layout = QHBoxLayout()
        time_layout.addWidget(self.position_slider)
        time_layout.addWidget(self.time_label)
        main_layout.addLayout(time_layout)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        main_layout.addLayout(controls_layout)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)
        main_layout.addLayout(volume_layout)

        audio_delay_layout = QHBoxLayout()
        audio_delay_layout.addWidget(self.audio_delay_label)
        audio_delay_layout.addWidget(self.audio_delay_slider)
        audio_delay_layout.addWidget(self.current_audio_delay_label)
        main_layout.addLayout(audio_delay_layout)

        self.setLayout(main_layout)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)

    def adjust_video_size(self):
        if not self.mediaplayer.is_playing():
            return

        video_width = self.mediaplayer.video_get_width()
        video_height = self.mediaplayer.video_get_height()

        if video_width and video_height:
            container_width = self.video_frame.width()
            container_height = self.video_frame.height()

            aspect_ratio = video_width / video_height
            new_height = int(container_width / aspect_ratio)

            if new_height > container_height:
                new_height = container_height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = container_width

            self.mediaplayer.video_set_scale(0)  # Reset scale
            self.mediaplayer.video_set_aspect_ratio(f"{new_width}:{new_height}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_video_size()

    def open_file(self, filename):
        self.media = self.instance.media_new(filename)
        self.mediaplayer.set_media(self.media)

        if sys.platform.startswith('linux'):
            self.mediaplayer.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.mediaplayer.set_nsobject(int(self.video_frame.winId()))

        self.play_pause()
        self.adjust_video_size()

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.play_button.setText("Play")
            self.is_paused = True
        else:
            if self.mediaplayer.play() == -1:
                self.error_dialog("Unable to play the media.")
            else:
                self.mediaplayer.play()
                self.play_button.setText("Pause")
                self.timer.start()
                self.is_paused = False

    def stop(self):
        self.mediaplayer.stop()
        self.play_button.setText("Play")
        self.timer.stop()
        self.position_slider.setValue(0)

    def set_position(self, position):
        self.mediaplayer.set_position(position / 1000.0)

    def update_ui(self):
        media_length = self.mediaplayer.get_length() / 1000.0
        media_position = self.mediaplayer.get_time() / 1000.0

        if media_length > 0:
            position = int(self.mediaplayer.get_position() * 1000)
            self.position_slider.setValue(position)
            self.time_label.setText(f"{self.format_time(media_position)} / {self.format_time(media_length)}")

        if not self.mediaplayer.is_playing():
            self.timer.stop()
            if not self.is_paused:
                self.stop()

    def set_volume(self, volume):
        self.mediaplayer.audio_set_volume(volume)

    def set_audio_delay(self, delay_ms):
        self.mediaplayer.audio_set_delay(delay_ms * 1000)
        self.current_audio_delay_label.setText(f"{delay_ms} ms")

    def format_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def error_dialog(self, message):
        QMessageBox.critical(self, "Error", message)

class FFmpegWorker(QThread):
    progress = pyqtSignal(str)

    def __init__(self, ffmpeg_path, input_file, output_file, audio_delay_ms):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.input_file = input_file
        self.output_file = output_file
        self.audio_delay_ms = audio_delay_ms

    def run(self):
        command = [
            self.ffmpeg_path,
            "-y",
            "-i", self.input_file,
            "-itsoffset", f"{self.audio_delay_ms / 1000.0}",
            "-i", self.input_file,
            "-map", "0:v",
            "-map", "1:a",
            "-c", "copy",
            self.output_file
        ]

        process = QProcess()
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.start(command[0], command[1:])
        while process.state() == QProcess.Running:
            process.waitForReadyRead(100)
            output = process.readAllStandardOutput().data().decode('utf-8')
            if output:
                self.progress.emit(output)
        process.waitForFinished()
        exit_code = process.exitCode()
        if exit_code != 0:
            self.progress.emit(f"FFmpeg process failed with exit code {exit_code}.")

class AudioDelayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Delay Adjuster")
        self.setGeometry(100, 100, 1920, 1080)  # Set to 1080p resolution

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a splitter for the main content and the terminal
        self.splitter = QSplitter(Qt.Vertical)
        self.layout.addWidget(self.splitter)

        # Main content widget
        self.main_content = QWidget()
        self.main_content_layout = QVBoxLayout(self.main_content)
        self.splitter.addWidget(self.main_content)

        self.video_player = VideoPlayer()
        self.main_content_layout.addWidget(self.video_player)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.export_button = QPushButton("Export Video with Adjusted Audio Delay")
        self.export_button.clicked.connect(self.export_video)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.export_button)
        self.main_content_layout.addLayout(button_layout)

        # Terminal widget
        self.output_widget = QPlainTextEdit()
        self.output_widget.setReadOnly(True)
        self.splitter.addWidget(self.output_widget)

        # Set the initial sizes of the splitter
        self.splitter.setSizes([800, 200])  # Adjust these values to change the initial sizes

        self.video_path = ""
        self.ffmpeg_path = None
        self.load_ffmpeg_path()

    def load_ffmpeg_path(self):
        self.ffmpeg_path = shutil.which('ffmpeg')
        if not self.ffmpeg_path:
            QMessageBox.information(self, "FFmpeg Not Found",
                                    "FFmpeg executable not found. Please locate the FFmpeg executable.")
            self.ffmpeg_path = self.browse_ffmpeg_executable()
        if not self.ffmpeg_path:
            QMessageBox.critical(self, "FFmpeg Not Found",
                                 "FFmpeg executable not found. The application cannot function without FFmpeg.")
            self.export_button.setEnabled(False)
        else:
            self.output_widget.appendPlainText(f"Using FFmpeg at: {self.ffmpeg_path}")

    def browse_ffmpeg_executable(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        ffmpeg_exec, _ = QFileDialog.getOpenFileName(self, "Locate FFmpeg Executable", "",
                                                     "Executable Files (*.exe);;All Files (*)", options=options)
        if ffmpeg_exec:
            if os.path.isfile(ffmpeg_exec):
                return ffmpeg_exec
        return None

    def load_video(self):
        file_dialog = QFileDialog()
        self.video_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "",
                                                         "Video Files (*.mp4 *.avi *.mkv)")
        if self.video_path:
            self.video_player.open_file(self.video_path)
            self.export_button.setEnabled(True)

    def export_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "No Video Loaded", "Please load a video file first.")
            return

        if self.video_player.mediaplayer.is_playing():
            self.video_player.play_pause()

        audio_delay_ms = self.video_player.audio_delay_slider.value()
        if audio_delay_ms == 0:
            QMessageBox.information(self, "No Audio Delay", "Audio delay is zero. No need to export.")
            return

        base_dir = os.path.dirname(self.video_path)
        base_name, ext = os.path.splitext(os.path.basename(self.video_path))
        default_output_file = os.path.join(base_dir, f"{base_name}_shifted{ext}")
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Output Video", default_output_file,
                                                     f"Video Files (*{ext})")
        if not output_file:
            return

        self.output_widget.clear()
        self.output_widget.appendPlainText("Starting FFmpeg process...\n")
        self.progress_bar = QProgressBar()
        self.main_content_layout.addWidget(self.progress_bar)
        self.progress_bar.setValue(0)

        self.ffmpeg_worker = FFmpegWorker(self.ffmpeg_path, self.video_path, output_file, audio_delay_ms)
        self.ffmpeg_worker.progress.connect(self.handle_ffmpeg_output)
        self.ffmpeg_worker.finished.connect(self.ffmpeg_finished)
        self.ffmpeg_worker.start()

    def handle_ffmpeg_output(self, output):
        self.output_widget.appendPlainText(output)
        time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", output)
        if time_match:
            time_str = time_match.group(1)
            processed_seconds = self.time_to_seconds_ffmpeg(time_str)
            total_duration = self.video_player.mediaplayer.get_length() / 1000.0
            if total_duration > 0:
                progress = int((processed_seconds / total_duration) * 100)
                self.progress_bar.setValue(progress if progress <= 100 else 100)

    def ffmpeg_finished(self):
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Process Completed", "Video export completed.")
        self.main_content_layout.removeWidget(self.progress_bar)
        self.progress_bar.deleteLater()
        self.progress_bar = None

    def time_to_seconds_ffmpeg(self, time_str):
        h, m, s = time_str.split(':')
        s, ms = s.split('.')
        total_seconds = int(h) * 3600 + int(m) * 60 + int(s) + float('0.' + ms)
        return total_seconds

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Adjust the splitter sizes when the window is resized
        total_height = self.splitter.height()
        main_content_height = int(total_height * 0.8)  # 80% for main content
        terminal_height = total_height - main_content_height
        self.splitter.setSizes([main_content_height, terminal_height])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioDelayApp()
    window.show()
    sys.exit(app.exec_())