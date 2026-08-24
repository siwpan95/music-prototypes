# -*- coding: utf-8 -*-
"""
audio_core.py —— 通用加密音乐转换核心（GUI / CLI / 拖拽 / bat 共用）

管线：输入识别（扩展名+魔数）→ 解密（decryptors）→ ffmpeg 转码 → mutagen 写标签。

支持：
  输入  ncm / qmc 全家族(v1+v2) / tm 缓存 / kgm / kgma / vpr / kwm / xm / mg3d
        以及普通音频 mp3/flac/wav/m4a/aac/ogg/oga/opus/wma/ape
  输出  mp3(默认) / flac / wav / aac / ogg / m4a / 原始格式（仅解密不转码）
  标签  歌名/歌手/专辑/封面：优先取加密文件内嵌元数据（ncm），
        其次取解密后音频自带标签，最后回退"歌手 - 歌名"文件名解析；
        按输出格式写入 ID3 / VorbisComment / FLAC Picture / MP4 标签。

智能行为：
  - 目标格式与源音频格式相同时直接写出原始字节（不重编码），
    避免无意义的二次编码造成音质损失；码率参数仅对实际转码的有损格式生效。
  - 输出文件已存在时跳过（与旧版行为一致）。

本模块完全本地运行，不联网。
"""
import base64
import os
import subprocess
import tempfile

import mutagen
from mutagen import flac as _flac_mod, id3, mp4, wave as _wave_mod

import decryptors

# --------------------------------------------------------------------------- #
# 输出格式定义
# --------------------------------------------------------------------------- #
# codec 为 ffmpeg 参数；bitrate=True 表示该格式接受码率参数（有损格式）
OUTPUT_FORMATS = {
    "mp3":  {"ext": ".mp3",  "codec": ["-c:a", "libmp3lame"], "bitrate": True},
    "flac": {"ext": ".flac", "codec": ["-c:a", "flac"],       "bitrate": False},
    "wav":  {"ext": ".wav",  "codec": ["-c:a", "pcm_s16le"],  "bitrate": False},
    "aac":  {"ext": ".aac",  "codec": ["-c:a", "aac"],        "bitrate": True},
    "ogg":  {"ext": ".ogg",  "codec": ["-c:a", "libvorbis"],  "bitrate": True},
    "m4a":  {"ext": ".m4a",  "codec": ["-c:a", "aac"],        "bitrate": True},
    "orig": {"ext": None,    "codec": None,                   "bitrate": False},  # 原始格式
}
OUTPUT_FORMAT_NAMES = ["mp3", "flac", "wav", "aac", "ogg", "m4a", "orig"]
DEFAULT_OUTPUT_FORMAT = "mp3"
DEFAULT_BITRATE = "320k"

FILE_DIALOG_PATTERNS = [
    ("加密音乐 (ncm/qmc/kgm/kwm/xm/mg3d/tm)",
     "*.ncm *.qmc* *.tkm *.bkcmp3 *.bkcflac *.bkcwav *.bkcogg *.bkcaac *.mflac* *.mgg* *.mmp4 "
     "*.tm0 *.tm2 *.tm3 *.tm6 *.kgm *.kgma *.vpr *.kwm *.xm *.mg3d"),
    ("音频文件", "*.mp3 *.flac *.wav *.m4a *.aac *.ogg *.oga *.opus *.wma *.ape"),
    ("所有文件", "*.*"),
]


