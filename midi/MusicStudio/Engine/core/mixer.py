#!/usr/bin/env python3
"""
MusicStudioPro - Core Mixer
整合 pro1 MusicMixer + DynamicOrchestrator 的完整混音引擎
"""
from __future__ import annotations
import numpy as np
import soundfile as sf
import os
from typing import Dict, List, Optional, Tuple


class Track:
    """单音轨数据容器"""

    def __init__(self, name: str, audio: np.ndarray, sample_rate: int = 44100,
                 volume: float = 1.0, pan: float = 0.5,
                 layer: int = 0, mute_group: Optional[str] = None):
        self.name = name
        self.audio = self._ensure_stereo(audio)
        self.sample_rate = sample_rate
        self.volume = volume
        self.pan = pan        # 0.0=左  1.0=右  0.5=中
        self.layer = layer
        self.mute_group = mute_group
        self.muted = False
        self.soloed = False
        self.effects: List[dict] = []

    @staticmethod
    def _ensure_stereo(audio: np.ndarray) -> np.ndarray:
        if audio.ndim == 1:
            return np.vstack([audio, audio]).T
        if audio.shape[0] == 2 and audio.shape[1] != 2:
            return audio.T
        return audio


class MusicMixer:
    """
    多轨混音引擎 (pro1 升级版)
    支持：音量/声相/淡入淡出/静音组/独奏层/防削波/分轨导出
    """

    def __init__(self, sample_rate: int = 44100, max_tracks: int = 32):
        self.sample_rate = sample_rate
        self.max_tracks = max_tracks
        self.tracks: Dict[str, Track] = {}
        self.mute_groups: Dict[str, List[str]] = {}
        self.master_volume = 1.0
        self.master_audio: Optional[np.ndarray] = None

    # ──────────────── 轨道管理 ────────────────

    def add_track(self, name: str, audio: np.ndarray, volume: float = 1.0,
                  pan: float = 0.5, layer: int = 0,
                  mute_group: Optional[str] = None) -> bool:
        if len(self.tracks) >= self.max_tracks:
            print(f"[Mixer] 已达最大轨道数 {self.max_tracks}")
            return False
        track = Track(name, audio, self.sample_rate, volume, pan, layer, mute_group)
        self.tracks[name] = track
        if mute_group:
            self.mute_groups.setdefault(mute_group, []).append(name)
        return True

    def remove_track(self, name: str) -> bool:
        if name not in self.tracks:
            return False
        t = self.tracks.pop(name)
        if t.mute_group and t.mute_group in self.mute_groups:
            self.mute_groups[t.mute_group] = [
                n for n in self.mute_groups[t.mute_group] if n != name
            ]
        return True

    # ──────────────── 混音控制 ────────────────

    def mute_group(self, group_name: str, muted: bool = True):
        for name in self.mute_groups.get(group_name, []):
            if name in self.tracks:
                self.tracks[name].muted = muted

    def solo_layer(self, layer: int):
        for track in self.tracks.values():
            if track.layer == layer:
                track.soloed = True
                track.muted = False
            else:
                track.muted = True

    def clear_solo(self):
        for track in self.tracks.values():
            track.soloed = False
            track.muted = False

    def apply_fade(self, track_name: str, fade_in_sec: float = 0.0,
                   fade_out_sec: float = 0.0):
        if track_name not in self.tracks:
            return
        audio = self.tracks[track_name].audio
        n = len(audio)
        sr = self.sample_rate
        if fade_in_sec > 0:
            fi = int(fade_in_sec * sr)
            ramp = np.linspace(0, 1, min(fi, n))
            audio[:len(ramp), 0] *= ramp
            audio[:len(ramp), 1] *= ramp
        if fade_out_sec > 0:
            fo = int(fade_out_sec * sr)
            ramp = np.linspace(1, 0, min(fo, n))
            audio[-len(ramp):, 0] *= ramp
            audio[-len(ramp):, 1] *= ramp

    # ──────────────── 混音 ────────────────

    def set_track_audio(self, name: str, audio: np.ndarray) -> bool:
        """替换轨道音频数据"""
        if name in self.tracks:
            self.tracks[name].audio = audio
            return True
        return False

    def get_track_names(self) -> List[str]:
        """获取所有轨道名"""
        return list(self.tracks.keys())

    def mix(self) -> np.ndarray:
        # 跳过静音轨道和 None 音频轨道
        active = [t for t in self.tracks.values()
                  if not t.muted and t.audio is not None and len(t.audio) > 0]
        if not active:
            return np.zeros((self.sample_rate, 2), dtype=np.float32)

        max_len = max(len(t.audio) for t in active)
        mix = np.zeros((max_len, 2), dtype=np.float64)

        for t in active:
            audio = t.audio.astype(np.float64)
            # 单声道 → 立体声
            if audio.ndim == 1:
                audio = np.column_stack([audio, audio])
            # 声相
            left_gain = t.volume * (1.0 - t.pan)
            right_gain = t.volume * t.pan
            # 对齐长度
            padded = np.zeros((max_len, 2))
            length = min(len(audio), max_len)
            padded[:length] = audio[:length]
            mix[:, 0] += padded[:, 0] * left_gain
            mix[:, 1] += padded[:, 1] * right_gain

        # 主音量 + 防削波
        mix *= self.master_volume
        peak = np.max(np.abs(mix))
        if peak > 1.0:
            mix /= peak
        self.master_audio = mix.astype(np.float32)
        return self.master_audio

    # ──────────────── 导出 ────────────────

    def export_wav(self, path: str, normalized: bool = True) -> bool:
        audio = self.mix()
        if normalized:
            peak = np.max(np.abs(audio))
            if peak > 0:
                audio = audio / peak
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        sf.write(path, audio, self.sample_rate)
        print(f"[Mixer] 已导出: {path}")
        return True

    def export_stems(self, folder: str) -> List[str]:
        os.makedirs(folder, exist_ok=True)
        paths = []
        for name, track in self.tracks.items():
            if not track.muted:
                path = os.path.join(folder, f"{name}.wav")
                sf.write(path, track.audio, self.sample_rate)
                paths.append(path)
        print(f"[Mixer] 分轨导出: {len(paths)} 个文件 → {folder}")
        return paths
