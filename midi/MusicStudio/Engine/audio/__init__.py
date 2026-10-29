#!/usr/bin/env python3
"""音频模块 - 合成器 + 软件合成器 + 三级回退"""
from .synthesizer import (
    find_soundfont, check_fluidsynth, load_audio,
    midi_to_wav_fluidsynth, midi_json_to_wav_software,
    batch_synthesize, synthesize_midi,
)
from .soft_synth import (
    generate_note, generate_drum,
    midi_note_array_to_audio, synthesize_from_midi_json,
    INSTRUMENT_PRESETS, DRUM_MAP,
)
