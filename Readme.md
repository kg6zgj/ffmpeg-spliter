# Video Splitter App

## Description
The Video Splitter App is a simple graphical tool that allows users to load a video file, mark split points while watching, edit or remove those split points, reorder them via drag-and-drop, choose between copying original codec or re-encoding with quality control, and then split the video into multiple segments based on those points. It offers options for MP4 encoding and GPU acceleration for faster processing.

## Requirements
- Windows operating system
- FFmpeg installed and added to the system PATH

## Installation

### For Users (Running the Executable)

1. Download the VideoSplitterApp.exe from the provided source.

2. Install FFmpeg:
   - Download FFmpeg from the [official FFmpeg website](https://ffmpeg.org/download.html).
   - Extract the downloaded archive.
   - Add the path to the folder containing ffmpeg.exe to your system's PATH environment variable.

3. Double-click VideoSplitterApp.exe to run the application.

### For Developers (Building from Source)

1. Ensure you have Python 3.6 or higher installed.

2. Clone this repository or download the source files.

3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

4. Install FFmpeg as described in the user installation steps above.

## Creating an Executable (for Windows)

To create a standalone executable for easy distribution on Windows:

1. Ensure you have all the requirements installed:
   ```
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```
   python build_exe.py
   ```

3. Once the process is complete, you'll find the executable in the `dist` folder, named `VideoSplitterApp.exe`.

## Distributing the Executable

To distribute the Video Splitter App:

1. Copy the `VideoSplitterApp.exe` from the `dist` folder.

2. Create a new folder named "Video Splitter App".

3. Place the `VideoSplitterApp.exe` in this folder.

4. (Optional) Add any additional files like a README or license information.

5. Zip the "Video Splitter App" folder.

6. Distribute the zip file to users.

Remind users that they need to install FFmpeg separately and add it to their system PATH.

Note: The executable is specific to the Windows version it was built on. For maximum compatibility, it's recommended to build on Windows 7 or Windows Server 2012 R2.

## Usage

1. Ensure FFmpeg is installed and added to your system PATH.

2. Run `VideoSplitterApp.exe` (for users with the executable) or run `python video_splitter.py` (for developers).

3. Click "Load Video" to select a video file.

4. Use the video player controls to navigate through the video.

5. Click "Add Split Point" to mark points where you want to split the video.

6. To edit a split point:
   - Double-click on the split point in the list, or
   - Select the split point and click "Edit Split Point"
   - Enter the new time in HH:MM:SS format

7. To remove a split point:
   - Select the split point in the list
   - Click "Remove Split Point"

8. To reorder split points:
   - Click and drag a split point to a new position in the list

9. Choose encoding options:
   - Check "Use MP4 Encoding" to re-encode the video segments to MP4 format
   - If MP4 Encoding is checked, adjust the quality slider:
     - Set to "Copy" (far left) to copy the original codec without re-encoding
     - Set between 1-51 to re-encode with specified quality (lower values = higher quality)
   - If MP4 Encoding is unchecked, the original codec will be copied without re-encoding

10. (Optional) If you have a CUDA-capable GPU, check the "Use GPU (CUDA)" box to enable GPU acceleration for re-encoding.

11. Click "Split Video" to process the video. You'll be prompted to choose an output directory for the split video segments.

## Notes
- The current time of the video is displayed below the video player for precise split point selection.
- Split points can be reordered by dragging and dropping them in the list.
- When using MP4 encoding, the quality slider adjusts the Constant Rate Factor (CRF) for video encoding. Lower values mean higher quality but larger file sizes.
- GPU acceleration is only available when re-encoding (not in "Copy" mode) and requires a CUDA-capable NVIDIA GPU.

## Troubleshooting
- If you encounter any issues with FFmpeg, ensure it's correctly installed and added to your system PATH.
- For GPU acceleration issues, make sure you have the latest NVIDIA drivers and CUDA Toolkit installed.
- If the app doesn't start, verify that all required packages are installed correctly (for developers) or that you're using a compatible Windows version (for executable users).

## Contributing
Feel free to fork this project and submit pull requests with any enhancements.

## License
This project is open-source and available under the MIT License.