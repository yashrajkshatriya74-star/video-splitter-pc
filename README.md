# Video Splitter Pro — Windows

Local Windows 10 desktop app — split any video into clips, either by a
fixed number of seconds per clip, or into an equal number of parts.
Same dark ocean-blue interface as Audio Splitter Pro.

## Features
- Select a video file (mp4, mov, mkv, avi, webm, m4v)
- Preview it with a play button (built-in video preview panel)
- Two split modes:
  - **Fixed duration per clip** — dial/spinbox, 5–600 seconds
  - **Equal number of parts** — enter how many pieces you want
- **No re-encoding** — uses FFmpeg's `-c copy` mode, so splitting is
  near-instant and there's zero quality loss (splits may land on the
  nearest keyframe rather than the exact frame — this is normal for
  copy-mode splitting)
- Export → pick any folder → clips save there automatically

---

## How to build this (same proven method as Audio Splitter Pro)

### Option D — GitHub Actions (recommended, no terminal, cloud build)
1. Create a GitHub repo, upload all files in this folder — `main.py`,
   `requirements.txt`, `build_exe.bat`, `installer.iss`, `README.md`,
   and the `.github` folder (enable **"Show hidden items"** in File
   Explorer's View tab to see and drag in `.github`)
2. Commit → click **Actions** tab → a build starts automatically
3. Takes ~5-8 minutes (downloads FFmpeg, builds the exe, builds the installer)
4. Green tick → **Artifacts** → download **`VideoSplitterPro-Setup-Installer`**
5. Unzip it, run **`VideoSplitterPro_Setup.exe`** — normal install
   wizard, Start Menu shortcut, Desktop icon, uninstaller — same as
   Audio Splitter Pro

FFmpeg is bundled inside automatically — nothing to install separately.

### Option A/B — Local build (needs Python + FFmpeg installed)
1. Install Python 3.10+ and FFmpeg (add to PATH)
2. `pip install -r requirements.txt`
3. Test: `python main.py`
4. Standalone exe: double-click `build_exe.bat` → `dist\VideoSplitterPro.exe`
   (place `ffmpeg.exe`/`ffprobe.exe` next to `main.py` first if you want
   them bundled into the exe; otherwise the exe will look for FFmpeg on
   your system PATH)

---

## Notes
- Split points can land on the nearest keyframe (not always frame-exact)
  because there's no re-encoding — this is what keeps it fast and
  lossless. A future re-encoding mode could add frame-exact cuts at the
  cost of speed and a slight quality hit.
