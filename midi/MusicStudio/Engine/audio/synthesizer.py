#!/usr/bin/env python3
"""
MusicStudioPro - 音频合成器
将 MIDI 文件合成为 WAV 音频（FluidSynth 或软件合成器回退）
"""
from __future__ import annotations
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Union
from tqdm import tqdm

from Engine.audio.soft_synth import synthesize_from_midi_json as soft_synth_json


# ── SoundFont 自动搜索 ─────────────────────────────────────────────────
def find_soundfont() -> Optional[str]:
    """在多个位置搜索 .sf2 SoundFont 文件"""
    search_paths = [
        Path(__file__).parent.parent.parent / "Libs" / "SoundFonts",
        Path("Libs/SoundFonts"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "MuseScore" / "MuseScore3" / "sound",
    ]
    for base in search_paths:
        if base.is_file() and base.suffix.lower() == ".sf2":
            return str(base)
        if base.is_dir():
            for f in base.glob("*.sf2"):
                return str(f)
    return None


def check_fluidsynth() -> bool:
    """检查 FluidSynth 是否可用"""
    try:
        import pyfluidsynth
        return True
    except ImportError:
        pass
    return False


def load_audio(filepath: str) -> Optional[np.ndarray]:
    """加载音频文件"""
    try:
        import soundfile as sf
        audio, _ = sf.read(filepath)
        return audio
    except Exception as e:
        print(f"  [WARN] 加载音频失败 ({filepath}): {e}")
        return None


def midi_to_wav_fluidsynth(
    midi_path: str,
    wav_path: str,
    soundfont_path: Optional[str] = None,
    sample_rate: int = 44100,
) -> bool:
    """使用 FluidSynth 将 MIDI 文件转为 WAV"""
    import pretty_midi
    import soundfile as sf

    if soundfont_path is None:
        soundfont_path = find_soundfont()
    if soundfont_path is None or not Path(soundfont_path).exists():
        return False

    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
        audio = pm.fluidsynth(fs=sample_rate, sf2_path=soundfont_path)
        if audio is None or len(audio) == 0:
            return False
        sf.write(wav_path, audio, sample_rate)
        return True
    except Exception as e:
        print(f"  [WARN] FluidSynth: {e}")
        return False


def midi_json_to_wav_software(
    midi_data: dict,
    wav_path: str,
    sample_rate: int = 44100,
) -> bool:
    """使用软件合成器将 MIDI JSON 数据合成为 WAV"""
    try:
        import soundfile as sf
        audio_list, track_names = soft_synth_json(midi_data, sample_rate)

        if not audio_list:
            return False

        max_len = max(len(a) for a in audio_list)
        mixed = np.zeros(max_len)
        for audio in audio_list:
            if len(audio) < max_len:
                audio = np.pad(audio, (0, max_len - len(audio)))
            mixed += audio

        max_val = np.max(np.abs(mixed))
        if max_val > 0:
            mixed /= max_val * 1.05

        sf.write(wav_path, mixed, sample_rate)
        return True
    except Exception as e:
        print(f"  [ERROR] 软件合成失败: {e}")
        return False


def batch_synthesize(
    midi_dir: str,
    output_dir: str,
    soundfont_path: Optional[str] = None,
    sample_rate: int = 44100,
    bpm: float = 120.0,
) -> List[str]:
    """
    批量合成：读取 MIDI 文件目录，输出 WAV 文件
    
    合成策略：
    1. 优先使用 FluidSynth (需 SoundFont)
    2. 回退到软件合成器 (纯 numpy, 无需额外安装)
    
    Args:
        midi_dir: MIDI 文件目录（含 .mid 和 .json）
        output_dir: WAV 输出目录
        soundfont_path: SoundFont 路径
        sample_rate: 采样率
        bpm: 备用 BPM（用于 JSON）
    Returns:
        wav_paths: 成功合成的 WAV 文件路径列表
    """
    midi_path = Path(midi_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not midi_path.exists():
        print(f"  [WARN] MIDI 目录不存在: {midi_dir}")
        return []

    # 检查引擎
    sf_path = soundfont_path or find_soundfont()
    has_fs = check_fluidsynth() and sf_path is not None

    if has_fs:
        print(f"\n[合成引擎] FluidSynth + {sf_path}")
    else:
        print(f"\n[合成引擎] 软件合成器 (音质受限)")
        print("  [INFO] 安装 SoundFont 以获得更好音质: python setup.py")

    wav_paths = []
    midi_files = sorted(midi_path.glob("*.mid"))
    json_files = {f.stem: f for f in midi_path.glob("*.json")}

    if not midi_files:
        print(f"  [WARN] 目录中无 MIDI 文件: {midi_dir}")
        return []

    for mf in tqdm(midi_files, desc="合成音频"):
        base_name = mf.stem
        wav_path = out_path / f"{base_name}.wav"
        success = False

        # 方法1: FluidSynth
        if has_fs:
            try:
                success = midi_to_wav_fluidsynth(str(mf), str(wav_path), sf_path, sample_rate)
                if success:
                    if not "skip" in os.environ.get("DEBUG", ""):
                        pass
            except Exception as e:
                print(f"  [WARN] FluidSynth({base_name}): {e}")

        # 方法2: 软件合成器 (从 JSON 数据)
        if not success and base_name in json_files:
            try:
                with open(json_files[base_name], "r", encoding="utf-8") as f:
                    midi_data = json.load(f)
                success = midi_json_to_wav_software(midi_data, str(wav_path), sample_rate)
            except Exception as e:
                print(f"  [WARN] 软件合成({base_name}): {e}")

        # 方法3: 从 MIDI 文件直接软件合成
        if not success:
            try:
                import pretty_midi
                pm = pretty_midi.PrettyMIDI(str(mf))
                # 构建简单的 JSON 数据
                midi_data = {
                    "name": base_name,
                    "bpm": bpm,
                    "tracks": []
                }
                for inst in pm.instruments:
                    track = {
                        "name": inst.name or f"Track_{len(midi_data['tracks'])}",
                        "program": inst.program,
                        "notes": []
                    }
                    for note in inst.notes:
                        track["notes"].append({
                            "pitch": note.pitch,
                            "start_time": note.start,
                            "duration": note.end - note.start,
                            "velocity": note.velocity,
                        })
                    midi_data["tracks"].append(track)
                success = midi_json_to_wav_software(midi_data, str(wav_path), sample_rate)
            except Exception as e:
                print(f"  [WARN] MIDI软件合成({base_name}): {e}")

        if success and wav_path.exists():
            wav_paths.append(str(wav_path))

    print(f"\n  合成完成: {len(wav_paths)}/{len(midi_files)} 个文件")
    return wav_paths


def synthesize_midi(
    midi_data: dict,
    output_path: str,
    soundfont_path: Optional[str] = None,
    sample_rate: int = 44100,
    bpm: float = 120.0,
) -> bool:
    """
    合成单个 MIDI JSON 为 WAV（供外部调用）
    自动选择 FluidSynth 或软件合成器
    """
    import pretty_midi
    from Engine.midi.converter import json_to_midi

    # 先尝试写 MIDI + FluidSynth
    temp_midi = Path(output_path).with_suffix(".temp.mid")
    try:
        midi_obj = json_to_midi(midi_data)
        midi_obj.write(str(temp_midi))
        sf_path = soundfont_path or find_soundfont()
        if sf_path and check_fluidsynth():
            if midi_to_wav_fluidsynth(str(temp_midi), output_path, sf_path, sample_rate):
                if temp_midi.exists():
                    temp_midi.unlink(missing_ok=True)
                return True
    except Exception:
        pass

    # 回退: 软件合成
    result = midi_json_to_wav_software(midi_data, output_path, sample_rate)
    if temp_midi.exists():
        temp_midi.unlink(missing_ok=True)
    return result
