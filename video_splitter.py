import sys
import re
import shutil
import configparser
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QListWidget,
                             QLabel, QCheckBox, QHBoxLayout, QInputDialog, QMessageBox, QListWidgetItem, QSlider,
                             QSplitter, QPlainTextEdit, QSizePolicy, QProgressBar)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt, QProcess, QProcessEnvironment
from PyQt5.QtGui import QIcon


class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.SingleSelection)


class VideoSplitterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Splitter")
        # Increase the starting size
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a splitter for the main window and output window
        self.splitter = QSplitter(Qt.Vertical)
        self.layout.addWidget(self.splitter)

        # Main window widget
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.splitter.addWidget(self.main_widget)

        # Video and controls splitter
        self.video_controls_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.video_controls_splitter)

        # Video widget and playback controls
        self.video_widget_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_widget_container)
        self.video_controls_splitter.addWidget(self.video_widget_container)

        self.video_widget = QVideoWidget()
        # Set size policy to expanding to allow the widget to grow
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.error.connect(self.handle_error)

        # Playback controls
        playback_layout = QHBoxLayout()
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.play_pause)
        playback_layout.addWidget(self.play_pause_button)

        # Timeline slider
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.sliderMoved.connect(self.set_position)
        playback_layout.addWidget(self.timeline_slider)

        self.time_label = QLabel("00:00:00 / 00:00:00")
        playback_layout.addWidget(self.time_label)

        self.video_layout.addLayout(playback_layout)

        # Volume slider
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        self.video_layout.addLayout(volume_layout)

        # Control widgets
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.video_controls_splitter.addWidget(self.controls_widget)

        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.controls_layout.addWidget(self.load_button)

        self.add_split_button = QPushButton("Add Split Point")
        self.add_split_button.clicked.connect(self.add_split_point)
        self.controls_layout.addWidget(self.add_split_button)

        self.split_list = DraggableListWidget()
        self.split_list.itemDoubleClicked.connect(self.edit_split_point)
        self.split_list.model().rowsMoved.connect(self.update_split_points_order)
        self.controls_layout.addWidget(self.split_list)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit Split Point")
        self.edit_button.clicked.connect(self.edit_selected_split_point)
        button_layout.addWidget(self.edit_button)

        self.remove_button = QPushButton("Remove Split Point")
        self.remove_button.clicked.connect(self.remove_split_point)
        button_layout.addWidget(self.remove_button)

        self.controls_layout.addLayout(button_layout)

        checkbox_layout = QHBoxLayout()
        self.mp4_checkbox = QCheckBox("Use MP4 Encoding")
        self.mp4_checkbox.setChecked(False)
        self.mp4_checkbox.stateChanged.connect(self.toggle_quality_slider)
        checkbox_layout.addWidget(self.mp4_checkbox)

        self.gpu_checkbox = QCheckBox("Use GPU (CUDA)")
        checkbox_layout.addWidget(self.gpu_checkbox)
        self.controls_layout.addLayout(checkbox_layout)

        # Add quality slider
        self.quality_layout = QHBoxLayout()
        self.quality_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(51)
        self.quality_slider.setValue(23)  # Default CRF value
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(5)
        self.quality_slider.setEnabled(False)  # Initially disabled
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        self.quality_layout.addWidget(self.quality_slider)

        self.quality_label = QLabel("Copy")
        self.quality_layout.addWidget(self.quality_label)
        self.controls_layout.addLayout(self.quality_layout)

        self.split_button = QPushButton("Split Video")
        self.split_button.clicked.connect(self.split_video)
        self.controls_layout.addWidget(self.split_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.controls_layout.addWidget(self.progress_bar)

        # Output window
        self.output_widget = QPlainTextEdit()
        self.output_widget.setReadOnly(True)
        self.splitter.addWidget(self.output_widget)

        self.video_path = ""
        self.split_points = []

        # Adjust the stretch factors to make the video widget expand
        self.video_controls_splitter.setStretchFactor(0, 3)  # Video widget
        self.video_controls_splitter.setStretchFactor(1, 1)  # Controls
        self.splitter.setStretchFactor(0, 4)  # Main window
        self.splitter.setStretchFactor(1, 1)  # Output window

        # Configuration file handling
        self.config_file = os.path.join(os.path.expanduser("~"), ".video_splitter_config.ini")
        self.config = configparser.ConfigParser()
        self.ffmpeg_path = None
        self.load_ffmpeg_path()

    def load_ffmpeg_path(self):
        # Try to read FFmpeg path from config file
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if 'FFmpeg' in self.config and 'path' in self.config['FFmpeg']:
                self.ffmpeg_path = self.config['FFmpeg']['path']
                if not os.path.isfile(self.ffmpeg_path):
                    self.ffmpeg_path = None
        if not self.ffmpeg_path:
            # Try to find FFmpeg in system PATH
            self.ffmpeg_path = shutil.which('ffmpeg')
        if not self.ffmpeg_path:
            # Prompt user to locate FFmpeg
            QMessageBox.information(self, "FFmpeg Not Found",
                                    "FFmpeg executable not found. Please locate the FFmpeg executable.")
            self.ffmpeg_path = self.browse_ffmpeg_executable()
            if self.ffmpeg_path:
                # Save to config file
                if 'FFmpeg' not in self.config:
                    self.config['FFmpeg'] = {}
                self.config['FFmpeg']['path'] = self.ffmpeg_path
                with open(self.config_file, 'w') as configfile:
                    self.config.write(configfile)
        if not self.ffmpeg_path:
            QMessageBox.critical(self, "FFmpeg Not Found",
                                 "FFmpeg executable not found. The application cannot function without FFmpeg.")
            self.split_button.setEnabled(False)
            self.add_split_button.setEnabled(False)
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

    def handle_error(self, error):
        self.output_widget.appendPlainText(f"Error: {self.media_player.errorString()}")

    def load_video(self):
        file_dialog = QFileDialog()
        self.video_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "",
                                                         "Video Files (*.mp4 *.avi *.mkv)")
        if self.video_path:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_path)))
            self.play_pause_button.setText("Play")

    def play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")
        else:
            self.media_player.play()
            self.play_pause_button.setText("Pause")

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_position(self, position):
        self.timeline_slider.setValue(position)
        self.update_time_label(position)

    def update_duration(self, duration):
        self.timeline_slider.setRange(0, duration)

    def set_volume(self, volume):
        self.media_player.setVolume(volume)

    def add_split_point(self):
        current_time = self.media_player.position() // 1000  # Convert to seconds
        self.split_points.append(current_time)
        self.update_split_list()

    def update_split_list(self):
        self.split_list.clear()
        for point in self.split_points:
            item = QListWidgetItem(self.format_time(point * 1000))
            item.setData(Qt.UserRole, point)
            self.split_list.addItem(item)

    def edit_split_point(self, item):
        current_time = item.data(Qt.UserRole)
        new_time, ok = QInputDialog.getText(self, "Edit Split Point",
                                            "Enter new time (HH:MM:SS):",
                                            text=self.format_time(current_time * 1000))
        if ok:
            try:
                new_seconds = self.time_to_seconds(new_time)
                index = self.split_points.index(current_time)
                self.split_points[index] = new_seconds
                self.update_split_list()
            except ValueError:
                QMessageBox.warning(self, "Invalid Time", "Please enter a valid time in HH:MM:SS format.")

    def edit_selected_split_point(self):
        selected_items = self.split_list.selectedItems()
        if selected_items:
            self.edit_split_point(selected_items[0])

    def remove_split_point(self):
        selected_items = self.split_list.selectedItems()
        if selected_items:
            current_time = selected_items[0].data(Qt.UserRole)
            self.split_points.remove(current_time)
            self.update_split_list()

    def update_split_points_order(self):
        self.split_points = [self.split_list.item(i).data(Qt.UserRole) for i in range(self.split_list.count())]

    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    def time_to_seconds(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def update_time_label(self, position):
        current_time = self.format_time(position)
        total_time = self.format_time(self.media_player.duration())
        self.time_label.setText(f"{current_time} / {total_time}")

    def update_quality_label(self, value):
        self.quality_label.setText("Copy" if value == 0 else str(value))

    def toggle_quality_slider(self, state):
        self.quality_slider.setEnabled(state == Qt.Checked)
        self.quality_label.setEnabled(state == Qt.Checked)
        if state == Qt.Checked:
            self.update_quality_label(self.quality_slider.value())
        else:
            self.quality_label.setText("Copy")

    def split_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "No Video Loaded", "Please load a video file first.")
            return
        if not self.split_points:
            QMessageBox.warning(self, "No Split Points", "Please add at least one split point.")
            return

        # Pause the video if it is playing
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return

        use_mp4 = self.mp4_checkbox.isChecked()
        use_gpu = self.gpu_checkbox.isChecked()
        crf_value = self.quality_slider.value() if use_mp4 else 0

        self.output_widget.clear()
        self.output_widget.appendPlainText("Starting video splitting process...\n")

        # Initialize the process
        self.process = QProcess()
        env = QProcessEnvironment.systemEnvironment()
        self.process.setProcessEnvironment(env)
        self.process.setProcessChannelMode(QProcess.MergedChannels)  # Capture both stdout and stderr
        self.process.readyReadStandardOutput.connect(self.handle_process_output)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)  # Handle process errors

        # Build the list of commands
        self.commands = []
        all_split_points = [0] + sorted(self.split_points) + [self.media_player.duration() // 1000]
        self.total_duration = all_split_points[-1] - all_split_points[0]
        self.current_segment_duration = 0

        # Get the original file name without extension
        base_filename = os.path.splitext(os.path.basename(self.video_path))[0]

        for i in range(len(all_split_points) - 1):
            start_time = self.format_time(all_split_points[i] * 1000)
            end_time = self.format_time(all_split_points[i + 1] * 1000)
            output_file = os.path.join(output_dir, f"{base_filename}_split_{i + 1}.mp4")

            command = [
                self.ffmpeg_path,
                "-y",  # Overwrite output files without asking
                "-i", self.video_path,
                "-ss", start_time,
                "-to", end_time
            ]

            if use_mp4:
                if crf_value > 0:
                    if use_gpu:
                        command.extend(["-c:v", "h264_nvenc", "-crf", str(crf_value), "-preset", "medium"])
                    else:
                        command.extend(["-c:v", "libx264", "-crf", str(crf_value), "-preset", "medium"])
                else:
                    command.extend(["-c", "copy"])
            else:
                command.extend(["-c", "copy"])

            command.append(output_file)
            segment_duration = all_split_points[i + 1] - all_split_points[i]
            self.commands.append({
                'segment_number': i + 1,
                'command': command,
                'duration': segment_duration,
                'processed': 0
            })

        # Start processing commands
        self.current_command_index = 0
        self.run_next_command()

    def run_next_command(self):
        if self.current_command_index < len(self.commands):
            self.current_command = self.commands[self.current_command_index]
            segment_number = self.current_command['segment_number']
            command = self.current_command['command']
            self.output_widget.appendPlainText(f"Processing segment {segment_number}...\n")
            self.output_widget.appendPlainText(" ".join([f'"{arg}"' if ' ' in arg else arg for arg in command]) + "\n")
            self.progress_bar.setValue(0)

            # Start the process with the command and arguments
            self.process.start(command[0], command[1:])
        else:
            self.output_widget.appendPlainText("Video splitting process completed.")
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Process Completed", "Video splitting process completed.")

    def handle_process_output(self):
        data = self.process.readAllStandardOutput()
        output = bytes(data).decode("utf8", errors='replace')
        self.output_widget.appendPlainText(output)

        # Parse progress information
        time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", output)
        if time_match:
            time_str = time_match.group(1)
            processed_seconds = self.time_to_seconds_ffmpeg(time_str)
            segment_duration = self.current_command['duration']
            progress = int((processed_seconds / segment_duration) * 100)
            self.progress_bar.setValue(progress if progress <= 100 else 100)

    def process_finished(self, exitCode, exitStatus):
        if exitCode != 0:
            self.output_widget.appendPlainText(f"FFmpeg process failed with exit code {exitCode}.")
            QMessageBox.critical(self, "Error", f"FFmpeg process failed with exit code {exitCode}.")
        else:
            self.current_command_index += 1
            self.run_next_command()

    def process_error(self, error):
        error_messages = {
            QProcess.FailedToStart: "Failed to start FFmpeg process. Please ensure FFmpeg is installed and in your PATH.",
            QProcess.Crashed: "FFmpeg process crashed.",
            QProcess.Timedout: "FFmpeg process timed out.",
            QProcess.WriteError: "An error occurred when attempting to write to the FFmpeg process.",
            QProcess.ReadError: "An error occurred when attempting to read from the FFmpeg process.",
            QProcess.UnknownError: "An unknown error occurred with the FFmpeg process."
        }
        message = error_messages.get(error, "An unknown error occurred.")
        self.output_widget.appendPlainText(f"Process Error: {message}")
        QMessageBox.critical(self, "Process Error", message)

    def time_to_seconds_ffmpeg(self, time_str):
        # Time format is HH:MM:SS.microseconds
        h, m, s = time_str.split(':')
        s, ms = s.split('.')
        total_seconds = int(h) * 3600 + int(m) * 60 + int(s) + float('0.' + ms)
        return total_seconds


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoSplitterApp()
    window.show()
    sys.exit(app.exec_())
