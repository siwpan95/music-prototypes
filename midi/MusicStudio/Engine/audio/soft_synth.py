#!/usr/bin/env python3
"""
MusicStudioPro - SoftSynth (软件合成器回退)
当 FluidSynth / SoundFont 不可用时，使用纯 numpy 生成基础波形音频
"""
from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional, Tuple


# ── 简易音色库（模拟 GM 乐器）─────────────────────────────────────────
# 基础音色生成器：谐波组合（基频 + 泛音比例）
# format: (name, harmonics_weights)
#   harmonics_weights: [基频振幅, 2次谐波, 3次, 4次, ...]
INSTRUMENT_PRESETS: Dict[int, Tuple[str, List[float]]] = {
    0:  ("Piano",       [1.0, 0.5, 0.3, 0.15, 0.05, 0.02]),
    1:  ("BrightPiano", [1.0, 0.7, 0.4, 0.2,  0.1,  0.05]),
    4:  ("E.Piano",     [1.0, 0.3, 0.1, 0.05]),
    11: ("Vibraphone",  [1.0, 0.1, 0.05, 0.02]),
    24: ("Guitar",      [1.0, 0.6, 0.4, 0.2, 0.1, 0.05, 0.02]),
    25: ("Ac.Guitar",   [1.0, 0.5, 0.3, 0.15, 0.07, 0.03]),
    32: ("Ac.Bass",     [1.0, 0.8, 0.2, 0.05]),
    33: ("FingerBass",  [1.0, 0.6, 0.1, 0.03]),
    40: ("Violin",      [1.0, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05]),
    48: ("Strings",     [1.0, 0.7, 0.5, 0.3, 0.15, 0.08, 0.04]),
    56: ("Trumpet",     [1.0, 0.7, 0.5, 0.3, 0.15, 0.07]),
    60: ("Fr.Horn",     [1.0, 0.6, 0.3, 0.15, 0.07]),
    68: ("Oboe",        [1.0, 0.3, 0.2, 0.1, 0.05]),
    73: ("Flute",       [1.0, 0.4, 0.1, 0.03]),
    80: ("SquareLead",  [1.0, 0.0, 0.33, 0.0, 0.2, 0.0, 0.14]),
    81: ("SawLead",     [1.0, 0.5, 0.33, 0.25, 0.2, 0.17, 0.14, 0.12]),
}


# MIDI 音符到频率
def midi_to_freq(note: int, a4: float = 440.0) -> float:
    return a4 * (2.0 ** ((note - 69) / 12.0))


def generate_note(
    note: int,
    duration: float,
    velocity: int = 64,
    program: int = 0,
    sample_rate: int = 44100,
) -> np.ndarray:
    """
    用加法合成（谐波叠加）生成单个音符的音频
    
    Args:
        note: MIDI 音符编号 (0-127)
        duration: 时长（秒）
        velocity: 力度 (0-127)
        program: GM 乐器编号
        sample_rate: 采样率
    Returns:
        np.ndarray: 单声道音频 [samples]
    """
    freq = midi_to_freq(note)
    amp = (velocity / 127.0) * 0.3  # 基础振幅
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    preset = INSTRUMENT_PRESETS.get(program, INSTRUMENT_PRESETS[0])
    name, harmonics = preset
    
    audio = np.zeros_like(t)
    for i, weight in enumerate(harmonics):
        if weight > 0:
            harmonic_freq = freq * (i + 1)
            # 泛音衰减 (高频泛音更快衰减)
            decay = 1.0 / (1.0 + 0.1 * i)
            audio += weight * decay * np.sin(2.0 * np.pi * harmonic_freq * t)
    
    # 归一化
    audio /= np.max(np.abs(audio)) + 1e-8
    
    # ADSR 包络
    n = len(audio)
    attack_samples = int(0.02 * sample_rate)      # 20ms attack
    decay_samples = int(0.1 * sample_rate)        # 100ms decay
    release_samples = int(0.1 * sample_rate)      # 100ms release
    
    env = np.ones(n)
    if attack_samples > 0:
        env[:attack_samples] = np.linspace(0, 1, min(attack_samples, n))
    if decay_samples > 0 and attack_samples < n:
        end = min(attack_samples + decay_samples, n)
        env[attack_samples:end] = np.linspace(1, 0.7, end - attack_samples)
    if release_samples > 0 and n > release_samples:
        env[-release_samples:] = np.linspace(0.7, 0, release_samples)
    
    audio *= env * amp
    
    return audio


