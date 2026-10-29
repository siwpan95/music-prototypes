#!/usr/bin/env python3
"""
增强配器引擎 - 整合四项目精华
- Pro1: 情绪驱动配器、完整乐器→情绪映射
- Pro2: 乐器参数预设
- Pro4: 已验证的核心配器流程
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import random
import numpy as np

from .arranger import (
    AutomaticArranger, DynamicOrchestrator,
    BarEvent, SectionPlan, SectionKind, EnergyLevel,
    print_arrangement_preview, MOOD_ARRANGEMENT_MAP,
)


# ═══════════════════════════════════════════════════════════════════════
# 乐器模板系统 (Pro1 10.py 精华 - 完整情绪→音色映射)
# ═══════════════════════════════════════════════════════════════════════

MOOD_INSTRUMENT_TEMPLATES: Dict[str, List[Dict]] = {
    "happy": [
        {"name": "Piano",       "program":  0, "type": "melody", "octave": 1, "pattern": "scale",
         "voicing": "triad",    "style": "pop"},
        {"name": "Chords",      "program":  0, "type": "chords", "voicing": "block",
         "style": "major"},
        {"name": "Bass",        "program": 33, "type": "bass", "octave": -2, "pattern": "walking",
         "style": "pop"},
        {"name": "Drums",       "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "pop",      "style": "pop"},
    ],
    "sad": [
        {"name": "Piano",       "program":  0, "type": "melody", "octave": 0, "pattern": "slow",
         "voicing": "minor",    "style": "minor"},
        {"name": "Strings",     "program": 49, "type": "chords", "voicing": "sustained",
         "style": "minor"},
        {"name": "Bass",        "program": 34, "type": "bass", "octave": -2, "pattern": "simple",
         "style": "minor"},
        {"name": "Percussion",  "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "soft",     "style": "minor"},
    ],
    "epic": [
        {"name": "Orchestra",   "program": 49, "type": "melody", "octave": 0, "pattern": "heroic",
         "voicing": "orchestral"},
        {"name": "Brass",       "program": 62, "type": "chords", "voicing": "block",
         "style": "epic"},
        {"name": "Bass",        "program": 34, "type": "bass", "octave": -2, "pattern": "power",
         "style": "epic"},
        {"name": "Drums",       "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "epic",     "style": "epic"},
    ],
    "calm": [
        {"name": "SoftPiano",   "program":  0, "type": "melody", "octave": 0, "pattern": "ambient",
         "voicing": "open",     "style": "ambient"},
        {"name": "Pad",         "program": 91, "type": "chords", "voicing": "sustained",
         "style": "ambient"},
        {"name": "Bass",        "program": 36, "type": "bass", "octave": -2, "pattern": "simple",
         "style": "ambient"},
        {"name": "LightPerc",   "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "ambient",  "style": "ambient"},
    ],
    "tense": [
        {"name": "Synth",       "program": 81, "type": "melody", "octave": 0, "pattern": "dissonant",
         "voicing": "tritone",  "style": "tense"},
        {"name": "Dissonant",   "program": 83, "type": "chords", "voicing": "block",
         "style": "tense"},
        {"name": "Bass",        "program": 39, "type": "bass", "octave": -2, "pattern": "ostinato",
         "style": "tense"},
        {"name": "Drums",       "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "industrial","style": "tense"},
    ],
    "romantic": [
        {"name": "Piano",       "program":  0, "type": "melody", "octave": 0, "pattern": "legato",
         "voicing": "rich"},
        {"name": "Strings",     "program": 49, "type": "chords", "voicing": "sustained",
         "style": "romantic"},
        {"name": "Bass",        "program": 33, "type": "bass", "octave": -2, "pattern": "walking",
         "style": "romantic"},
        {"name": "LightPerc",   "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "soft",     "style": "romantic"},
    ],
    "energetic": [
        {"name": "Synth",       "program": 81, "type": "melody", "octave": 1, "pattern": "fast",
         "voicing": "power"},
        {"name": "Guitar",      "program": 30, "type": "chords", "voicing": "power",
         "style": "rock"},
        {"name": "Bass",        "program": 34, "type": "bass", "octave": -2, "pattern": "groove",
         "style": "rock"},
        {"name": "Drums",       "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "full",     "style": "rock"},
    ],
    "mysterious": [
        {"name": "Pad",         "program": 91, "type": "melody", "octave": 0, "pattern": "ambient",
         "voicing": "open"},
        {"name": "Bell",        "program": 15, "type": "chords", "voicing": "sparse",
         "style": "mysterious"},
        {"name": "Bass",        "program": 39, "type": "bass", "octave": -2, "pattern": "drone",
         "style": "mysterious"},
        {"name": "Percussion",  "program":  0, "type": "drums",  "is_drum": True,
         "pattern": "ambient",  "style": "mysterious"},
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# 调式与和声规则 (Pro1 11.py + Pro2 1.py 合并)
# ═══════════════════════════════════════════════════════════════════════

SCALE_MAP = {
    "C":  [60, 62, 64, 65, 67, 69, 71, 72],
    "G":  [55, 57, 59, 60, 62, 64, 66, 67],
    "D":  [50, 52, 54, 55, 57, 59, 61, 62],
    "A":  [57, 59, 61, 62, 64, 66, 68, 69],
    "F":  [53, 55, 57, 58, 60, 62, 64, 65],
    "Bb": [46, 48, 50, 51, 53, 55, 57, 58],
    "Eb": [51, 53, 55, 56, 58, 60, 62, 63],
}

CHORD_MAP = {
    "C":  {"I": [60,64,67], "IV": [65,69,72], "V": [67,71,74], "vi": [69,72,76]},
    "G":  {"I": [55,59,62], "IV": [60,64,67], "V": [62,66,69], "vi": [64,67,71]},
    "D":  {"I": [50,54,57], "IV": [55,59,62], "V": [57,61,64], "vi": [59,62,66]},
    "A":  {"I": [57,61,64], "IV": [62,66,69], "V": [64,68,71], "vi": [66,69,73]},
    "F":  {"I": [53,57,60], "IV": [58,62,65], "V": [60,64,67], "vi": [62,65,69]},
}

# 常见和弦进行 (Pro2 1.py + Pro1 5.py)
CHORD_PROGRESSIONS = {
    "pop":       ["I", "V", "vi", "IV"],
    "classic":   ["I", "IV", "V", "IV"],
    "minor":     ["vi", "IV", "I", "V"],
    "jazz":      ["ii", "V", "I", "vi"],
    "epic":      ["I", "vi", "IV", "V"],
    "ambient":   ["I", "V", "vi", "iii"],
    "rock":      ["I", "IV", "V", "V"],
    "tense":     ["vi", "V", "vi", "V"],
    "cadence":   ["I", "IV", "V", "I"],
}


# ═══════════════════════════════════════════════════════════════════════
# 智能配器引擎
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class OrchestrationConfig:
    """配器配置"""
    mood: str = "happy"
    key: str = "C"
    bpm: float = 120.0
    complexity: int = 3
    bars: int = 8
    sample_rate: int = 44100
    soundfont_path: Optional[str] = None


class IntelligentOrchestrator:
    """
    智能配器引擎
    融合 Pro1 的情绪驱动配器 + Pro2 的乐器参数 + Pro4 的运行管道
    """

    MOOD_MAP = MOOD_INSTRUMENT_TEMPLATES
    ALL_MOODS = list(MOOD_INSTRUMENT_TEMPLATES.keys())

    def __init__(self, config: Optional[OrchestrationConfig] = None):
        self.config = config or OrchestrationConfig()
        self.arranger = AutomaticArranger()
        self.dynamic = DynamicOrchestrator(num_tracks=16)
        self._bar_events: List[BarEvent] = []
        self._section_plan: List[SectionPlan] = []

    # ── 主配器流程 ─────────────────────────────────────────────────

    def orchestrate(self, mood: Optional[str] = None,
                    key: Optional[str] = None,
                    bpm: Optional[float] = None,
                    complexity: Optional[int] = None,
                    bars: Optional[int] = None) -> Tuple[List[Dict], List[BarEvent]]:
        """
        完整配器流程：情绪→乐器→编排→小节事件

        Returns:
            (instruments_config, bar_events)
        """
        if mood is not None:
            self.config.mood = mood
        if key is not None:
            self.config.key = key
        if bpm is not None:
            self.config.bpm = bpm
        if complexity is not None:
            self.config.complexity = complexity
        if bars is not None:
            self.config.bars = bars

        mood = self.config.mood

        # 1. 获取乐器模板
        templates = MOOD_INSTRUMENT_TEMPLATES.get(mood, MOOD_INSTRUMENT_TEMPLATES["happy"])

        # 2. 根据复杂度调整乐器数量和参数
        instruments = self._adjust_complexity(templates, self.config.complexity)

        # 3. 生成段落编排计划
        self._section_plan = self.arranger.plan_sections(mood)

        # 4. 生成小节级事件
        self._bar_events = self.arranger.arrange(
            mood=mood,
            bars=sum(s.bars for s in self._section_plan),
            key=self.config.key,
            bpm=self.config.bpm,
        )

        # 5. 应用编排结果到动态管理器
        self._apply_to_dynamic(self._bar_events)

        return instruments, self._bar_events

    def orchestrate_advanced(self, mood: str, key: str = "C",
                              bpm: float = 120.0, complexity: int = 3,
                              custom_sections: Optional[List[SectionPlan]] = None
                              ) -> Tuple[List[Dict], List[BarEvent], List[SectionPlan]]:
        """
        高级配器：支持自定义段落计划

        Returns:
            (instruments, bar_events, section_plan)
        """
        templates = MOOD_INSTRUMENT_TEMPLATES.get(mood, MOOD_INSTRUMENT_TEMPLATES["happy"])
        instruments = self._adjust_complexity(templates, complexity)

        if custom_sections:
            self._section_plan = custom_sections
        else:
            self._section_plan = self.arranger.plan_sections(mood)

        self._bar_events = self.arranger.arrange(
            mood=mood,
            bars=sum(s.bars for s in self._section_plan),
            key=key, bpm=bpm,
        )

        self._apply_to_dynamic(self._bar_events)
        return instruments, self._bar_events, self._section_plan

    # ── 复杂度调整 ─────────────────────────────────────────────────

    def _adjust_complexity(self, templates: List[Dict],
                           complexity: int) -> List[Dict]:
        """根据复杂度级别调整乐器配置

        complexity 1: 只保留旋律 + 鼓（最简）
        complexity 2: 旋律 + 和弦 + 鼓
        complexity 3: 完整四件（默认）
        complexity 4: 四件 + 增强效果标记
        complexity 5: 全部 + 副旋律
        """
        if complexity <= 1:
            keep_types = {"melody", "drums"}
        elif complexity == 2:
            keep_types = {"melody", "chords", "drums"}
        elif complexity == 3:
            keep_types = {"melody", "chords", "bass", "drums"}
        elif complexity == 4:
            keep_types = {"melody", "chords", "bass", "drums", "fx"}
        else:
            keep_types = {"melody", "chords", "bass", "drums", "fx", "pad"}

        result = []
        for inst in templates:
            inst_type = inst.get("type", "melody")
            if inst_type in keep_types or inst_type == "melody":
                inst_copy = dict(inst)
                # 复杂度越高，音域越宽
                if complexity >= 4:
                    inst_copy.setdefault("velocity_range", (60, 127))
                else:
                    inst_copy.setdefault("velocity_range", (70, 110))
                result.append(inst_copy)

        return result

    # ── 应用到动态管理器 ────────────────────────────────────────────

    def _apply_to_dynamic(self, events: List[BarEvent]):
        """将编排事件映射到动态编排管理器"""
        # 映射：乐器名 → 内部索引
        track_index = {}
        for i, inst in enumerate(
            MOOD_INSTRUMENT_TEMPLATES.get(self.config.mood, [])
        ):
            track_index[inst["name"].lower()] = i

        # 按静音组设置（同一类乐器的不同配置互斥）
        groups = {"melody": [], "chords": [], "bass": [], "drums": []}
        for i, inst in enumerate(
            MOOD_INSTRUMENT_TEMPLATES.get(self.config.mood, [])
        ):
            tp = inst.get("type", "melody")
            groups.setdefault(tp, []).append(i)

        for gid, (tp, ids) in enumerate(groups.items()):
            if len(ids) > 1:
                self.dynamic.add_mute_group(gid, ids)

    # ── 和弦进行生成 ───────────────────────────────────────────────

    def get_chord_progression(self, style: str = "pop",
                              key: Optional[str] = None) -> List[List[int]]:
        """生成和弦进行"""
        key = key or self.config.key
        progression = CHORD_PROGRESSIONS.get(style, CHORD_PROGRESSIONS["pop"])
        chord_map = CHORD_MAP.get(key, CHORD_MAP["C"])
        return [chord_map.get(c, [60, 64, 67]) for c in progression]

    def get_scale(self, key: Optional[str] = None) -> List[int]:
        """获取音阶"""
        key = key or self.config.key
        return SCALE_MAP.get(key, SCALE_MAP["C"])

    # ── 信息查询 ────────────────────────────────────────────────────

    def list_moods(self) -> List[str]:
        """列出所有支持的情绪"""
        return list(MOOD_INSTRUMENT_TEMPLATES.keys())

    def get_arrangement_preview(self) -> str:
        """获取当前编排计划的文本预览"""
        return self.arranger.to_table(self.config.mood)

    def get_arrangement_summary(self) -> str:
        """获取编排摘要"""
        return self.arranger.get_summary(self.config.mood)

    def print_preview(self):
        """打印编排预览到控制台"""
        print_arrangement_preview(self.config.mood)

    # ── 属性 ────────────────────────────────────────────────────────

    @property
    def bar_events(self) -> List[BarEvent]:
        return self._bar_events

    @property
    def section_plan(self) -> List[SectionPlan]:
        return self._section_plan


# ═══════════════════════════════════════════════════════════════════════
# 便捷函数 (保持向下兼容)
# ═══════════════════════════════════════════════════════════════════════

def create_orchestrator(mood: str = "happy", key: str = "C",
                        bpm: float = 120.0, complexity: int = 3,
                        bars: int = 8) -> IntelligentOrchestrator:
    """创建配器器实例"""
    config = OrchestrationConfig(mood=mood, key=key, bpm=bpm,
                                  complexity=complexity, bars=bars)
    return IntelligentOrchestrator(config)


if __name__ == "__main__":
    print("=" * 60)
    print("  MusicStudioPro - Intelligent Orchestrator")
    print("  (Pro1 + Pro2 + Pro4 合并)")
    print("=" * 60)

    orch = IntelligentOrchestrator()
    for mood in orch.ALL_MOODS:
        instruments, events = orch.orchestrate(mood=mood)
        n_bars = len(events)
        n_sections = len(orch.section_plan)
        print(f"\n  {mood.upper()}")
        print(f"  {'─' * 30}")
        print(f"  Instruments: {[i['name'] for i in instruments]}")
        print(f"  Sections: {n_sections}, Total bars: {n_bars}")
        for i, s in enumerate(orch.section_plan):
            print(f"    [{i+1}] {s.kind.value}: {s.bars} bars, "
                  f"energy={s.energy.name}, lead={s.lead_instrument}")
