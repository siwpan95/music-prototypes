#!/usr/bin/env python3
"""
MusicStudio - 增强 DAW 界面
整合: Pro2 pygame_gui 框架 + Pro1 编排视图 + Pro4 引擎管道
"""
from __future__ import annotations
import sys
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Windows 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class DAWWindow:
    """
    增强 DAW 主窗口
    
    面板布局:
    ┌──────────────┬──────────────────────────────┐
    │              │                              │
    │  乐器面板    │     编排时间轴                │
    │  (左侧)     │     (中央)                    │
    │              │                              │
    ├──────────────┼──────────────────────────────┤
    │  情绪选择    │     播放控制                  │
    │  参数面板    │     (底部)                    │
    └──────────────┴──────────────────────────────┘
    """

    def __init__(self, mood: str = "happy", bpm: float = 120.0,
                 key: str = "C", complexity: int = 3, bars: int = 4):
        self.mood = mood
        self.bpm = bpm
        self.key = key
        self.complexity = complexity
        self.bars = bars
        
        self.running = False
        self._window = None
        self._manager = None
        self._orchestrator = None
        self._current_instruments: List[Dict] = []
        self._current_arrangement: Optional[Any] = None

    # ── 启动 ────────────────────────────────────────────────────────

    def run(self):
        """启动 GUI（纯 pygame_gui 模式，若无则回退到控制台）"""
        try:
            self._run_pygame_gui()
        except ImportError:
            print("[GUI] pygame/pygame_gui 未安装，启动控制台交互模式")
            self._run_cli_fallback()

    def _run_pygame_gui(self):
        """pygame_gui 完整 GUI 实现"""
        import pygame
        import pygame_gui

        pygame.init()
        W, H = 1280, 800
        self._window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        pygame.display.set_caption(f"MusicStudio - {self.mood} @ {self.bpm}BPM")
        self._manager = pygame_gui.UIManager((W, H))
        self._manager.set_visual_debug_mode(False)

        self.running = True
        clock = pygame.time.Clock()

        # ── UI 元素 ──────────────────────────────────────────────
        # 情绪选择
        moods = ["happy", "sad", "epic", "calm", "tense"]
        mood_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=moods, starting_option=self.mood,
            relative_rect=pygame.Rect(20, 20, 140, 30),
            manager=self._manager,
        )

        # 生成按钮
        generate_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(180, 20, 120, 30),
            text="Generate",
            manager=self._manager,
        )

        # 状态文本
        status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(320, 20, 600, 30),
            text=f"Ready | Key: {self.key} | BPM: {self.bpm} | Complexity: {self.complexity}",
            manager=self._manager,
        )

        # 编排预览文本
        preview_label = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(20, 70, 1200, 200),
            html_text=self._get_arrangement_html(),
            manager=self._manager,
        )

        # 乐器列表
        instruments_label = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(20, 290, 1200, 200),
            html_text="<b>Instruments:</b><br>Click Generate to compose...",
            manager=self._manager,
        )

        # 导出按钮
        export_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, 510, 120, 30),
            text="Export WAV",
            manager=self._manager,
        )

        while self.running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

                if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == mood_dropdown:
                        self.mood = event.text
                        preview_label.set_text(self._get_arrangement_html())
                        status_label.set_text(f"Mood: {self.mood} | Key: {self.key} | BPM: {self.bpm}")

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == generate_btn:
                        status_label.set_text("Generating... please wait")
                        instruments, events = self._do_orchestrate()
                        self._current_instruments = instruments
                        self._current_arrangement = events
                        instruments_label.set_text(self._get_instruments_html(instruments))
                        status_label.set_text(
                            f"Done | {len(instruments)} instruments | {len(events)} bars "
                            f"| Mood: {self.mood}"
                        )

                    elif event.ui_element == export_btn:
                        status_label.set_text("Exporting WAV...")
                        self._do_export()
                        status_label.set_text(f"Exported: Output/Exports/mixdown.wav")

                self._manager.process_events(event)

            self._manager.update(time_delta)
            self._window.fill((30, 30, 35))
            self._manager.draw_ui(self._window)
            pygame.display.update()

        pygame.quit()

    def _run_cli_fallback(self):
        """控制台交互模式回退"""
        from Engine.orchestration import print_arrangement_preview
        from Engine.composition import compose, DRUM_PATTERNS

        print("\n" + "=" * 60)
        print("  MusicStudio - Console Mode")
        print("=" * 60)

        # 展示编排
        events = print_arrangement_preview(self.mood)

        # 生成作曲
        instruments = [
            {"name": "Piano", "type": "melody", "pattern": "scale"},
            {"name": "Chords", "type": "chords", "voicing": "block"},
            {"name": "Bass", "type": "bass", "pattern": "walking"},
            {"name": "Drums", "type": "drums", "is_drum": True, "pattern": "pop"},
        ]
        results = compose(instruments, key=self.key, bars=self.bars)
        print(f"\n  Generated {len(results)} tracks:")
        for r in results:
            print(f"    {r.track_name}: {len(r.notes)} notes")

        print("\n  [INFO] Run 'python main.py --mode gui' for DAW interface")
        print("  [INFO] Install pygame, pygame_gui for full GUI experience\n")

    # ── 编排逻辑 ────────────────────────────────────────────────────

    def _do_orchestrate(self) -> Tuple[List[Dict], Any]:
        """执行完整的配器+作曲流程"""
        from Engine.orchestration import IntelligentOrchestrator
        from Engine.composition import compose

        orch = IntelligentOrchestrator()
        instruments, events = orch.orchestrate(
            mood=self.mood, key=self.key, bpm=self.bpm,
            complexity=self.complexity, bars=self.bars,
        )

        # 作曲
        compose(instruments, key=self.key, bpm=self.bpm, bars=self.bars)

        return instruments, events

    def _do_export(self):
        """导出完整 WAV 文件"""
        from Engine.core.mixer import MusicMixer
        from Engine.composition import batch_generate
        from Engine.midi.converter import batch_json_to_midi
        from Engine.audio.synthesizer import batch_synthesize, load_audio
        from Engine.effects.effects import apply_effect_chain
        import soundfile as sf
        import glob

        for d in ["Data/Instruments", "Data/MIDI", "Data/Audio",
                  "Output/Exports"]:
            os.makedirs(d, exist_ok=True)
            for f in glob.glob(os.path.join(d, "*")):
                try: os.remove(f)
                except: pass

        if not self._current_instruments:
            self._do_orchestrate()

        # 生成 → MIDI → 合成 → 混音 → 导出
        instruments = self._current_instruments or [
            {"name": "Piano",    "program": 0, "type": "melody", "octave": 5, "pattern": "scale"},
            {"name": "Chords",   "program": 0, "type": "chords", "voicing": "block"},
            {"name": "Bass",     "program": 33, "type": "bass", "octave": 3, "pattern": "walking"},
            {"name": "Drums",    "program": 0, "type": "drums", "is_drum": True, "pattern": "pop"},
        ]

        batch_generate(instruments, "Data/Instruments", key=self.key,
                       bpm=self.bpm, bars=self.bars)
        batch_json_to_midi("Data/Instruments", "Data/MIDI", self.bpm)
        audio_paths = batch_synthesize("Data/MIDI", "Data/Audio")

        mixer = MusicMixer()
        from Engine.orchestration import IntelligentOrchestrator
        orch = IntelligentOrchestrator()
        orch.orchestrate(mood=self.mood, complexity=self.complexity,
                         key=self.key, bpm=self.bpm)

        if audio_paths:
            for ap in audio_paths:
                audio = load_audio(ap)
                name = os.path.splitext(os.path.basename(ap))[0]
                if audio is not None:
                    mixer.add_track(name, audio)

        final = mixer.mix()
        final = apply_effect_chain(final, [
            {"type": "eq", "low_gain": 1.05, "mid_gain": 1.0, "high_gain": 0.98},
            {"type": "compressor", "threshold": 0.6, "ratio": 3.0},
            {"type": "reverb", "amount": 0.25},
        ])

        os.makedirs("Output/Exports", exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"Output/Exports/{self.mood}_{stamp}.wav"
        sf.write(export_path, final, mixer.sample_rate)
        print(f"\n  [Export] {export_path}")

    # ── UI 文本 ─────────────────────────────────────────────────────

    def _get_arrangement_html(self) -> str:
        """生成编排预览 HTML"""
        from Engine.orchestration import AutomaticArranger
        arr = AutomaticArranger()
        return arr.get_summary(self.mood)

    def _get_instruments_html(self, instruments: List[Dict]) -> str:
        """生成乐器列表 HTML"""
        lines = ["<b>Instruments:</b>"]
        for i, inst in enumerate(instruments):
            lines.append(f"  [{i+1}] {inst.get('name','Track')} "
                         f"({inst.get('type','melody')}) "
                         f"program={inst.get('program',0)}")
        return "<br>".join(lines)


def launch_daw(mood: str = "happy", bpm: float = 120.0,
               key: str = "C", complexity: int = 3,
               bars: int = 4):
    """启动 DAW 窗口"""
    window = DAWWindow(mood=mood, bpm=bpm, key=key,
                        complexity=complexity, bars=bars)
    window.run()


if __name__ == "__main__":
    launch_daw(mood="happy")