def check_ffmpeg():
    """检查系统是否安装了 ffmpeg。"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# --------------------------------------------------------------------------- #
# 输入收集
# --------------------------------------------------------------------------- #
def collect_files(paths):
    """
    收集多个输入路径（文件或目录）下所有受支持的文件，返回排重后的有序列表。
      - 文件：一律收入（未知扩展名由 process_one 做魔数兜底识别）；
      - 目录：递归遍历，只收已知扩展名（避免把无关文件当成音频）；
      - 跳过 macOS 元数据垃圾（._* AppleDouble / .DS_Store）。
    """
    def _is_junk(name):
        return name.startswith("._") or name == ".DS_Store"

    seen = set()
    result = []
    for p in paths:
        if os.path.isfile(p):
            if not _is_junk(os.path.basename(p)) and p not in seen:
                seen.add(p)
                result.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    if _is_junk(f):
                        continue
                    ext = os.path.splitext(f)[1].lstrip(".").lower()
                    if ext in decryptors.SUPPORTED_INPUT_EXTS:
                        fp = os.path.join(root, f)
                        if fp not in seen:
                            seen.add(fp)
                            result.append(fp)
    return result


def collect_ncm_files(paths):
    """兼容旧入口名：只收集 .ncm 文件。"""
    return [p for p in collect_files(paths) if p.lower().endswith(".ncm")]


# --------------------------------------------------------------------------- #
# 标签读写（mutagen，按格式分发）
# --------------------------------------------------------------------------- #
def _read_tags_from_bytes(audio_bytes, fmt):
    """把解密后的音频字节落临时文件并用 mutagen 读标签（读不到返回 None）。"""
    with tempfile.TemporaryDirectory() as td:
        probe = os.path.join(td, "probe." + fmt)
        with open(probe, "wb") as f:
            f.write(audio_bytes)
        return _read_tags_from_file(probe)


def _read_tags_from_file(path):
    """用 mutagen 读取音频文件标签，返回 dict(title/artist/album/cover) 或 None。"""
    try:
        easy = mutagen.File(path, easy=True)
        if easy is None or easy.tags is None:
            return None
        title = str(easy.get("title", [""])[0] or "")
        artist = str(easy.get("artist", [""])[0] or "")
        album = str(easy.get("album", [""])[0] or "")
        cover = _extract_cover(path)
        if not (title or artist or album or cover):
            return None
        return {"title": title, "artist": artist, "album": album, "cover": cover}
    except Exception:
        return None


def _extract_cover(path):
    """从音频文件提取封面字节（ID3/FLAC/OGG/MP4）。"""
    try:
        raw = mutagen.File(path)
        if raw is None:
            return None
        # ID3（mp3/wav）
        if raw.tags is not None:
            for frame in raw.tags.getall("APIC"):
                return bytes(frame.data)
        # FLAC / OGG
        pics = getattr(raw, "pictures", None)
        if pics:
            return bytes(pics[0].data)
        # MP4
        if isinstance(raw.tags, mp4.MP4Tags) and "covr" in raw.tags:
            return bytes(raw.tags["covr"][0])
    except Exception:
        pass
    return None


def _cover_mime(data):
    if data[:4] == b"\x89PNG":
        return "image/png"
    return "image/jpeg"


def write_tags(path, fmt, meta, cover=None):
    """
    把歌名/歌手/专辑/封面写入音频文件（按格式选择标签体系）。
    meta 为 dict(title/artist/album)；cover 为封面字节或 None。
    不支持内嵌标签的格式（如裸 aac ADTS）返回 False。
    """
    if not (meta and any(meta.values())) and not cover:
        return False
    meta = meta or {}
    try:
        if fmt == "flac":
            return _tag_flac(path, meta, cover)
        if fmt in ("ogg", "oga", "opus"):
            return _tag_vorbis(path, meta, cover)
        if fmt == "m4a":
            return _tag_mp4(path, meta, cover)
        if fmt in ("mp3", "wav"):
            return _tag_id3(path, meta, cover, wave=(fmt == "wav"))
        return False
    except Exception:
        return False


def _tag_id3(path, meta, cover, wave=False):
    audio = _wave_mod.WAVE(path) if wave else mutagen.File(path)
    if audio is None:
        return False
    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags
    if meta.get("title"):
        tags.setall("TIT2", [id3.TIT2(text=meta["title"], encoding=id3.Encoding.UTF8)])
    if meta.get("artist"):
        tags.setall("TPE1", [id3.TPE1(text=meta["artist"], encoding=id3.Encoding.UTF8)])
        tags.setall("TPE2", [id3.TPE2(text=meta["artist"], encoding=id3.Encoding.UTF8)])
    if meta.get("album"):
        tags.setall("TALB", [id3.TALB(text=meta["album"], encoding=id3.Encoding.UTF8)])
    if cover:
        tags.setall("APIC", [id3.APIC(
            encoding=id3.Encoding.UTF8, type=3, mime=_cover_mime(cover),
            data=cover, desc="",
        )])
    audio.save()
    return True


def _tag_flac(path, meta, cover):
    audio = _flac_mod.FLAC(path)
    if meta.get("title"):
        audio["title"] = meta["title"]
    if meta.get("artist"):
        audio["artist"] = meta["artist"]
    if meta.get("album"):
        audio["album"] = meta["album"]
    if cover:
        pic = _flac_mod.Picture()
        pic.type = 3
        pic.mime = _cover_mime(cover)
        pic.data = cover
        audio.clear_pictures()
        audio.add_picture(pic)
    audio.save()
    return True


def _tag_vorbis(path, meta, cover):
    audio = mutagen.File(path)  # ogg/oga/opus 容器自动识别
    if audio is None:
        return False
    if meta.get("title"):
        audio["title"] = meta["title"]
    if meta.get("artist"):
        audio["artist"] = meta["artist"]
    if meta.get("album"):
        audio["album"] = meta["album"]
    if cover:
        pic = _flac_mod.Picture()
        pic.type = 3
        pic.mime = _cover_mime(cover)
        pic.data = cover
        audio["metadata_block_picture"] = [base64.b64encode(pic.write()).decode("ascii")]
    audio.save()
    return True


def _tag_mp4(path, meta, cover):
    audio = mp4.MP4(path)
    if audio.tags is None:
        audio.add_tags()
    if meta.get("title"):
        audio["\xa9nam"] = [meta["title"]]
    if meta.get("artist"):
        audio["\xa9ART"] = [meta["artist"]]
        audio["aART"] = [meta["artist"]]
    if meta.get("album"):
        audio["\xa9alb"] = [meta["album"]]
    if cover:
        fmt_png = cover[:4] == b"\x89PNG"
        audio["covr"] = [mp4.MP4Cover(
            cover, imageformat=mp4.MP4Cover.FORMAT_PNG if fmt_png else mp4.MP4Cover.FORMAT_JPEG
        )]
    audio.save()
    return True


# --------------------------------------------------------------------------- #
# 元数据归一化
# --------------------------------------------------------------------------- #
def _meta_from_ncm(parsed):
    """ncm 内嵌元数据 → 归一化 dict。"""
    md = parsed.get("metadata") or {}
    title = str(md.get("musicName") or "")
    artists = ""
    if md.get("artist"):
        try:
            artists = "/".join(str(a[0]) for a in md["artist"] if a and a[0])
        except Exception:
            artists = ""
    album = str(md.get("album") or "")
    return {"title": title, "artist": artists, "album": album}


def _meta_from_filename(base):
    """从"歌手 - 歌名"文件名解析元数据兜底。"""
    if " - " in base:
        artist, title = base.split(" - ", 1)
        return {"title": title.strip(), "artist": artist.strip(), "album": ""}
    return {"title": base, "artist": "", "album": ""}


# --------------------------------------------------------------------------- #
# ffmpeg 转码
# --------------------------------------------------------------------------- #
def _run_ffmpeg(src, dst, fmt_key, bitrate):
    spec = OUTPUT_FORMATS[fmt_key]
    cmd = ["ffmpeg", "-i", src, "-y", "-vn"]
    cmd += spec["codec"]
    if spec["bitrate"] and bitrate:
        cmd += ["-ab", bitrate]
    # 清除源标签，稍后由 write_tags 按输出格式统一重写（值已提前从解密结果读取）
    cmd += ["-map_metadata", "-1", dst]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError("ffmpeg 转码失败：" + err[-300:])


def convert_to_mp3(raw_path, mp3_path, bitrate="320k"):
    """兼容旧入口名：ncm_core.convert_to_mp3。"""
    _run_ffmpeg(raw_path, mp3_path, "mp3", bitrate)


# --------------------------------------------------------------------------- #
# 单文件处理
# --------------------------------------------------------------------------- #
def process_one(path, out_dir=None, output_format=DEFAULT_OUTPUT_FORMAT,
                bitrate=DEFAULT_BITRATE):
    """
    处理单个文件：识别 → 解密 → 转码 → 写标签。返回 (成功: bool, 信息: str)。
    """
    base = os.path.splitext(os.path.basename(path))[0]
    ext = os.path.splitext(path)[1].lstrip(".").lower()

    try:
        # ---- 1. 识别与解密 → (源格式, 音频字节, ncm元数据, ncm封面, 是否普通音频) ----
        is_plain = False
        if ext in decryptors.ENCRYPTED_EXTS:
            parsed = decryptors.decrypt_file(path, ext)
        elif ext in decryptors.AUDIO_EXTS:
            parsed = decryptors.decrypt_plain(path)
            is_plain = True
        else:
            # 未知扩展名（仅可能来自显式添加的文件）：魔数兜底
            with open(path, "rb") as f:
                data = f.read()
            if data[:8] == decryptors.NCM_FILE_MAGIC:
                parsed = decryptors.decrypt_ncm(path)
            elif data[:16] in (decryptors.KGM_FILE_MAGIC, decryptors.VPR_FILE_MAGIC):
                parsed = decryptors.decrypt_kgm(data)
            elif data[:16] in (decryptors.KWM_FILE_MAGIC, decryptors.KWM_FILE_MAGIC2):
                parsed = decryptors.decrypt_kwm(data)
            elif data[:4] == decryptors.XM_FILE_MAGIC:
                parsed = decryptors.decrypt_xm(data)
            elif decryptors.looks_like_plain_audio(data[:64]):
                parsed = decryptors.decrypt_plain(path)
                is_plain = True
            else:
                return False, "无法识别的文件格式：" + os.path.basename(path)

        src_fmt = parsed["format"]
        audio_bytes = parsed["audio"]
        ncm_meta = _meta_from_ncm(parsed) if ext in decryptors.NCM_EXTS else None
        ncm_cover = parsed.get("cover")

        # ---- 2. 计算输出路径 ----
        target_fmt = src_fmt if output_format == "orig" else output_format
        out_name = base + "." + target_fmt
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, out_name)
        else:
            out_path = os.path.join(os.path.dirname(path) or ".", out_name)

        if os.path.exists(out_path):
            return True, "已存在，跳过：" + out_path

        # ---- 3. 产出音频 ----
        note = ""
        if target_fmt == src_fmt:
            # 目标即源格式：解密/原始字节直接写出，不重编码（无损、最快）
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            note = "（源为 %s，直接写出不重编码）" % src_fmt
            if is_plain:
                # 普通音频同格式复制：标签本就在文件里，无需处理
                return True, "成功：" + out_path + " " + note
        else:
            with tempfile.TemporaryDirectory() as td:
                raw = os.path.join(td, "src." + src_fmt)
                with open(raw, "wb") as f:
                    f.write(audio_bytes)
                _run_ffmpeg(raw, out_path, output_format, bitrate)

        # ---- 4. 写标签（同格式直写的解密文件 / 重编码文件）----
        meta = dict(ncm_meta) if ncm_meta else {}
        cover = ncm_cover
        # 缺失的字段从解密后音频自带标签补齐（qmc/kgm 等格式的标签在音频流内）
        if not (meta.get("title") and meta.get("artist") and meta.get("album")) or not cover:
            read = _read_tags_from_bytes(audio_bytes, src_fmt)
            if read:
                for k in ("title", "artist", "album"):
                    meta[k] = meta.get(k) or read[k]
                cover = cover or read.get("cover")
        # 仍缺歌名 → 文件名兜底
        if not meta.get("title"):
            meta["title"] = _meta_from_filename(base)["title"]
        if any(meta.values()) or cover:
            write_tags(out_path, target_fmt, meta, cover)

        return True, "成功：" + out_path + " " + note
    except Exception as e:
        return False, "异常：" + str(e)
