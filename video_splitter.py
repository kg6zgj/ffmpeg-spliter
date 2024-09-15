import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QListWidget,
                             QLabel, QCheckBox, QHBoxLayout, QInputDialog, QMessageBox, QListWidgetItem, QSlider)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.SingleSelection)

class VideoSplitterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Splitter")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.update_time_label)

        self.time_label = QLabel("Current Time: 0:00:00")
        self.layout.addWidget(self.time_label)

        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.layout.addWidget(self.load_button)

        self.add_split_button = QPushButton("Add Split Point")
        self.add_split_button.clicked.connect(self.add_split_point)
        self.layout.addWidget(self.add_split_button)

        self.split_list = DraggableListWidget()
        self.split_list.itemDoubleClicked.connect(self.edit_split_point)
        self.split_list.model().rowsMoved.connect(self.update_split_points_order)
        self.layout.addWidget(self.split_list)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit Split Point")
        self.edit_button.clicked.connect(self.edit_selected_split_point)
        button_layout.addWidget(self.edit_button)

        self.remove_button = QPushButton("Remove Split Point")
        self.remove_button.clicked.connect(self.remove_split_point)
        button_layout.addWidget(self.remove_button)

        self.layout.addLayout(button_layout)

        checkbox_layout = QHBoxLayout()
        self.mp4_checkbox = QCheckBox("Use MP4 Encoding")
        self.mp4_checkbox.setChecked(False)
        self.mp4_checkbox.stateChanged.connect(self.toggle_quality_slider)
        checkbox_layout.addWidget(self.mp4_checkbox)

        self.gpu_checkbox = QCheckBox("Use GPU (CUDA)")
        checkbox_layout.addWidget(self.gpu_checkbox)
        self.layout.addLayout(checkbox_layout)

        # Add quality slider
        self.quality_layout = QHBoxLayout()
        self.quality_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(51)
        self.quality_slider.setValue(23)  # Default CRF value
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(5)
        self.quality_layout.addWidget(self.quality_slider)
        self.quality_label = QLabel("23")
        self.quality_layout.addWidget(self.quality_label)
        self.layout.addLayout(self.quality_layout)

        self.quality_slider.valueChanged.connect(self.update_quality_label)

        self.split_button = QPushButton("Split Video")
        self.split_button.clicked.connect(self.split_video)
        self.layout.addWidget(self.split_button)

        self.video_path = ""
        self.split_points = []

    def load_video(self):
        file_dialog = QFileDialog()
        self.video_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        if self.video_path:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_path)))
            self.media_player.play()

    def add_split_point(self):
        current_time = self.media_player.position() // 1000  # Convert to seconds
        self.split_points.append(current_time)
        self.update_split_list()

    def update_split_list(self):
        self.split_list.clear()
        for point in self.split_points:
            item = QListWidgetItem(self.format_time(point))
            item.setData(Qt.UserRole, point)
            self.split_list.addItem(item)

    def edit_split_point(self, item):
        current_time = item.data(Qt.UserRole)
        new_time, ok = QInputDialog.getText(self, "Edit Split Point",
                                            "Enter new time (HH:MM:SS):",
                                            text=self.format_time(current_time))
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

    def format_time(self, seconds):
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    def time_to_seconds(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

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
        if not self.video_path or not self.split_points:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return

        use_mp4 = self.mp4_checkbox.isChecked()
        use_gpu = self.gpu_checkbox.isChecked()
        crf_value = self.quality_slider.value() if use_mp4 else 0

        for i, split_point in enumerate(self.split_points):
            start_time = "0" if i == 0 else str(self.split_points[i-1])
            end_time = str(split_point)
            output_file = f"{output_dir}/split_{i+1}.mp4"

            command = [
                "ffmpeg",
                "-i", self.video_path,
                "-ss", start_time,
                "-to", end_time
            ]

            if use_mp4:
                if crf_value > 0:
                    command.extend(["-crf", str(crf_value)])
                    if use_gpu:
                        command.extend(["-hwaccel", "cuda", "-c:v", "h264_nvenc"])
                    else:
                        command.extend(["-c:v", "libx264"])
                    command.extend(["-preset", "medium"])
                else:
                    command.extend(["-c", "copy"])
            else:
                command.extend(["-c", "copy"])

            command.append(output_file)
            subprocess.run(command)

        # Handle the last segment
        last_command = [
            "ffmpeg",
            "-i", self.video_path,
            "-ss", str(self.split_points[-1])
        ]

        if use_mp4:
            if crf_value > 0:
                last_command.extend(["-crf", str(crf_value)])
                if use_gpu:
                    last_command.extend(["-hwaccel", "cuda", "-c:v", "h264_nvenc"])
                else:
                    last_command.extend(["-c:v", "libx264"])
                last_command.extend(["-preset", "medium"])
            else:
                last_command.extend(["-c", "copy"])
        else:
            last_command.extend(["-c", "copy"])

        last_command.append(f"{output_dir}/split_{len(self.split_points)+1}.mp4")
        subprocess.run(last_command)

    def update_time_label(self, position):
        current_time = position // 1000
        self.time_label.setText(f"Current Time: {self.format_time(current_time)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoSplitterApp()
    window.show()
    sys.exit(app.exec_())