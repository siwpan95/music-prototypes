#!/usr/bin/env python3
"""
MusicStudio - 一键部署脚本
来源: Pro3 Install.bat + Pro4 setup.py
"""
from __future__ import annotations
import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()


def check_python():
    """检查 Python 版本"""
    ver = sys.version_info
    if ver.major < 3 or (ver.major == 3 and ver.minor < 8):
        print("[ERROR] 需要 Python 3.8+, 当前: {}.{}".format(ver.major, ver.minor))
        return False
    print(f"[OK] Python {ver.major}.{ver.minor}.{ver.micro}")
    return True

def install_deps():
    """安装 pip 依赖"""
    req_file = BASE_DIR / "requirements.txt"
    if not req_file.exists():
        print("[WARN] requirements.txt not found")
        return False
    print("[INFO] 安装 Python 依赖...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            cwd=str(BASE_DIR),
        )
        print("[OK] 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 依赖安装失败: {e}")
        return False

def create_dirs():
    """创建必需的目录结构"""
    dirs = [
        "Data/Instruments", "Data/MIDI", "Data/Audio",
        "Output/Exports", "Output/Renders", "Output/Projects", "Output/Stems",
        "SoundFonts", "Logs", "Config",
    ]
    for d in dirs:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
    print("[OK] 目录结构就绪")

def check_soundfont():
    """提示 SoundFont 下载"""
    sf_dir = BASE_DIR / "SoundFonts"
    sf_files = list(sf_dir.glob("*.sf2"))
    if sf_files:
        print(f"[OK] SoundFont 已就绪: {sf_files[0].name}")
    else:
        print("\n" + "=" * 60)
        print("  [INFO] 未检测到 SoundFont 文件")
        print()
        print("  软件合成器已内置 (纯 numpy)，但音质受限。")
        print("  如需高品质音频，请下载 SoundFont:")
        print()
        print("  推荐: FluidR3_GM.sf2")
        print("  - https://member.keymusician.com/Member/FluidR3_GM/")
        print()
        print("  下载后放入 SoundFonts/ 目录即可。")
        print("=" * 60)

def main():
    print("\n" + "=" * 60)
    print("  MusicStudio - Setup")
    print("=" * 60 + "\n")

    if not check_python():
        return 1

    create_dirs()

    user_input = input("  安装 Python 依赖? (pip install) [Y/n]: ").strip().lower()
    if user_input in ("", "y", "yes"):
        install_deps()

    check_soundfont()

    # 验证安装
    print("\n" + "=" * 60)
    print("  Setup 完成!")
    print("=" * 60)
    print()
    print("  快速开始:")
    print("    python main.py                        # 交互菜单")
    print("    python main.py --mode gui             # DAW 界面")
    print("    python main.py --mode batch --mood epic  # 一键生成")
    print("    MusicStudio.bat                       # Windows 启动")
    return 0

if __name__ == "__main__":
    sys.exit(main())
