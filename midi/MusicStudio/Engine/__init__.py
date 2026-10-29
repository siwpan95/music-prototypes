#!/usr/bin/env python3
"""
MusicStudio - 统一引擎
四项目精华整合：
- 智能配器 (Pro1)
- 算法作曲 (Pro2)
- 多级合成 (Pro4)
- 效果链处理 (Pro2+Pro4)
"""
from Engine.orchestration import (
    IntelligentOrchestrator, AutomaticArranger, DynamicOrchestrator,
    BarEvent, SectionPlan, SectionKind, EnergyLevel,
    create_orchestrator, quick_arrange,
    CHORD_PROGRESSIONS, SCALE_MAP,
)
from Engine.composition import (
    MelodyGenerator, ChordGenerator, BassGenerator, DrumGenerator,
    compose, batch_generate, create_instrument_config, generate_melody,
)
