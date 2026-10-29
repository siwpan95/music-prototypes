#!/usr/bin/env python3
"""
MusicStudioPro - Audio Effects Chain
整合 pro3 audio_effects.py + pro2 effects chain
提供：Reverb / EQ / Compressor / Delay / Chorus
"""
from __future__ import annotations
import numpy as np
from typing import Optional
from scipy import signal as sig


def apply_reverb(audio: np.ndarray, amount: float = 0.4,
                 sample_rate: int = 44100) -> np.ndarray:
    """Schroeder 混响（4 并联梳状滤波器 + 2 全通滤波器）"""
    if amount <= 0:
        return audio
    comb_delays = [int(0.0297 * sample_rate),
                   int(0.0371 * sample_rate),
                   int(0.0411 * sample_rate),
                   int(0.0437 * sample_rate)]
    fb = 0.84 * amount
    wet = np.zeros_like(audio)
    for d in comb_delays:
        buf = np.zeros((d, audio.shape[1]) if audio.ndim == 2 else d)
        for i in range(len(audio)):
            idx = i % d
            if audio.ndim == 2:
                out = buf[idx].copy()
                buf[idx] = audio[i] + fb * buf[idx]
            else:
                out = buf[idx]
                buf[idx] = audio[i] + fb * buf[idx]
            wet[i] += out * 0.25
    return (1 - amount) * audio + amount * np.clip(wet, -1, 1)


def apply_eq(audio: np.ndarray, low_gain: float = 1.0,
             mid_gain: float = 1.0, high_gain: float = 1.0,
             sample_rate: int = 44100) -> np.ndarray:
    """三频段均衡器（使用 Butterworth 滤波器）"""
    def butter_filter(data, cutoff, btype, order=4):
        nyq = sample_rate / 2
        normalized = cutoff / nyq
        b, a = sig.butter(order, normalized, btype=btype)
        if data.ndim == 2:
            return np.column_stack([sig.lfilter(b, a, data[:, c]) for c in range(data.shape[1])])
        return sig.lfilter(b, a, data)

    low = butter_filter(audio, 300, "low") * low_gain
    mid_lo = butter_filter(audio, 300, "high")
    mid_hi = butter_filter(mid_lo, 3000, "low")
    mid = mid_hi * mid_gain
    high = butter_filter(audio, 3000, "high") * high_gain
    return np.clip(low + mid + high, -1, 1)


def apply_compressor(audio: np.ndarray, threshold: float = 0.5,
                     ratio: float = 4.0, attack_ms: float = 10.0,
                     release_ms: float = 100.0,
                     sample_rate: int = 44100) -> np.ndarray:
    """动态压缩器"""
    attack  = 1 - np.exp(-1 / (attack_ms  * 0.001 * sample_rate))
    release = 1 - np.exp(-1 / (release_ms * 0.001 * sample_rate))
    envelope = np.zeros(len(audio))
    level = 0.0
    for i, frame in enumerate(np.abs(audio[:, 0] if audio.ndim == 2 else audio)):
        if frame > level:
            level += attack * (frame - level)
        else:
            level += release * (frame - level)
        envelope[i] = level
    gain = np.ones_like(envelope)
    over = envelope > threshold
    gain[over] = threshold + (envelope[over] - threshold) / ratio
    gain[over] /= envelope[over]
    if audio.ndim == 2:
        return np.clip(audio * gain[:, np.newaxis], -1, 1)
    return np.clip(audio * gain, -1, 1)


def apply_delay(audio: np.ndarray, time_sec: float = 0.3,
                feedback: float = 0.4, mix: float = 0.3,
                sample_rate: int = 44100) -> np.ndarray:
    """单声道延迟效果"""
    delay_n = int(time_sec * sample_rate)
    buf = np.zeros((delay_n, audio.shape[1]) if audio.ndim == 2 else delay_n,
                   dtype=np.float32)
    out = audio.copy().astype(np.float32)
    for i in range(len(audio)):
        idx = i % delay_n
        d = buf[idx].copy()
        buf[idx] = audio[i] + feedback * d
        out[i] = audio[i] + mix * d
    return np.clip(out, -1, 1)


def apply_chorus(audio: np.ndarray, rate: float = 1.5,
                 depth: float = 0.004, mix: float = 0.5,
                 sample_rate: int = 44100) -> np.ndarray:
    """合唱效果（LFO 调制延迟）"""
    n = len(audio)
    t = np.arange(n) / sample_rate
    lfo = depth * sample_rate * (1 + np.sin(2 * np.pi * rate * t))
    delays = lfo.astype(int)
    wet = np.zeros_like(audio)
    for i in range(n):
        d = delays[i]
        j = i - d
        if j >= 0:
            wet[i] = audio[j]
    return np.clip((1 - mix) * audio + mix * wet, -1, 1)


# ── 效果链统一接口 ──────────────────────────────────

EFFECT_PRESETS: dict = {
    "gentle_boost":  {"type": "eq", "low_gain": 1.1, "mid_gain": 1.0, "high_gain": 1.05},
    "soft_comp":     {"type": "compressor", "threshold": 0.6, "ratio": 3.0},
    "room_medium":   {"type": "reverb", "amount": 0.35},
    "hall_large":    {"type": "reverb", "amount": 0.6},
    "slap_delay":    {"type": "delay", "time_sec": 0.12, "feedback": 0.3, "mix": 0.25},
    "warm_chorus":   {"type": "chorus", "rate": 1.2, "depth": 0.005, "mix": 0.4},
}


def apply_effect(audio: np.ndarray, effect: dict,
                 sample_rate: int = 44100) -> np.ndarray:
    """通过字典描述应用单个效果"""
    et = effect.get("type", "")
    if et == "reverb":
        return apply_reverb(audio, effect.get("amount", 0.4), sample_rate)
    elif et == "eq":
        return apply_eq(audio, effect.get("low_gain", 1.0),
                        effect.get("mid_gain", 1.0),
                        effect.get("high_gain", 1.0), sample_rate)
    elif et == "compressor":
        return apply_compressor(audio, effect.get("threshold", 0.5),
                                effect.get("ratio", 4.0), sample_rate=sample_rate)
    elif et == "delay":
        return apply_delay(audio, effect.get("time_sec", 0.3),
                           effect.get("feedback", 0.4),
                           effect.get("mix", 0.3), sample_rate)
    elif et == "chorus":
        return apply_chorus(audio, effect.get("rate", 1.5),
                            effect.get("depth", 0.004),
                            effect.get("mix", 0.5), sample_rate)
    return audio


def apply_effect_chain(audio: np.ndarray, chain: list,
                       sample_rate: int = 44100) -> np.ndarray:
    """按顺序应用效果链"""
    result = audio.copy()
    for item in chain:
        if isinstance(item, str):
            item = EFFECT_PRESETS.get(item, {})
        if item:
            result = apply_effect(result, item, sample_rate)
    return result
