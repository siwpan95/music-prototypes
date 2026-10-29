#!/usr/bin/env python3
"""
MusicStudioPro - Project Manager
整合 pro2 exa/1.py ProjectPackage + 项目持久化
"""
from __future__ import annotations
import json
import os
import pickle
import base64
import zlib
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any


@dataclass
class Project:
    """项目数据容器"""
    name: str = "Untitled"
    author: str = "Anonymous"
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 音乐参数
    tempo: float = 120.0
    time_signature: str = "4/4"
    key: str = "C"
    sample_rate: int = 44100
    mood: str = "happy"
    complexity: int = 3

    # 数据
    instruments: List[Dict] = field(default_factory=list)
    midi_tracks: List[Dict] = field(default_factory=list)
    mixer_settings: Dict = field(default_factory=dict)
    effects_chain: List[Dict] = field(default_factory=list)
    vocal_tracks: List[Dict] = field(default_factory=list)
    resources: Dict = field(default_factory=dict)


class ProjectManager:
    """
    项目保存/加载管理器
    支持 JSON（可读）和 .mspro（压缩二进制）两种格式
    """

    # ── 保存 ──────────────────────────────────

    @staticmethod
    def save_json(project: Project, path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        project.modified_at = datetime.now().isoformat()
        data = asdict(project)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Project] 已保存 JSON: {path}")
        return path

    @staticmethod
    def save_binary(project: Project, path: str) -> str:
        """压缩二进制格式（.mspro）"""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        project.modified_at = datetime.now().isoformat()
        raw = pickle.dumps(asdict(project))
        compressed = zlib.compress(raw, level=9)
        encoded = base64.b64encode(compressed)
        checksum = hashlib.md5(encoded).hexdigest()
        payload = json.dumps({
            "checksum": checksum,
            "data": encoded.decode("ascii")
        }).encode("utf-8")
        with open(path, "wb") as f:
            f.write(payload)
        print(f"[Project] 已保存二进制: {path}")
        return path

    # ── 加载 ──────────────────────────────────

    @staticmethod
    def load_json(path: str) -> Optional[Project]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Project(**{k: v for k, v in data.items()
                              if k in Project.__dataclass_fields__})
        except Exception as e:
            print(f"[Project] 加载失败: {e}")
            return None

    @staticmethod
    def load_binary(path: str) -> Optional[Project]:
        try:
            with open(path, "rb") as f:
                payload = json.loads(f.read())
            checksum = payload["checksum"]
            encoded = payload["data"].encode("ascii")
            assert hashlib.md5(encoded).hexdigest() == checksum, "校验失败"
            data = pickle.loads(zlib.decompress(base64.b64decode(encoded)))
            return Project(**{k: v for k, v in data.items()
                              if k in Project.__dataclass_fields__})
        except Exception as e:
            print(f"[Project] 加载失败: {e}")
            return None

    @classmethod
    def load(cls, path: str) -> Optional[Project]:
        if path.endswith(".json"):
            return cls.load_json(path)
        return cls.load_binary(path)
