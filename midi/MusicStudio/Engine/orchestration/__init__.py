#!/usr/bin/env python3
"""编排模块 - Pro1 智能配器引擎整合"""
from .arranger import (
    AutomaticArranger, DynamicOrchestrator,
    BarEvent, SectionPlan, SectionKind, EnergyLevel,
    quick_arrange, print_arrangement_preview, MOOD_ARRANGEMENT_MAP,
)
from .orchestrator import (
    IntelligentOrchestrator, OrchestrationConfig,
    create_orchestrator,
    SCALE_MAP, CHORD_MAP, CHORD_PROGRESSIONS,
    MOOD_INSTRUMENT_TEMPLATES,
)
