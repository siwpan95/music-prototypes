#!/usr/bin/env python3
"""算法作曲模块 - Pro2 风格生成器整合"""
from .param_gen import (
    MelodyGenerator, ChordGenerator, BassGenerator, DrumGenerator,
    compose, batch_generate, create_instrument_config, generate_melody,
    ComposeResult,
    list_rhythm_patterns, list_drum_patterns,
    RHYTHM_PATTERNS, DRUM_PATTERNS, DRUM_NOTE_MAP,
)
