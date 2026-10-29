#!/usr/bin/env python3
"""
AutomaticArranger - 段落级智能编排
来源: Pro1 (13.py) - 小节级事件调度，段落A/B/C自动分配
增强: 整合 Pro2 的节奏型生成 + Pro4 的情绪映射
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import random
import math


class SectionKind(Enum):
    INTRO = "intro"
    VERSE = "verse"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    SOLO = "solo"
    BREAKDOWN = "breakdown"


class EnergyLevel(Enum):
    LOW = 1
    MEDIUM_LOW = 2
    MEDIUM = 3
    MEDIUM_HIGH = 4
    HIGH = 5


# ═══════════════════════════════════════════════════════════════════════
# 编排事件系统
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class BarEvent:
    """小节级编排事件"""
    bar_index: int
    active_tracks: List[str]           # 本小节活跃音轨
    muted_tracks: List[str]            # 本小节静音音轨
    solo_track: Optional[str] = None    # 独奏音轨（如有）
    velocity_mod: float = 1.0          # 力度缩放
    density_mod: float = 1.0           # 音符密度缩放
    effects_mod: Dict[str, float] = field(default_factory=dict)  # 效果参数变化


@dataclass
class SectionPlan:
    """段落编排计划"""
    kind: SectionKind
    bars: int
    energy: EnergyLevel
    tracks: List[str]
    lead_instrument: str
    drum_pattern: str
    bass_pattern: str
    chord_density: float       # 0.0 - 1.0
    melody_activity: float     # 0.0 - 1.0
    transition: bool = False


# ═══════════════════════════════════════════════════════════════════════
# 情绪→编排映射 (Pro1 10.py 精华)
# ═══════════════════════════════════════════════════════════════════════

MOOD_ARRANGEMENT_MAP: Dict[str, List[SectionPlan]] = {
    "happy": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.MEDIUM,
                    tracks=["piano", "drums"], lead_instrument="piano",
                    drum_pattern="simple", bass_pattern="root",
                    chord_density=0.5, melody_activity=0.3),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM_HIGH,
                    tracks=["piano", "bass", "drums"],
                    lead_instrument="piano",
                    drum_pattern="pop", bass_pattern="walking",
                    chord_density=0.7, melody_activity=0.7),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["piano", "chords", "bass", "drums"],
                    lead_instrument="piano",
                    drum_pattern="full", bass_pattern="groove",
                    chord_density=1.0, melody_activity=1.0),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM_HIGH,
                    tracks=["piano", "bass", "drums"],
                    lead_instrument="piano",
                    drum_pattern="pop", bass_pattern="walking",
                    chord_density=0.6, melody_activity=0.6),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["piano", "chords", "bass", "drums"],
                    lead_instrument="piano",
                    drum_pattern="full", bass_pattern="groove",
                    chord_density=1.0, melody_activity=1.0),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.MEDIUM,
                    tracks=["piano", "drums"], lead_instrument="piano",
                    drum_pattern="simple", bass_pattern="root",
                    chord_density=0.4, melody_activity=0.2),
    ],
    "sad": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["piano"], lead_instrument="piano",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.3, melody_activity=0.2),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["piano", "strings", "bass"],
                    lead_instrument="piano",
                    drum_pattern="none", bass_pattern="root",
                    chord_density=0.5, melody_activity=0.4),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.MEDIUM,
                    tracks=["piano", "strings", "bass", "percussion"],
                    lead_instrument="piano",
                    drum_pattern="soft", bass_pattern="walking",
                    chord_density=0.7, melody_activity=0.6),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["piano", "strings"], lead_instrument="piano",
                    drum_pattern="none", bass_pattern="root",
                    chord_density=0.2, melody_activity=0.1),
    ],
    "epic": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["strings", "brass", "percussion"],
                    lead_instrument="strings",
                    drum_pattern="military", bass_pattern="none",
                    chord_density=0.4, melody_activity=0.3),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM,
                    tracks=["strings", "brass", "bass", "percussion"],
                    lead_instrument="brass",
                    drum_pattern="epic", bass_pattern="power",
                    chord_density=0.6, melody_activity=0.5),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["orchestra", "brass", "bass", "drums", "choir"],
                    lead_instrument="orchestra",
                    drum_pattern="full_epic", bass_pattern="power",
                    chord_density=1.0, melody_activity=1.0),
        SectionPlan(SectionKind.BRIDGE,  bars=2, energy=EnergyLevel.MEDIUM,
                    tracks=["strings", "brass", "bass"],
                    lead_instrument="strings",
                    drum_pattern="epic", bass_pattern="walking",
                    chord_density=0.5, melody_activity=0.4, transition=True),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["orchestra", "brass", "bass", "drums", "choir"],
                    lead_instrument="orchestra",
                    drum_pattern="full_epic", bass_pattern="power",
                    chord_density=1.0, melody_activity=1.0),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.HIGH,
                    tracks=["orchestra", "brass", "drums"],
                    lead_instrument="brass",
                    drum_pattern="full_epic", bass_pattern="power",
                    chord_density=0.8, melody_activity=0.6),
    ],
    "calm": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["soft_piano"], lead_instrument="soft_piano",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.2, melody_activity=0.2),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.LOW,
                    tracks=["soft_piano", "pad"],
                    lead_instrument="soft_piano",
                    drum_pattern="none", bass_pattern="root",
                    chord_density=0.4, melody_activity=0.3),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["soft_piano", "pad", "bass", "light_percussion"],
                    lead_instrument="soft_piano",
                    drum_pattern="soft", bass_pattern="root",
                    chord_density=0.5, melody_activity=0.5),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["soft_piano", "pad"],
                    lead_instrument="soft_piano",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.2, melody_activity=0.1),
    ],
    "tense": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["synth_bass", "percussion"],
                    lead_instrument="synth",
                    drum_pattern="industrial", bass_pattern="drone",
                    chord_density=0.3, melody_activity=0.1),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM,
                    tracks=["synth", "synth_bass", "percussion"],
                    lead_instrument="synth",
                    drum_pattern="tense", bass_pattern="ostinato",
                    chord_density=0.5, melody_activity=0.4),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["synth", "dissonant_chords", "synth_bass", "drums"],
                    lead_instrument="synth",
                    drum_pattern="full", bass_pattern="ostinato",
                    chord_density=1.0, melody_activity=0.8),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["synth_bass"], lead_instrument="synth_bass",
                    drum_pattern="none", bass_pattern="drone",
                    chord_density=0.1, melody_activity=0.0),
    ],
}

# New moods from Pro1 that Pro4 didn't have
MOOD_ARRANGEMENT_MAP.update({
    "romantic": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["piano", "strings"], lead_instrument="piano",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.3, melody_activity=0.3),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["piano", "strings", "bass"],
                    lead_instrument="piano",
                    drum_pattern="soft", bass_pattern="root",
                    chord_density=0.6, melody_activity=0.5),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.MEDIUM,
                    tracks=["piano", "strings", "bass", "light_percussion"],
                    lead_instrument="strings",
                    drum_pattern="soft", bass_pattern="walking",
                    chord_density=0.8, melody_activity=0.7),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["piano", "strings"], lead_instrument="piano",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.2, melody_activity=0.1),
    ],
    "energetic": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.MEDIUM_HIGH,
                    tracks=["drums", "bass"], lead_instrument="synth",
                    drum_pattern="full", bass_pattern="groove",
                    chord_density=0.4, melody_activity=0.3),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["synth", "guitar", "bass", "drums"],
                    lead_instrument="synth",
                    drum_pattern="full", bass_pattern="groove",
                    chord_density=1.0, melody_activity=1.0),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.HIGH,
                    tracks=["synth", "guitar", "bass", "drums", "pad"],
                    lead_instrument="synth",
                    drum_pattern="full", bass_pattern="groove",
                    chord_density=1.0, melody_activity=1.0),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.MEDIUM_HIGH,
                    tracks=["synth", "drums"], lead_instrument="synth",
                    drum_pattern="full", bass_pattern="none",
                    chord_density=0.5, melody_activity=0.5),
    ],
    "mysterious": [
        SectionPlan(SectionKind.INTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["pad", "bell"], lead_instrument="pad",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.2, melody_activity=0.1),
        SectionPlan(SectionKind.VERSE,   bars=4, energy=EnergyLevel.MEDIUM_LOW,
                    tracks=["pad", "bell", "bass"],
                    lead_instrument="bell",
                    drum_pattern="ambient", bass_pattern="drone",
                    chord_density=0.4, melody_activity=0.3),
        SectionPlan(SectionKind.CHORUS,  bars=4, energy=EnergyLevel.MEDIUM,
                    tracks=["pad", "bell", "bass", "percussion"],
                    lead_instrument="bell",
                    drum_pattern="ambient", bass_pattern="drone",
                    chord_density=0.6, melody_activity=0.5),
        SectionPlan(SectionKind.OUTRO,   bars=2, energy=EnergyLevel.LOW,
                    tracks=["pad"], lead_instrument="pad",
                    drum_pattern="none", bass_pattern="none",
                    chord_density=0.1, melody_activity=0.0),
    ],
})


# ═══════════════════════════════════════════════════════════════════════
# AutomaticArranger 核心类
# ═══════════════════════════════════════════════════════════════════════

class AutomaticArranger:
    """
    智能自动编排器
    从情绪出发，自动生成完整的段落编排计划和小节级事件

    来源: Pro1 13.py, 增强自 Pro2 节奏型 + Pro4 情绪映射
    """

    MOODS = list(MOOD_ARRANGEMENT_MAP.keys())
    DEFAULT_MOOD = "happy"

    # ── 轨道类型定义 ──────────────────────────────────────────────
    TRACK_TYPES = {
        "melody":    ["piano", "strings", "brass", "synth", "soft_piano",
                      "guitar", "orchestra", "bell", "lead", "flute"],
        "chords":    ["chords", "dissonant_chords", "pad", "choir",
                      "strings", "orchestra"],
        "bass":      ["bass", "synth_bass"],
        "drums":     ["drums", "percussion", "light_percussion"],
        "fx":        ["sweep", "riser", "impacts"],
    }

    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)

    # ── 主 API ────────────────────────────────────────────────────

    def arrange(self, mood: str = "happy", bars: int = 8,
                key: str = "C", bpm: float = 120.0) -> List[BarEvent]:
        """
        为指定情绪生成完整的小节级编排计划

        Returns:
            List[BarEvent]: 每小节的编排事件列表
        """
        if mood not in MOOD_ARRANGEMENT_MAP:
            mood = "happy"

        section_plan = MOOD_ARRANGEMENT_MAP[mood]
        bar_events = self._sections_to_bars(section_plan)
        return bar_events

    def plan_sections(self, mood: str = "happy") -> List[SectionPlan]:
        """返回该情绪的段落计划（不含小节展开）"""
        if mood not in MOOD_ARRANGEMENT_MAP:
            mood = "happy"
        return MOOD_ARRANGEMENT_MAP[mood]

    # ── 内部实现 ──────────────────────────────────────────────────

    def _sections_to_bars(self, sections: List[SectionPlan]) -> List[BarEvent]:
        """将段落计划展开为逐小节事件"""
        events: List[BarEvent] = []
        bar_idx = 0

        for section in sections:
            for bi in range(section.bars):
                event = self._build_bar_event(
                    bar_index=bar_idx,
                    section=section,
                    bar_in_section=bi,
                    total_bars_in_section=section.bars,
                )
                events.append(event)
                bar_idx += 1

        return events

    def _build_bar_event(self, bar_index: int, section: SectionPlan,
                         bar_in_section: int,
                         total_bars_in_section: int) -> BarEvent:
        """构建单个小节的编排事件"""
        # 密度曲线：段落中逐渐增长（除结尾渐弱外）
        if section.kind == SectionKind.OUTRO:
            progress = 1.0 - (bar_in_section / max(1, total_bars_in_section))
        else:
            progress = min(1.0, (bar_in_section + 1) / max(1, total_bars_in_section))

        density_mod = section.chord_density * (0.5 + 0.5 * progress)
        velocity_mod = 0.6 + 0.4 * section.energy.value / 5.0

        # 确定该小节活跃音轨
        active = self._active_tracks_for_section(section, bar_in_section,
                                                  total_bars_in_section)
        muted = []
        solo = None

        # 过渡段独奏
        if section.transition and bar_in_section == 0:
            if section.lead_instrument in active:
                solo = section.lead_instrument

        # Intro: 第一小节只放 lead
        if section.kind == SectionKind.INTRO and bar_in_section == 0:
            active = [t for t in active if t == section.lead_instrument]

        return BarEvent(
            bar_index=bar_index,
            active_tracks=active,
            muted_tracks=muted,
            solo_track=solo,
            velocity_mod=velocity_mod,
            density_mod=density_mod,
            effects_mod={"reverb": 0.2 + 0.15 * progress},
        )

    def _active_tracks_for_section(self, section: SectionPlan,
                                    bar_in_section: int,
                                    total_bars_in_section: int) -> List[str]:
        """计算每个小节的活跃音轨"""
        tracks = list(section.tracks)

        # By type filtering
        if section.kind == SectionKind.VERSE:
            tracks = [t for t in tracks
                      if t not in ("pad", "choir", "dissonant_chords")]
        elif section.kind == SectionKind.BRIDGE:
            # Bridge drops drums
            tracks = [t for t in tracks
                      if t not in ("drums", "percussion")]

        return tracks

    # ── 工具方法 ──────────────────────────────────────────────────

    def list_moods(self) -> List[str]:
        """列出所有支持的情绪"""
        return list(MOOD_ARRANGEMENT_MAP.keys())

    def get_section_names(self, mood: str) -> List[str]:
        """获取指定情绪的段落名称列表"""
        if mood not in MOOD_ARRANGEMENT_MAP:
            return []
        return [s.kind.value for s in MOOD_ARRANGEMENT_MAP[mood]]

    def get_summary(self, mood: str) -> str:
        """获取编排概要"""
        if mood not in MOOD_ARRANGEMENT_MAP:
            return f"Unknown mood: {mood}"

        plan = MOOD_ARRANGEMENT_MAP[mood]
        total_bars = sum(s.bars for s in plan)
        sections = [f"{s.kind.value}({s.bars}bars)" for s in plan]
        return (
            f"Mood: {mood} | Total bars: {total_bars} | "
            f"Sections: {' → '.join(sections)}"
        )

    def to_table(self, mood: str) -> str:
        """格式化为可打印的编排表格"""
        if mood not in MOOD_ARRANGEMENT_MAP:
            return f"Unknown mood: {mood}"

        lines = []
        plan = MOOD_ARRANGEMENT_MAP[mood]
        bar_offset = 0
        for s in plan:
            lines.append(
                f"  Bars {bar_offset+1:>2d}-{bar_offset+s.bars:<2d}  "
                f"{s.kind.value:<10s}  "
                f"Energy: {'●' * s.energy.value}{'○' * (5 - s.energy.value)}  "
                f"Lead: {s.lead_instrument:<12s}  "
                f"Tracks: {', '.join(s.tracks)}"
            )
            bar_offset += s.bars
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 动态编排器 (Pro1 9.py - DynamicOrchestrator 增强版)
# ═══════════════════════════════════════════════════════════════════════

class DynamicOrchestrator:
    """
    动态编配管理器
    管理音轨静音组、声部层级、自动化参数曲线

    来源: Pro1 9.py, 增强自 Pro4 的 mute group 系统
    """

    def __init__(self, num_tracks: int = 16):
        self.num_tracks = num_tracks
        self.mute_groups: Dict[int, List[int]] = {}   # group_id → [track_idx, ...]
        self.solo_state: Optional[int] = None           # 独奏的音轨索引
        self.muted_tracks: set = set()                  # 被静音的音轨索引
        self.track_layers: Dict[int, List[int]] = {}   # layer_id → [track_idx, ...]
        self.automation: Dict[int, List[Tuple[float, float]]] = {}  # track → [(time,value), ...]

    def add_mute_group(self, group_id: int, tracks: List[int]):
        """添加静音组：组内音轨互斥，同一时间只有一个发声"""
        self.mute_groups[group_id] = tracks

    def set_solo(self, track_idx: Optional[int]):
        """设置独奏音轨"""
        self.solo_state = track_idx

    def clear_solo(self):
        """取消独奏"""
        self.solo_state = None

    def mute(self, track_idx: int):
        """静音指定音轨"""
        self.muted_tracks.add(track_idx)

    def unmute(self, track_idx: int):
        """取消静音"""
        self.muted_tracks.discard(track_idx)

    def get_active_tracks(self) -> List[int]:
        """获取当前活跃的音轨列表

        优先级: solo > mute_groups > muted
        """
        # Solo 优先
        if self.solo_state is not None:
            return [self.solo_state]

        active = []
        for i in range(self.num_tracks):
            if i in self.muted_tracks:
                continue

            # 检查静音组：同一组内只允许第一个在 active 中
            conflict = False
            for g_id, members in self.mute_groups.items():
                if i in members:
                    # 组内已有更小索引的活跃音轨
                    for m in members:
                        if m < i and m not in self.muted_tracks:
                            conflict = True
                            break
                    break
            if not conflict:
                active.append(i)

        return active

    def add_automation(self, track_idx: int, points: List[Tuple[float, float]]):
        """为音轨添加自动化参数"""
        self.automation[track_idx] = sorted(points, key=lambda x: x[0])

    def get_automation_value(self, track_idx: int, time: float) -> Optional[float]:
        """获取指定时间点的自动化值（线性插值）"""
        if track_idx not in self.automation:
            return None
        points = self.automation[track_idx]
        if len(points) == 0:
            return None
        if time <= points[0][0]:
            return points[0][1]
        if time >= points[-1][0]:
            return points[-1][1]
        for i in range(len(points) - 1):
            t1, v1 = points[i]
            t2, v2 = points[i + 1]
            if t1 <= time <= t2:
                ratio = (time - t1) / (t2 - t1) if t2 != t1 else 0.0
                return v1 + ratio * (v2 - v1)
        return None

    def add_layer(self, layer_id: int, tracks: List[int]):
        """添加声部层级"""
        self.track_layers[layer_id] = tracks

    def get_layer(self, layer_id: int) -> List[int]:
        """获取层级中的音轨"""
        return self.track_layers.get(layer_id, [])


# ── 快速编排辅助 ─────────────────────────────────────────────────────

def quick_arrange(mood: str = "happy", bpm: float = 120.0,
                  key: str = "C") -> Tuple[List[BarEvent], str]:
    """
    快速编排：一行代码生成完整的编排计划

    Returns:
        (bar_events, summary_string)
    """
    arranger = AutomaticArranger()
    plan = arranger.plan_sections(mood)
    total_bars = sum(s.bars for s in plan)
    events = arranger.arrange(mood=mood, bars=total_bars, key=key, bpm=bpm)
    summary = arranger.get_summary(mood)
    return events, summary


def print_arrangement_preview(mood: str):
    """打印指定情绪的编排预览（Pro1 风格的可视化表格）"""
    arranger = AutomaticArranger()
    print(f"\n{'='*60}")
    print(f"  Arrangement: {mood.upper()}")
    print(f"{'='*60}")
    print(arranger.to_table(mood))
    print(f"{'='*60}\n")
    return arranger.arrange(mood=mood)


if __name__ == "__main__":
    # 演示：打印所有情绪的编排计划
    for m in AutomaticArranger.MOODS:
        print_arrangement_preview(m)
