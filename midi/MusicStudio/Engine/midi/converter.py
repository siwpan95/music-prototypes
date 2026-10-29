#!/usr/bin/env python3
"""
MusicStudioPro - MIDI Converter
从 JSON 配置生成 MIDI 文件（pro1/2 整合版）
"""
from __future__ import annotations
import json
import os
import pretty_midi
from typing import List, Dict, Optional


def json_to_midi(json_path: str, output_path: Optional[str] = None,
                 tempo: float = 120.0, time_sig: str = "4/4") -> str:
    """
    将乐器参数 JSON 转换为 MIDI 文件
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    metadata = data.get("metadata", {})
    params = data.get("parameters", {})
    notes_data = data.get("notes", [])
    program = metadata.get("program", 0)
    channel = metadata.get("channel", 0)
    is_drum = metadata.get("is_drum", False) or channel == 9

    instrument = pretty_midi.Instrument(
        program=program,
        is_drum=is_drum,
        name=metadata.get("instrument_name", "Untitled")
    )

    for note in notes_data:
        n = pretty_midi.Note(
            velocity=note.get("velocity", 100),
            pitch=note.get("pitch", 60),
            start=note.get("start", 0.0),
            end=note.get("start", 0.0) + note.get("duration", 0.5)
        )
        instrument.notes.append(n)

    midi.instruments.append(instrument)

    if output_path is None:
        name = os.path.splitext(os.path.basename(json_path))[0]
        output_path = os.path.join(
            os.path.dirname(json_path).replace("Instruments", "MIDI"),
            f"{name}.mid"
        )
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    midi.write(output_path)
    print(f"[MIDI] 已生成: {output_path}")
    return output_path


def batch_json_to_midi(json_dir: str, midi_dir: str,
                       tempo: float = 120.0) -> List[str]:
    """批量将 JSON 目录转换为 MIDI 文件"""
    os.makedirs(midi_dir, exist_ok=True)
    paths = []
    for fname in sorted(os.listdir(json_dir)):
        if fname.endswith(".json"):
            json_path = os.path.join(json_dir, fname)
            midi_name = os.path.splitext(fname)[0] + ".mid"
            midi_path = os.path.join(midi_dir, midi_name)
            try:
                path = json_to_midi(json_path, midi_path, tempo)
                paths.append(path)
            except Exception as e:
                print(f"[MIDI] 转换失败 {fname}: {e}")
    print(f"[MIDI] 批量完成，共 {len(paths)} 个文件")
    return paths


def midi_to_json(midi_path: str, output_path: Optional[str] = None) -> Dict:
    """
    将 MIDI 文件反向解析为配置 JSON
    （用于导入外部 MIDI）
    """
    midi = pretty_midi.PrettyMIDI(midi_path)
    instruments_data = []

    for inst in midi.instruments:
        inst_data = {
            "metadata": {
                "instrument_name": inst.name or "Unknown",
                "program": inst.program,
                "channel": 0,
                "is_drum": inst.is_drum,
                "creation_time": "",
                "version": "2.0"
            },
            "parameters": {"volume": 100, "pan": 64},
            "notes": []
        }
        for note in inst.notes:
            inst_data["notes"].append({
                "pitch": note.pitch,
                "velocity": note.velocity,
                "start": round(note.start, 4),
                "duration": round(note.end - note.start, 4)
            })
        instruments_data.append(inst_data)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(instruments_data, f, ensure_ascii=False, indent=2)
        print(f"[MIDI] 已导出 JSON: {output_path}")

    return instruments_data
