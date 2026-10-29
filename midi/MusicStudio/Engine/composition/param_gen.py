#!/usr/bin/env python3
"""
算法作曲模块 - 四项目精华整合
- Pro2: 旋律动机生成、贝斯行走低音、鼓节奏型库
- Pro1: 调式约束、声部引导规则
- Pro4: 批量参数生成管道
"""
from __future__ import annotations
import json
import os
import random
import math
from copy import deepcopy
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

from Engine.orchestration import SCALE_MAP, CHORD_MAP, CHORD_PROGRESSIONS


# ═══════════════════════════════════════════════════════════════════════
# Pro2 风格的节奏型库
# ═══════════════════════════════════════════════════════════════════════

RHYTHM_PATTERNS: Dict[str, List[float]] = {
    # 旋律节奏型
    "simple":    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    "swing":     [0.0, 0.67, 1.0, 1.67, 2.0, 2.67, 3.0, 3.67],
    "dotted":    [0.0, 0.75, 1.5, 2.0, 2.75, 3.5],
    "syncopated":[0.0, 0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25],
    "legato":    [0.0, 1.0, 2.0, 3.0],
    "staccato":  [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
                  2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75],
    "triplet":   [0.0, 0.33, 0.67, 1.0, 1.33, 1.67, 2.0, 2.33,
                  2.67, 3.0, 3.33, 3.67],
    "slow":      [0.0, 1.0, 2.0, 2.5, 3.0],
    "fast":      [0.0, 0.125, 0.25, 0.5, 0.625, 0.75, 1.0, 1.125,
                  1.25, 1.5, 1.625, 1.75, 2.0, 2.125, 2.25, 2.5,
                  2.625, 2.75, 3.0, 3.125, 3.25, 3.5, 3.625, 3.75],
}

