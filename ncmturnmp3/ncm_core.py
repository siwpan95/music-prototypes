# -*- coding: utf-8 -*-
"""
ncm_core.py —— 旧版核心模块的兼容层（已废弃）

原有职责已泛化迁移：
  - 解密算法        → decryptors.py（ncm 之外新增 qmc/kgm/kwm/xm/mg3d/tm 等）
  - 转换/打标/调度  → audio_core.py（输出格式可选，不再局限于 mp3）

保留本文件仅为兼容可能引用 `import ncm_core` 的旧脚本，
接口签名与旧版一致。新代码请直接使用 audio_core / decryptors。
"""
from decryptors import decrypt_ncm  # noqa: F401  （旧版直接可用的解密函数）
from audio_core import (  # noqa: F401
    check_ffmpeg,
    collect_ncm_files,
    convert_to_mp3,
    write_tags as _write_tags,
)

# 旧版 tag_mp3(mp3_path, metadata, cover_bytes) 签名适配
from audio_core import _meta_from_filename, _read_tags_from_bytes


def tag_mp3(mp3_path, metadata, cover_bytes):
    """旧版接口：按 ncm 元数据字典写 ID3 标签。"""
    md = metadata or {}
    title = md.get("musicName", "")
    artists = ""
    if md.get("artist"):
        try:
            artists = "/".join(str(a[0]) for a in md["artist"] if a and a[0])
        except Exception:
            artists = ""
    album = md.get("album", "")
    from audio_core import write_tags
    return write_tags(mp3_path, "mp3",
                      {"title": title, "artist": artists, "album": album},
                      cover_bytes)


def process_one(ncm_path, out_dir=None, bitrate="320k"):
    """旧版接口：仅处理 .ncm → mp3。新功能（多格式/多输出）请用 audio_core.process_one。"""
    from audio_core import process_one as _new
    return _new(ncm_path, out_dir, "mp3", bitrate)
