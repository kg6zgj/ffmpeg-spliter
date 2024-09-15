import PyInstaller.__main__
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the main script
main_script = os.path.join(script_dir, "video_splitter.py")

# Path to the icon file (you can add an .ico file if you have one)
# icon_file = os.path.join(script_dir, "icon.ico")

PyInstaller.__main__.run([
    main_script,
    "--name=VideoSplitterApp",
    "--onefile",
    "--windowed",
    # "--icon=" + icon_file,  # Uncomment this line if you have an icon file
    #"--add-data=ffmpeg.exe;.",  # This assumes ffmpeg.exe is in the same directory
])