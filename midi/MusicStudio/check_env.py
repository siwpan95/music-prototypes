#!/usr/bin/env python3
"""
MusicStudio - 环境诊断工具
来源: Pro3 QuickFix.bat + 增强诊断
"""
import sys
import os
import shutil

def check(msg, ok=True):
    status = "[OK]" if ok else "[MISS]"
    print(f"  {status:<8} {msg}")

def main():
    print("\n" + "=" * 60)
    print("  MusicStudio - Environment Diagnostics")
    print("=" * 60)
    print()

    # Python
    ver = sys.version_info
    print(f"  Python: {ver.major}.{ver.minor}.{ver.micro}")
    print(f"  Path:   {sys.executable}")
    print(f"  Arch:   {'64-bit' if sys.maxsize > 2**32 else '32-bit'}")
    print()

    # 核心库
    print("  --- Core Libraries ---")
    for name, pkg in [
        ("numpy", "numpy"), ("scipy", "scipy"),
        ("pretty_midi", "pretty_midi"), ("soundfile", "soundfile"),
        ("json", "json"), ("pathlib", "pathlib"),
    ]:
        try:
            m = __import__(name)
            ver_str = getattr(m, "__version__", "unknown")
            check(f"{pkg} ({ver_str})")
        except ImportError:
            check(f"{pkg}", False)

    print()
    print("  --- GUI Libraries ---")
    for name, pkg in [
        ("pygame", "pygame"), ("pygame_gui", "pygame_gui"),
    ]:
        try:
            m = __import__(name)
            ver_str = getattr(m, "__version__", "unknown")
            check(f"{pkg} ({ver_str})")
        except ImportError:
            check(f"{pkg}", False)

    print()
    print("  --- Optional ---")
    try:
        import yaml
        check("PyYAML")
    except ImportError:
        check("PyYAML", False)

    # SoundFont
    sf_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SoundFonts")
    sf_files = []
    if os.path.isdir(sf_dir):
        sf_files = [f for f in os.listdir(sf_dir) if f.endswith(".sf2")]
    
    if sf_files:
        check(f"SoundFont: {sf_files[0]}")
    else:
        check("SoundFont", False)
        print("          (download FluidR3_GM.sf2 to SoundFonts/ for better quality)")

    # 音频设备
    print()
    print("  --- System ---")
    try:
        import sounddevice
        devs = sounddevice.query_devices()
        audio_out = [d for d in devs if d["max_output_channels"] > 0]
        check(f"Audio outputs: {len(audio_out)} devices")
    except (ImportError, Exception):
        check("sounddevice not installed (optional)")

    print()
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