# Pro2 鼓节奏型
DRUM_PATTERNS: Dict[str, Dict[str, List[float]]] = {
    "pop": {
        "kick":    [0.0, 1.0, 2.0, 3.0],
        "snare":   [1.0, 3.0],
        "hihat":   [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    },
    "rock": {
        "kick":    [0.0, 0.75, 2.0, 2.75],
        "snare":   [1.0, 3.0],
        "hihat":   [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    },
    "epic": {
        "kick":    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "snare":   [1.0, 3.0],
        "hihat":   [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
                    2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75],
        "crash":   [0.0, 2.0],
    },
    "full": {
        "kick":    [0.0, 0.75, 2.0, 2.5],
        "snare":   [1.0, 3.0],
        "hihat":   [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "tom":     [0.5, 1.5, 2.5, 3.5],
        "crash":   [0.0],
    },
    "full_epic": {
        "kick":    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "snare":   [0.5, 1.5, 2.5, 3.5],
        "hihat":   [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
                    2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75],
        "crash":   [0.0, 2.0],
    },
    "soft": {
        "kick":    [0.0, 2.0],
        "snare":   [2.0],
        "hihat":   [1.0, 3.0],
    },
    "military": {
        "snare":   [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "kick":    [0.0, 2.0],
        "crash":   [2.0],
    },
    "industrial": {
        "kick":    [0.0, 0.25, 0.75, 1.25, 2.0, 3.0],
        "snare":   [1.0, 3.0],
        "hihat":   [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
                    2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75],
        "tom":     [1.5, 3.5],
    },
    "tense": {
        "kick":    [0.0, 1.5, 3.0],
        "snare":   [0.5, 2.5],
        "hihat":   [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75],
        "tom":     [1.0, 3.0],
    },
    "ambient": {
        "kick":    [0.0],
        "snare":   [2.0],
        "hihat":   [1.0, 3.0],
        "bell":    [0.5, 2.5],
    },
    "simple": {
        "kick":    [0.0, 2.0],
        "snare":   [1.0, 3.0],
        "hihat":   [0.0, 1.0, 2.0, 3.0],
    },
    "none": {},
}


# ═══════════════════════════════════════════════════════════════════════
# 音符映射（Pro2 + Pro1）
# ═══════════════════════════════════════════════════════════════════════

DRUM_NOTE_MAP = {
    "kick":   36,  # C2
    "snare":  38,  # D2
    "hihat":  42,  # F#2
    "tom":    45,  # A2
    "crash":  49,  # C#3
    "bell":   75,  # D#5
    "ride":   51,  # D#3
}


# ═══════════════════════════════════════════════════════════════════════
# 旋律生成器 (Pro2 增强版)
# ═══════════════════════════════════════════════════════════════════════

class MelodyGenerator:
    """旋律生成器 - 支持动机/变奏/即兴"""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate(self, key: str = "C", octave: int = 5,
                 bars: int = 4, pattern: str = "scale",
                 style: str = "pop", complexity: int = 3) -> List[Dict]:
        """
        生成旋律音符列表

        Args:
            key: 调性 (C, G, D, etc.)
            octave: 基准八度 (MIDI: 5 = C5)
            bars: 小节数
            pattern: 节奏型名 (scale/arpeggio/dotted/syncopated/legato/fast)
            style: 风格标签
            complexity: 复杂度 1-5
        """
        scale = SCALE_MAP.get(key, SCALE_MAP["C"])
        rhythm = RHYTHM_PATTERNS.get(pattern, RHYTHM_PATTERNS["simple"])
        notes = []

        # 根据复杂度调整跳音习惯
        max_leap = 2 if complexity <= 2 else (4 if complexity <= 3 else 7)

        for bar in range(bars):
            bar_start = bar * 4.0
            bar_rhythm = [t for t in rhythm if bar_start <= t < bar_start + 4.0]

            prev_note_idx = None
            for t in bar_rhythm:
                beat_in_bar = t - bar_start

                # Pro2 风格：强拍趋向根音/五度音
                if beat_in_bar in (0.0, 2.0):
                    note_idx = random.choice([0, 4, 7])
                elif beat_in_bar in (0.5, 2.5):
                    note_idx = random.choice([2, 5, 9])
                else:
                    note_idx = random.randint(0, len(scale) - 1)

                # 声部引导约束 (Pro1 11.py)：避免过大跳跃
                if prev_note_idx is not None and abs(note_idx - prev_note_idx) > max_leap:
                    # 平滑化：选择最近的可行音
                    step = 1 if note_idx > prev_note_idx else -1
                    note_idx = prev_note_idx + step
                    note_idx = max(0, min(len(scale) - 1, note_idx))

                midi_note = max(0, min(127, scale[note_idx % len(scale)] + int(octave) * 12))

                # 根据风格微调速度
                vel = random.randint(70, 110)
                if pattern == "legato":
                    duration = 0.9
                elif pattern == "staccato":
                    duration = 0.3
                else:
                    duration = 0.5 + 0.2 * complexity / 5.0

                notes.append({
                    "note": midi_note,
                    "time": t,
                    "duration": duration * random.uniform(0.8, 1.2),
                    "velocity": vel,
                    "bar": bar,
                })
                prev_note_idx = note_idx

        return notes

    def generate_motif(self, key: str = "C", octave: int = 5,
                       length: int = 4) -> List[int]:
        """生成动机（短旋律片段）"""
        scale = SCALE_MAP.get(key, SCALE_MAP["C"])
        # 小型动机：3-6 个音
        base = max(0, min(127, scale[0] + octave * 12))
        return [base + random.choice([0, 2, 4, 5, 7])
                for _ in range(length)]

    def apply_variation(self, motif: List[int], variation_type: str = "transpose"
                        ) -> List[int]:
        """动机变奏"""
        if variation_type == "transpose":
            shift = random.choice([2, 4, 5, 7, -2, -4, -5])
            return [n + shift for n in motif]
        elif variation_type == "retrograde":
            return list(reversed(motif))
        elif variation_type == "augment":
            return [n + 12 for n in motif]
        elif variation_type == "diminish":
            return [n - 12 for n in motif]
        elif variation_type == "rhythmic":
            return [motif[i] for i in range(len(motif))
                    if i % 2 == 0]  # 保留一半
        return motif


# ═══════════════════════════════════════════════════════════════════════
# 和弦生成器 (Pro2 + Pro1 合并)
# ═══════════════════════════════════════════════════════════════════════

class ChordGenerator:
    """和弦生成器"""

    def generate(self, key: str = "C", style: str = "pop",
                 bars: int = 4, voicing: str = "block",
                 density: float = 0.7) -> List[Dict]:
        """
        生成和弦音符列表

        Args:
            key: 调性
            style: 和弦进行风格
            bars: 小节数
            voicing: 排列方式 (block/arpeggiated/sustained/open)
            density: 和弦密度 0.0-1.0
        """
        progression = CHORD_PROGRESSIONS.get(style, CHORD_PROGRESSIONS["pop"])
        chord_map = CHORD_MAP.get(key, CHORD_MAP["C"])

        notes = []
        for bar in range(bars):
            chord_degree = progression[bar % len(progression)]
            chord_notes = chord_map.get(chord_degree, [60, 64, 67])

            bar_start = bar * 4.0

            if voicing == "block":
                # 整小节同时发声
                if random.random() < density:
                    for cn in chord_notes:
                        notes.append({
                            "note": cn,
                            "time": bar_start,
                            "duration": 3.8,
                            "velocity": random.randint(60, 90),
                            "bar": bar,
                        })
            elif voicing == "arpeggiated":
                # 分解和弦
                for i, cn in enumerate(chord_notes):
                    if random.random() < density:
                        notes.append({
                            "note": cn,
                            "time": bar_start + i * 0.5,
                            "duration": 1.5,
                            "velocity": random.randint(50, 80),
                            "bar": bar,
                        })
            elif voicing == "sustained":
                # 持续和弦
                for cn in chord_notes:
                    notes.append({
                        "note": cn,
                        "time": bar_start,
                        "duration": 3.9,
                        "velocity": random.randint(40, 70),
                        "bar": bar,
                    })
            elif voicing == "open":
                # 开放排列（跨越两个八度）
                spaced = [chord_notes[0]] + [chord_notes[1]] + [chord_notes[2] + 12]
                for i, cn in enumerate(spaced):
                    if random.random() < density:
                        notes.append({
                            "note": cn,
                            "time": bar_start,
                            "duration": 3.5 + i * 0.3,
                            "velocity": random.randint(50, 80),
                            "bar": bar,
                        })
            else:
                # 默认：block
                for cn in chord_notes:
                    notes.append({
                        "note": cn,
                        "time": bar_start,
                        "duration": 3.8,
                        "velocity": random.randint(60, 90),
                        "bar": bar,
                    })

        return notes


# ═══════════════════════════════════════════════════════════════════════
# 贝斯生成器 (Pro2 walking bass + Pro1 约束)
# ═══════════════════════════════════════════════════════════════════════

class BassGenerator:
    """贝斯/低音线生成器"""

    def generate(self, key: str = "C", octave: int = 0,
                 bars: int = 4, pattern: str = "root",
                 complexity: int = 3) -> List[Dict]:
        """
        生成低音线

        Args:
            key: 调性
            octave: 相对八度偏移（0=C3区域, -1=C2, 1=C4）
            bars: 小节数
            pattern: root/walking/groove/power/ostinato/drone
            complexity: 复杂度
        """
        scale = SCALE_MAP.get(key, SCALE_MAP["C"])
        # 低音偏移：从C4 scale降2个八度到C2区域
        bass_shift = -24 + octave * 12

        def _bass_note(scale_degree: int) -> int:
            return max(0, min(127, scale[scale_degree % len(scale)] + bass_shift))

        notes = []

        if pattern == "drone" or pattern == "none":
            root = _bass_note(0)
            for bar in range(bars):
                notes.append({
                    "note": root, "time": bar * 4.0,
                    "duration": 3.9, "velocity": 60, "bar": bar,
                })
            return notes

        for bar in range(bars):
            bar_start = bar * 4.0

            if pattern == "root":
                for beat in (0.0, 1.0, 2.0, 3.0):
                    notes.append({
                        "note": _bass_note(0),
                        "time": bar_start + beat, "duration": 0.8,
                        "velocity": random.randint(60, 90), "bar": bar,
                    })
            elif pattern == "walking":
                chord_idx = bar % 3
                chord_offsets = [[0, 4, 7], [2, 5, 9], [4, 7, 11]]
                offsets = chord_offsets[chord_idx]
                for beat_idx, beat in enumerate([0.0, 1.0, 2.0, 3.0]):
                    offset = offsets[beat_idx % len(offsets)]
                    notes.append({
                        "note": _bass_note(offset),
                        "time": bar_start + beat, "duration": 0.8,
                        "velocity": random.randint(60, 90), "bar": bar,
                    })
            elif pattern == "groove":
                for beat in (0.0, 0.75, 2.0, 2.75):
                    notes.append({
                        "note": _bass_note(0),
                        "time": bar_start + beat, "duration": 0.5,
                        "velocity": random.randint(70, 100), "bar": bar,
                    })
            elif pattern == "power":
                for i in range(8):
                    note_idx = random.choice([0, 4, 7])
                    notes.append({
                        "note": _bass_note(note_idx),
                        "time": bar_start + i * 0.5, "duration": 0.4,
                        "velocity": random.randint(80, 110), "bar": bar,
                    })
            elif pattern == "ostinato":
                for i in range(8):
                    note_idx = [0, 4, 7, 4][i % 4]
                    notes.append({
                        "note": _bass_note(note_idx),
                        "time": bar_start + i * 0.5, "duration": 0.45,
                        "velocity": random.randint(65, 95), "bar": bar,
                    })
            else:
                for beat in (0.0, 2.0):
                    notes.append({
                        "note": _bass_note(0),
                        "time": bar_start + beat, "duration": 1.8,
                        "velocity": random.randint(60, 80), "bar": bar,
                    })

        return notes


# ═══════════════════════════════════════════════════════════════════════
# 鼓生成器 (Pro2 完整鼓节奏型)
# ═══════════════════════════════════════════════════════════════════════

class DrumGenerator:
    """鼓/打击乐生成器"""

    def generate(self, bars: int = 4, pattern: str = "pop",
                 style: str = "pop") -> List[Dict]:
        """
        生成鼓音符

        Args:
            bars: 小节数
            pattern: 鼓节奏型名
            style: 风格标签（回退用）
        """
        drum_pattern = DRUM_PATTERNS.get(pattern, DRUM_PATTERNS.get(style, DRUM_PATTERNS["pop"]))
        notes = []

        for bar in range(bars):
            bar_start = bar * 4.0
            for drum_name, hits in drum_pattern.items():
                midi_note = DRUM_NOTE_MAP.get(drum_name, 36)
                for hit in hits:
                    time_in_bar = hit + bar_start
                    if 0 <= (hit % 4.0) < 1:
                        vel = random.randint(90, 120)  # 强拍
                    else:
                        vel = random.randint(60, 90)   # 弱拍
                    notes.append({
                        "note": midi_note,
                        "time": time_in_bar,
                        "duration": 0.2,
                        "velocity": vel,
                        "bar": bar,
                        "drum": drum_name,
                    })

        return notes


# ═══════════════════════════════════════════════════════════════════════
# 批量生成 API
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ComposeResult:
    """作曲结果"""
    track_name: str
    instrument: Dict
    notes: List[Dict]
    midi_notes: Optional[List[Dict]] = None


def compose(instruments: List[Dict], key: str = "C",
            bpm: float = 120.0, bars: int = 4) -> List[ComposeResult]:
    """
    一键作曲：根据乐器配置生成所有音轨

    这是 Pro2 pipeline 的核心：params → json → midi → audio
    """
    melody_gen = MelodyGenerator()
    chord_gen = ChordGenerator()
    bass_gen = BassGenerator()
    drum_gen = DrumGenerator()

    results = []

    for inst in instruments:
        name = inst.get("name", "Track")
        inst_type = inst.get("type", "melody")
        
        if inst.get("is_drum", False) or inst_type == "drums":
            notes = drum_gen.generate(
                bars=bars,
                pattern=inst.get("pattern", inst.get("style", "pop")),
            )
        elif inst_type == "chords":
            notes = chord_gen.generate(
                key=key, bars=bars,
                voicing=inst.get("voicing", "block"),
                style=inst.get("style", "pop"),
            )
        elif inst_type == "bass" or "bass" in name.lower():
            notes = bass_gen.generate(
                key=key, bars=bars,
                octave=inst.get("octave", 3),
                pattern=inst.get("pattern", "root"),
            )
        else:
            notes = melody_gen.generate(
                key=key, bars=bars,
                octave=inst.get("octave", 5),
                pattern=inst.get("pattern", "scale"),
                style=inst.get("style", "pop"),
            )

        results.append(ComposeResult(
            track_name=name,
            instrument=inst,
            notes=notes,
        ))

    return results


def batch_generate(instruments: List[Dict], output_dir: str,
                   key: str = "C", bpm: float = 120.0,
                   bars: int = 4) -> List[str]:
    """
    批量生成并保存 JSON 参数文件到磁盘
    输出格式匹配 json_to_midi 的期望结构
    """
    os.makedirs(output_dir, exist_ok=True)
    results = compose(instruments, key, bpm, bars)
    saved_paths = []

    for result in results:
        safe_name = result.track_name.replace(" ", "_").replace("/", "_")
        filepath = os.path.join(output_dir, f"{safe_name}.json")
        inst = result.instrument

        # 转换为 json_to_midi 期望的格式
        converted_notes = []
        for n in result.notes:
            converted_notes.append({
                "pitch": n.get("note", n.get("pitch", 60)),
                "velocity": n.get("velocity", 80),
                "start": n.get("time", n.get("start", 0.0)),
                "duration": n.get("duration", 0.5),
            })

        data = {
            "metadata": {
                "instrument_name": result.track_name,
                "program": inst.get("program", 0),
                "channel": 9 if inst.get("is_drum", False) else 0,
                "is_drum": inst.get("is_drum", False),
                "creation_time": "",
                "version": "2.0",
            },
            "parameters": {
                "volume": 100,
                "pan": 64,
            },
            "notes": converted_notes,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        saved_paths.append(filepath)

    return saved_paths


def create_instrument_config(name: str, program: int = 0,
                              inst_type: str = "melody",
                              octave: int = 5,
                              pattern: str = "scale",
                              **kwargs) -> Dict:
    """创建乐器配置（保持向后兼容）"""
    return {"name": name, "program": program, "type": inst_type,
            "octave": octave, "pattern": pattern, **kwargs}


def generate_melody(notes: List[int] = None, key: str = "C",
                    octave: int = 5, bars: int = 4,
                    pattern: str = "scale") -> List[Dict]:
    """快速生成旋律（独立函数，保持向后兼容）"""
    gen = MelodyGenerator()
    return gen.generate(key=key, octave=octave, bars=bars, pattern=pattern)


# ── 信息查询 ─────────────────────────────────────────────────────────

def list_rhythm_patterns() -> List[str]:
    """列出所有可用的节奏型"""
    return list(RHYTHM_PATTERNS.keys())


def list_drum_patterns() -> List[str]:
    """列出所有可用的鼓节奏型"""
    return list(DRUM_PATTERNS.keys())


if __name__ == "__main__":
    print("=" * 60)
    print("  MusicStudioPro - Algorithm Composition")
    print("  (Pro2 + Pro1 + Pro4 合并)")
    print("=" * 60)

    # 演示每个生成器
    mg = MelodyGenerator()
    melody = mg.generate(key="C", pattern="scale", bars=2)
    print(f"\n  Melody: {len(melody)} notes")
    print(f"  First 5: {[m['note'] for m in melody[:5]]}")

    cg = ChordGenerator()
    chords = cg.generate(key="C", voicing="block", bars=2)
    print(f"\n  Chords: {len(chords)} notes")

    bg = BassGenerator()
    bass = bg.generate(key="C", pattern="walking", bars=2)
    print(f"\n  Bass: {len(bass)} notes")

    dg = DrumGenerator()
    drums = dg.generate(pattern="full", bars=2)
    print(f"\n  Drums: {len(drums)} notes")

    # 完整作曲演示
    print("\n  ── Full Composition Demo ──")
    instruments = [
        {"name": "Piano", "type": "melody", "pattern": "scale"},
        {"name": "Chords", "type": "chords", "voicing": "block"},
        {"name": "Bass", "type": "bass", "pattern": "walking"},
        {"name": "Drums", "type": "drums", "is_drum": True, "pattern": "pop"},
    ]
    results = compose(instruments, key="C", bars=2)
    for r in results:
        print(f"    {r.track_name}: {len(r.notes)} notes")
