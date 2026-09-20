@echo off
echo ==============================================
echo   Building Video Splitter Pro (.exe)
echo ==============================================

pyinstaller --noconfirm --onefile --windowed ^
    --name "VideoSplitterPro" ^
    main.py

echo.
echo Done! Find your EXE inside the "dist" folder:
echo    dist\VideoSplitterPro.exe
echo.
echo NOTE: this local build does NOT bundle ffmpeg.exe automatically.
echo Place ffmpeg.exe and ffprobe.exe in this same folder before running
echo this script if you want them bundled, or install ffmpeg system-wide.
pause