def generate_drum(
    drum_type: str = "kick",
    velocity: int = 100,
    sample_rate: int = 44100,
) -> np.ndarray:
    """
    合成鼓声音
    
    Args:
        drum_type: "kick", "snare", "hihat", "tom", "clap", "crash"
        velocity: 力度
    """
    duration_map = {
        "kick": 0.3, "snare": 0.2, "hihat": 0.05,
        "tom": 0.25, "clap": 0.15, "crash": 0.5,
    }
    dur = duration_map.get(drum_type, 0.1)
    amp = (velocity / 127.0) * 0.5
    t = np.linspace(0, dur, int(sample_rate * dur), endpoint=False)
    
    if drum_type == "kick":
        # 频率扫描: 150Hz -> 50Hz
        freq_env = 150 * np.exp(-t * 20) + 50
        audio = np.sin(2.0 * np.pi * freq_env * t)
        env = np.exp(-t * 8)
        
    elif drum_type == "snare":
        # 基音 + 噪音
        body = np.sin(2.0 * np.pi * 180 * t) * np.exp(-t * 5)
        noise = np.random.randn(len(t)) * 0.3
        # 高通噪声
        noise = np.convolve(noise, [1, -0.95], mode='same')
        audio = (body * 0.6 + noise * 0.4) * np.exp(-t * 10)
        
    elif drum_type == "hihat":
        noise = np.random.randn(len(t))
        # 带通滤波模拟
        audio = np.convolve(noise, [0.2, 0.5, 0.2], mode='same')
        env = np.exp(-t * 40)
        
    elif drum_type == "tom":
        freq_env = 200 * np.exp(-t * 8) + 80
        audio = np.sin(2.0 * np.pi * freq_env * t) * 0.7
        env = np.exp(-t * 6)
        
    elif drum_type == "clap":
        noise = np.random.randn(len(t))
        audio = np.convolve(noise, [1, -0.9, -0.8], mode='same')
        env = np.exp(-t * 15)
        # 快速包络
        env[:int(sample_rate * 0.01)] = 1.0
        
    elif drum_type == "crash":
        noise = np.random.randn(len(t))
        audio = np.convolve(noise, [1, 0.5, 0.3, 0.2, 0.1, 0.05], mode='same')
        env = np.exp(-t * 3)
        
    else:
        audio = np.sin(2.0 * np.pi * 200 * t)
        env = np.exp(-t * 10)
    
    audio *= env * amp
    audio /= np.max(np.abs(audio)) + 1e-8
    
    return audio


# GM 打击乐映射 (MIDI Note -> Drum Type)
DRUM_MAP: Dict[int, str] = {
    35: "kick",   36: "kick",
    38: "snare",  40: "snare",
    42: "hihat",  44: "hihat",  46: "hihat",
    45: "tom",    47: "tom",    48: "tom",    50: "tom",
    39: "clap",
    49: "crash",  57: "crash",
    51: "crash",  52: "crash",  53: "crash",  55: "crash",  59: "crash",
}


def midi_note_array_to_audio(
    notes: np.ndarray,
    sample_rate: int = 44100,
    program: int = 0,
    bpm: float = 120.0,
) -> Optional[np.ndarray]:
    """
    将 MIDI 音符数组转换为音频（纯软件合成）
    
    Args:
        notes: numpy array from pretty_midi instrument.notes,
               每行 [pitch, start_time, duration, velocity]
        sample_rate: 采样率
        program: GM 乐器编号
        bpm: 拍速
    Returns:
        单声道音频 np.ndarray
    """
    if len(notes) == 0:
        return None
    
    # 计算总时长
    total_duration = (notes[:, 1] + notes[:, 2]).max() + 0.5  # 加 0.5s 余量
    total_samples = int(sample_rate * total_duration)
    audio = np.zeros(total_samples)
    
    is_drum = (program >= 112 or program == 0)  # 简化判断
    # 更精确的鼓组判断：channel 9 或 program 0 with special notes
    
    for pitch, start, dur, vel in notes:
        # 检查是否为鼓音符
        if is_drum and int(pitch) in DRUM_MAP:
            drum_audio = generate_drum(DRUM_MAP[int(pitch)], int(vel), sample_rate)
        else:
            drum_audio = generate_note(int(pitch), max(dur, 0.05), int(vel), program, sample_rate)
        
        start_sample = int(start * sample_rate)
        end_sample = min(start_sample + len(drum_audio), total_samples)
        audio[start_sample:end_sample] += drum_audio[:end_sample - start_sample]
    
    # 总体归一化
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio /= max_val * 1.1
    
    return audio


def synthesize_from_midi_json(
    midi_data: dict,
    sample_rate: int = 44100,
) -> Tuple[List[np.ndarray], List[str]]:
    """
    从 MIDI JSON 数据合成音频（纯软件回退方案）
    
    Args:
        midi_data: MIDI JSON 数据，包含 tracks
        sample_rate: 采样率
    Returns:
        (audio_list, track_names) 
    """
    audio_list = []
    names = []
    
    tracks = midi_data.get("tracks", [])
    bpm = midi_data.get("bpm", 120.0)
    
    for track in tracks:
        name = track.get("name", "Unknown")
        program = track.get("program", 0)
        notes = track.get("notes", [])
        
        if not notes:
            continue
        
        # 计算总时长
        total_duration = 0.0
        note_arrays = []
        for n in notes:
            pitch = n.get("pitch", 60)
            start = n.get("start_time", 0.0)
            duration = n.get("duration", 0.5)
            velocity = n.get("velocity", 80)
            note_arrays.append([pitch, start, duration, velocity])
            total_duration = max(total_duration, start + duration)
        
        total_duration += 0.5
        total_samples = int(sample_rate * total_duration)
        audio = np.zeros(total_samples)
        
        for pitch, start, dur, vel in note_arrays:
            note_audio = generate_note(int(pitch), max(dur, 0.05), int(vel), program, sample_rate)
            start_sample = int(start * sample_rate)
            end_sample = min(start_sample + len(note_audio), total_samples)
            if end_sample > start_sample:
                audio[start_sample:end_sample] += note_audio[:end_sample - start_sample]
        
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio /= max_val * 1.1
        
        if np.any(audio):
            audio_list.append(audio)
            names.append(name)
    
    return audio_list, names
