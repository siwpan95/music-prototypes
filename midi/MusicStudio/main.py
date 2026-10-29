#!/usr/bin/env python3
"""
MusicStudio - 统一主入口
四合一整合: Pro1智能配器 + Pro2 DAW界面 + Pro3部署体系 + Pro4完整引擎

用法:
  python main.py                        # 交互菜单
  python main.py --mode gui             # 启动 DAW 界面
  python main.py --mode batch --mood epic    # 一键批处理
  python main.py --mode cli             # 交互式命令行
  python main.py --mode env             # 环境检查
  python main.py --mode arrange --mood epic  # 打印编排计划
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime

# ── 路径修复 ─────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    _BUNDLE = sys._MEIPASS  # type: ignore
    os.chdir(BASE_DIR)
    sys.path.insert(0, _BUNDLE)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# Windows 中文编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════
# 模式处理
# ═══════════════════════════════════════════════════════════════════════

def run_gui(mood="happy", bpm=120.0, key="C", complexity=3, bars=4):
    """启动增强 DAW GUI"""
    print("\n[Main] 启动 DAW GUI...")
    try:
        from Engine.gui.daw_window import launch_daw
        launch_daw(mood=mood, bpm=bpm, key=key, complexity=complexity, bars=bars)
    except ImportError as e:
        print(f"[Main] GUI 启动失败: {e}")
        print("[Main] 请安装: pip install pygame pygame-gui")
        print("[Main] 退回到控制台模式...")
        run_cli_interactive()


def run_batch(mood="happy", complexity=3, bpm=120.0, key="C", bars=4,
              output=None, soundfont=None):
    """纯命令行批处理：参数→MIDI→音频→混音→导出"""
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"Output/Exports/{mood}_{stamp}.wav"
    from Engine.composition import batch_generate, compose
    from Engine.midi.converter import batch_json_to_midi
    from Engine.audio.synthesizer import batch_synthesize, load_audio, find_soundfont
    from Engine.effects.effects import apply_effect_chain
    from Engine.orchestration import IntelligentOrchestrator, print_arrangement_preview
    import glob

    print("\n" + "=" * 60)
    print("  MusicStudio - Batch Processing")
    print("  " + "=" * 50)
    print("=" * 60)

    # ── 编排预览 ──────────────────────────────────────────────────
    events = print_arrangement_preview(mood)

    # ── 准备目录 + 清理 ───────────────────────────────────────────
    for d in ["Data/Instruments", "Data/MIDI", "Data/Audio",
              "Output/Exports", "Output/Renders", "Output/Stems"]:
        os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*")):
            try: os.remove(f)
            except: pass

    # ── 1. 智能配器 ───────────────────────────────────────────────
    print("[1/5] 智能配器...")
    orch = IntelligentOrchestrator()
    instruments, bar_events = orch.orchestrate(
        mood=mood, key=key, bpm=bpm,
        complexity=complexity, bars=bars,
    )
    print(f"      情绪: {mood} | 乐器: {[i['name'] for i in instruments]}")
    print(f"      段落: {len(orch.section_plan)} 段, {len(bar_events)} 小节")

    # ── 2. 算法作曲 ───────────────────────────────────────────────
    print("[2/5] 算法作曲...")
    batch_generate(instruments, "Data/Instruments", key=key, bpm=bpm, bars=bars)

    # ── 3. JSON→MIDI ──────────────────────────────────────────────
    print("[3/5] JSON→MIDI 转换...")
    batch_json_to_midi("Data/Instruments", "Data/MIDI", float(bpm))

    # ── 4. MIDI→音频合成 ─────────────────────────────────────────
    print("[4/5] 音频合成...")
    sf_path = soundfont or find_soundfont()
    audio_paths = batch_synthesize("Data/MIDI", "Data/Audio", sf_path)

    # ── 5. 混音 + 效果 + 导出 ─────────────────────────────────────
    print("[5/5] 混音与导出...")
    from Engine.core.mixer import MusicMixer
    mixer = MusicMixer()

    # 加载合成的音频轨道
    if audio_paths:
        for ap in audio_paths:
            audio = load_audio(ap)
            name = os.path.splitext(os.path.basename(ap))[0]
            if audio is not None and len(audio) > 0:
                mixer.add_track(name, audio)

    final = mixer.mix()

    # 主效果链 (EQ → Compressor → Reverb)
    final = apply_effect_chain(final, [
        {"type": "eq", "low_gain": 1.05, "mid_gain": 1.0, "high_gain": 0.98},
        {"type": "compressor", "threshold": 0.6, "ratio": 3.0},
        {"type": "reverb", "amount": 0.25},
    ])

    import soundfile as sf
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    sf.write(output, final, mixer.sample_rate)

    duration = len(final) / mixer.sample_rate
    print(f"\n" + "=" * 60)
    print(f"  [DONE] {output}")
    print(f"  Duration: {duration:.1f}s | Mood: {mood} | BPM: {bpm}")
    print("=" * 60 + "\n")
    return output


def run_cli_interactive():
    """交互式命令行模式"""
    from Engine.orchestration import AutomaticArranger

    arranger = AutomaticArranger()
    moods = arranger.list_moods()

    print("\n" + "=" * 60)
    print("  MusicStudio - Interactive CLI")
    print("=" * 60)
    print(f"\n  Available Moods: {', '.join(moods)}")
    print()

    mood = input(f"  Mood [{moods[0]}]: ").strip().lower()
    if mood not in moods:
        mood = moods[0]

    # 显示编排预览
    arranger.print_arrangement_preview(mood)

    complexity = input("  Complexity (1-5) [3]: ").strip()
    complexity = int(complexity) if complexity.isdigit() and 1 <= int(complexity) <= 5 else 3

    bpm = input("  BPM [120]: ").strip()
    bpm = int(bpm) if bpm.isdigit() else 120

    key = input("  Key (C/G/D/A/F) [C]: ").strip().upper()
    key = key if key else "C"

    bars = input("  Bars [8]: ").strip()
    bars = int(bars) if bars.isdigit() else 8

    output = input("  Output path [Output/Exports/mixdown.wav]: ").strip()
    output = output or "Output/Exports/mixdown.wav"

    run_batch(mood=mood, complexity=complexity, bpm=bpm,
              key=key, bars=bars, output=output)


def run_env_check():
    """运行环境检查"""
    print("\n" + "=" * 60)
    print("  MusicStudio - Environment Check")
    print("=" * 60)

    checks = {
        "numpy": "numpy",
        "scipy": "scipy",
        "pretty_midi": "pretty_midi",
        "soundfile": "soundfile",
        "pygame": "pygame",
        "pygame_gui": "pygame_gui",
        "yaml": "PyYAML",
    }

    all_ok = True
    for import_name, pkg_name in checks.items():
        try:
            __import__(import_name)
            print(f"  [OK]    {pkg_name}")
        except ImportError:
            print(f"  [MISS]  {pkg_name}")
            all_ok = False

    # 检查 SoundFont
    from Engine.audio.synthesizer import find_soundfont
    sf = find_soundfont()
    if sf:
        print(f"  [OK]    SoundFont: {sf}")
    else:
        print(f"  [INFO]  SoundFont: not found (optional for better quality)")

    print("\n" + ("  All checks passed!" if all_ok else "  Some packages missing."))
    print("=" * 60 + "\n")
    return all_ok


def run_arrangement_view(mood="happy"):
    """仅显示编排计划（不生成音频）"""
    from Engine.orchestration import AutomaticArranger, IntelligentOrchestrator

    arranger = AutomaticArranger()
    import_arrangement_preview = arranger.print_arrangement_preview
    print_arrangement_preview(mood)

    # 也显示乐器模板
    orch = IntelligentOrchestrator()
    instruments, _ = orch.orchestrate(mood=mood)
    print(f"  Instruments for '{mood}':")
    for i, inst in enumerate(instruments):
        print(f"    [{i+1}] {inst['name']:<12s} type={inst.get('type','melody'):<8s} "
              f"program={inst.get('program',0):<3d} "
              f"pattern={inst.get('pattern','-')}")


# ═══════════════════════════════════════════════════════════════════════
# 交互式启动菜单 (无参数时)
# ═══════════════════════════════════════════════════════════════════════

def interactive_menu():
    """交互式主菜单"""
    print("\n" + "=" * 60)
    print("  MusicStudio v4.0")
    print("  四合一整合: 智能配器 | 算法作曲 | DAW界面 | 部署体系")
    print("=" * 60)
    print()
    print("  [1] Start DAW GUI          (pygame_gui)")
    print("  [2] Batch Process (all moods)")
    print("  [3] Interactive CLI")
    print("  [4] View Arrangement Plan")
    print("  [5] Environment Check")
    print("  [6] Quick Demo (happy, 8 bars)")
    print("  [q] Quit")
    print()

    choice = input("  Select [1]: ").strip().lower()

    if choice == "1" or choice == "":
        run_gui()
    elif choice == "2":
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for m in ["happy", "sad", "epic", "calm", "tense"]:
            output = f"Output/Exports/{m}_{stamp}.wav"
            print(f"\n  {'─' * 50}")
            print(f"  Batch: {m.upper()}")
            print(f"  {'─' * 50}")
            run_batch(mood=m, output=output)
        print("\n  [DONE] All 5 moods processed.")
    elif choice == "3":
        run_cli_interactive()
    elif choice == "4":
        run_arrangement_view()
    elif choice == "5":
        run_env_check()
    elif choice == "6":
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_batch(mood="happy", bars=8, output=f"Output/Exports/quick_demo_{stamp}.wav")
    elif choice == "q":
        print("  Goodbye!")
    else:
        print(f"  Unknown option: {choice}")


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MusicStudio v4.0 - 四合一音乐制作系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Interactive menu
  python main.py --mode gui                   # DAW GUI
  python main.py --mode batch --mood epic     # Batch export
  python main.py --mode cli                   # CLI mode
  python main.py --mode arrange --mood sad    # View arrangement
  python main.py --mode env                   # Check environment
        """)
    parser.add_argument("--mode", choices=["gui", "batch", "cli", "env", "arrange"],
                        help="启动模式（无参数则显示交互菜单）")
    parser.add_argument("--mood", default="happy",
                        choices=["happy", "sad", "epic", "calm", "tense",
                                 "romantic", "energetic", "mysterious"])
    parser.add_argument("--complexity", type=int, default=3)
    parser.add_argument("--bpm", type=int, default=120)
    parser.add_argument("--key", default="C")
    parser.add_argument("--bars", type=int, default=4)
    parser.add_argument("--output", default=None,
                        help="输出文件路径（默认：Output/Exports/{mood}_{timestamp}.wav）")
    parser.add_argument("--soundfont", default=None)

    args = parser.parse_args()

    if args.mode is None:
        interactive_menu()
    elif args.mode == "gui":
        run_gui(mood=args.mood, bpm=args.bpm, key=args.key,
                complexity=args.complexity, bars=args.bars)
    elif args.mode == "batch":
        run_batch(mood=args.mood, complexity=args.complexity, bpm=args.bpm,
                  key=args.key, bars=args.bars, output=args.output,
                  soundfont=args.soundfont)
    elif args.mode == "cli":
        run_cli_interactive()
    elif args.mode == "env":
        run_env_check()
    elif args.mode == "arrange":
        run_arrangement_view(args.mood)
