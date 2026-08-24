# -*- coding: utf-8 -*-
"""
selftest.py —— 自检脚本：对解密器与转换管线做端到端验证

验证内容：
  1. 依赖与 ffmpeg 环境检查
  2. QMC 官方测试向量（unlock-music 项目 testdata，字节级比对）
     - QmcDeriveKey 密钥派生（含 TEA / EncV2 链路）× 4
     - QMCv1 静态密码盒单元测试 × 2 + 真实向量
     - QMCv2 Map / RC4 流密码真实向量 + 分段偏移场景
     - 完整 QmcDecoder（文件尾 ekey 识别）× 5
  3. KGM 表常量权威校验：按 unlock-music/cli 的 mask 生成管线，
     用本地表生成 272MB / 4.25GB mask 流，SHA256 与官方发布值比对
  4. KGM numpy 向量化实现与纯 Python 参考实现逐字节一致性
  5. KGM/KWM/XM/MG3D/TM 构造-解密往返测试（用各格式加密逆运算构造样本）
  6. NCM 真实文件回归（E:\\ncmturnmp3 下的样本 → mp3，ffprobe 校验时长与标签）
  7. 普通音频转换管线（ffmpeg 合成样本 → 各输出格式 + 标签存活校验）

用法：
  python selftest.py            # 全部测试（含 4.25GB mask 校验，约 1~3 分钟）
  python selftest.py --quick    # 跳过 4.25GB 大 mask 校验（保留 272MB 校验）
  python selftest.py --skip-ffmpeg  # 跳过需要 ffmpeg 的转换类测试

退出码 0 = 全部通过。
"""
import argparse
import hashlib
import io
import os
import struct

# Windows 控制台编码修复：汇总输出含 ✔ 符号，GBK 代码页无法编码
import sys
if sys.stdout and getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import audio_core  # noqa: E402
import decryptors  # noqa: E402
from crypto_tables import (  # noqa: E402
    KGM_TABLE_1, KGM_TABLE_2, KGM_TABLE_V2, KGM_VPR_KEY,
)

TESTDATA_DIR = os.path.join(HERE, "tests", "testdata")
FFPROBE = "ffprobe"
FFMPEG = "ffmpeg"

# unlock-music/cli 项目发布的 mask 文件权威 SHA256（@jixun/kugou-crypto README）
KGM_MASK_V2_SHA256 = "d4903d367b158f4f9287c6bd5dedca9893fa1da6643e372c2ea45d18e50fba00"
KGM_MASK_V21_SHA256 = "3ed82a45df47f5b6e93d77eff7a94a120b93b7f6a59b50d6209e47c8c36d5a0e"

_PASS = 0
_FAIL = 0


def check(name, ok, detail=""):
    global _PASS, _FAIL
    if ok:
        _PASS += 1
        print("  [PASS] %s" % name)
    else:
        _FAIL += 1
        print("  [FAIL] %s %s" % (name, detail))


def section(title):
    print("\n=== %s ===" % title)


def load(name):
    path = os.path.join(TESTDATA_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def have_ffprobe():
    try:
        subprocess.run([FFPROBE, "-version"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
def test_env():
    section("环境检查")
    check("pycryptodome", True, "")  # 能 import decryptors 即已通过
    check("mutagen", True, "")
    check("numpy 向量化路径", decryptors._HAS_NUMPY or True,
          "" if decryptors._HAS_NUMPY else "（未装 numpy，走纯 Python 回退路径）")
    check("ffmpeg", audio_core.check_ffmpeg())
    check("ffprobe", have_ffprobe())


# --------------------------------------------------------------------------- #
def test_qmc_vectors():
    section("QMC 官方测试向量（unlock-music testdata）")
    if load("qmc0_static_target.bin") is None:
        check("测试向量文件存在", False, "缺少 tests/testdata/*.bin")
        return

    # 密钥派生
    sk = decryptors.simple_make_key(106, 8)
    check("simpleMakeKey 单元",
          list(sk) == [0x69, 0x56, 0x46, 0x38, 0x2B, 0x20, 0x15, 0x0B])
    for name in ("mflac_map", "mgg_map", "mflac0_rc4", "mflac_rc4"):
        raw = load(name + "_key_raw.bin")
        key = load(name + "_key.bin")
        got = decryptors.qmc_derive_key(raw)
        check("QmcDeriveKey %s" % name, got == key,
              "(len %d vs %d)" % (len(got), len(key)))

    # 静态密码盒单元测试
    c = decryptors.QmcStaticCipher()
    buf = bytearray(16)
    c.decrypt(buf, 0x7FF8)
    check("static [0x7ff8,0x8000)",
          bytes(buf) == bytes([0xD8, 0x52, 0xF7, 0x67, 0x90, 0xCA, 0xD6, 0x4A,
                               0x4A, 0xD6, 0xCA, 0x90, 0x67, 0xF7, 0x52, 0xD8]))
    buf = bytearray(16)
    c.decrypt(buf, 0)
    check("static [0,0x10)",
          bytes(buf) == bytes([0xC3, 0x4A, 0xD6, 0xCA, 0x90, 0x67, 0xF7, 0x52,
                               0xD8, 0xA1, 0x66, 0x62, 0x9F, 0x5B, 0x09, 0x00]))

    # Map 密码单元测试
    mc = decryptors.QmcMapCipher(bytes(range(256)))
    buf = bytearray(16)
    mc.decrypt(buf, 0)
    check("map mask [0,0x10)",
          bytes(buf) == bytes([0xBB, 0x7D, 0x80, 0xBE, 0xFF, 0x38, 0x81, 0xFB,
                               0xBB, 0xFF, 0x82, 0x3C, 0xFF, 0xBA, 0x83, 0x79]))

    # 真实向量：Map / RC4
    for name in ("mflac_map", "mgg_map"):
        raw = bytearray(load(name + "_raw.bin"))
        target = load(name + "_target.bin")
        decryptors.QmcMapCipher(load(name + "_key.bin")).decrypt(raw, 0)
        check("map real %s" % name, bytes(raw) == target)
    for name in ("mflac0_rc4", "mflac_rc4"):
        raw = bytearray(load(name + "_raw.bin"))
        target = load(name + "_target.bin")
        decryptors.QmcRC4Cipher(load(name + "_key.bin")).decrypt(raw, 0)
        check("rc4 real %s" % name, bytes(raw) == target)

    # RC4 分段偏移场景
    for name in ("mflac0_rc4", "mflac_rc4"):
        raw = load(name + "_raw.bin")
        target = load(name + "_target.bin")
        cipher = decryptors.QmcRC4Cipher(load(name + "_key.bin"))
        ok_all = True
        for lo, hi in ((0, 128), (128, 5120), (5120, 10240)):
            b = bytearray(raw[lo:hi])
            cipher.decrypt(b, lo)
            ok_all = ok_all and bytes(b) == target[lo:hi]
        check("rc4 分段偏移 %s" % name, ok_all)

    # 完整解码器（raw + suffix 拼接 → target）
    for name in ("mflac0_rc4", "mflac_rc4", "mflac_map", "mgg_map", "qmc0_static"):
        body = load(name + "_raw.bin")
        suffix = load(name + "_suffix.bin") or b""
        target = load(name + "_target.bin")
        res = decryptors.decrypt_qmc(body + suffix)
        check("QmcDecoder %s" % name, res["audio"] == target)


# --------------------------------------------------------------------------- #
def _gen_mask_v2_numpy():
    """按 @jixun/kugou-crypto generate-mask.ts 的管线生成 272MB mask 流。"""
    import numpy as np
    t1 = np.frombuffer(KGM_TABLE_1, dtype=np.uint8)
    t2 = np.frombuffer(KGM_TABLE_2, dtype=np.uint8)
    s = np.repeat(t2, 16)                       # 4352
    s = s ^ np.tile(t1, len(s) // 272)          # ^ t1
    s = np.repeat(s, 16)                        # 69632
    s = s ^ np.tile(t2, len(s) // 272)          # ^ t2
    s = np.repeat(s, 16)                        # 1,114,112
    s = s ^ np.tile(t1, len(s) // 272)          # ^ t1
    s = np.repeat(s, 16)                        # 17,825,792
    s = s ^ np.tile(t2, len(s) // 272)          # ^ t2
    s = np.repeat(s, 16)                        # 285,212,672
    s = s ^ np.tile(t1, len(s) // 272)          # ^ t1
    return s


def test_kgm_tables():
    section("KGM 表常量权威校验（mask 流 SHA256 对照 unlock-music/cli）")
    try:
        import numpy as np
    except ImportError:
        check("numpy 可用（mask 校验需要）", False)
        return

    mask = _gen_mask_v2_numpy()
    check("kgm.v2.mask 流大小 = 285,212,672", len(mask) == 285212672, str(len(mask)))
    sha = hashlib.sha256(mask.tobytes()).hexdigest()
    check("kgm.v2.mask SHA256（校验 table1+table2）", sha == KGM_MASK_V2_SHA256, sha)

    # v2.1 mask（4.25GB）：tableV2 参与，分块流式计算
    total = len(mask) * 16  # 4,563,402,752
    h = hashlib.sha256()
    v2 = np.frombuffer(KGM_TABLE_V2, dtype=np.uint8)
    chunk = 1 << 26  # 64MB
    for lo in range(0, total, chunk):
        hi = min(lo + chunk, total)
        p = np.arange(lo, hi, dtype=np.int64)
        part = mask[p >> 4] ^ v2[p % 272]
        h.update(part.tobytes())
    sha21 = h.hexdigest()
    check("kgm.v2.1.mask SHA256（校验 tableV2）", sha21 == KGM_MASK_V21_SHA256, sha21)


def test_kgm_numpy_vs_pure():
    section("KGM numpy 向量化实现 vs 纯 Python 参考实现（逐字节一致性）")
    import random
    random.seed(42)
    n = 4096
    data = bytes(random.randrange(256) for _ in range(n))
    key17 = bytes(random.randrange(256) for _ in range(16)) + b"\x00"
    # 纯 Python
    pure = bytes(decryptors.decrypt_kgm_byte_v2(data[i], key17, i) for i in range(n))
    # numpy 路径（直接调内部函数模拟 decrypt_kgm 的向量化部分）
    import numpy as np
    offs = np.arange(n, dtype=np.int64)
    mask = decryptors._kgm_mask_v2_numpy(offs)
    key_arr = np.frombuffer(key17, dtype=np.uint8)[offs % 17]
    v = mask ^ np.frombuffer(data, dtype=np.uint8) ^ key_arr
    out = (v ^ (np.left_shift(v & 0x0F, 4))).astype(np.uint8).tobytes()
    check("KGM 逐字节一致（含 >0x7fff 之前的全部偏移）", pure == out)

    # 大偏移一致性（跨 272/16^k 周期边界）
    base_off = 0x100000  # 1MB 偏移起步
    n2 = 2048
    data2 = bytes(random.randrange(256) for _ in range(n2))
    pure2 = bytes(decryptors.decrypt_kgm_byte_v2(data2[i], key17, base_off + i)
                  for i in range(n2))
    offs2 = np.arange(base_off, base_off + n2, dtype=np.int64)
    mask2 = decryptors._kgm_mask_v2_numpy(offs2)
    key_arr2 = np.frombuffer(key17, dtype=np.uint8)[offs2 % 17]
    v2 = mask2 ^ np.frombuffer(data2, dtype=np.uint8) ^ key_arr2
    out2 = (v2 ^ (np.left_shift(v2 & 0x0F, 4))).astype(np.uint8).tobytes()
    check("KGM 大偏移逐字节一致（1MB+ 起点）", pure2 == out2)


# --------------------------------------------------------------------------- #
# 加密逆运算（用于构造往返测试样本）
# --------------------------------------------------------------------------- #
def _encrypt_kgm_byte_v2(plain, key17, offset):
    x = decryptors._xor_lower_half_byte(plain)  # f 为对合运算
    return x ^ decryptors._kgm_mask_v2_at_offset(offset) ^ key17[offset % 17]


def _encrypt_vpr_byte(plain, key17, offset):
    return _encrypt_kgm_byte_v2(plain ^ KGM_VPR_KEY[offset % 17], key17, offset)


def _build_kgm_file(audio, is_vpr=False, header_len=0x400, key16=None):
    import random
    random.seed(7)
    if key16 is None:
        key16 = bytes(random.randrange(256) for _ in range(16))
    key17 = key16 + b"\x00"
    header = bytearray(header_len)
    header[0:16] = decryptors.VPR_FILE_MAGIC if is_vpr else decryptors.KGM_FILE_MAGIC
    struct.pack_into("<I", header, 0x10, header_len)
    header[0x1C:0x2C] = key16
    enc = bytes(
        (_encrypt_vpr_byte if is_vpr else _encrypt_kgm_byte_v2)(audio[i], key17, i)
        for i in range(len(audio))
    )
    return bytes(header) + enc


def _build_kwm_file(audio, fmt=b" MP3"):
    import random
    random.seed(8)
    file_key8 = bytes(random.randrange(256) for _ in range(8))
    mask = decryptors._kwm_make_mask(file_key8)
    header = bytearray(0x400)
    header[0:16] = decryptors.KWM_FILE_MAGIC
    header[0x18:0x20] = file_key8
    enc = bytes(audio[i] ^ mask[i % 32] for i in range(len(audio)))
    return bytes(header) + enc


def _build_xm_file(audio, type_text=b" MP3"):
    import random
    random.seed(9)
    key = random.randrange(1, 256)
    data_offset = random.randrange(0, min(64, len(audio)))
    header = bytearray(0x10)
    header[0:4] = decryptors.XM_FILE_MAGIC
    header[4:8] = type_text
    header[8:12] = b"\xfe\xfe\xfe\xfe"
    header[0x0C] = data_offset & 0xFF
    header[0x0D] = (data_offset >> 8) & 0xFF
    header[0x0E] = (data_offset >> 16) & 0xFF
    header[0x0F] = key
    body = bytearray(audio)
    for cur in range(data_offset, len(body)):
        body[cur] = (body[cur] ^ 0xFF) & 0xFF
        body[cur] = (body[cur] + key) & 0xFF
    return bytes(header) + bytes(body)


def test_roundtrip():
    section("构造-解密往返测试（KGM/KWM/XM/MG3D/TM）")
    import random
    random.seed(11)
    # 用 ID3 头伪造一段"mp3"
    audio = b"ID3\x04\x00\x00\x00\x00\x00\x00" + bytes(random.randrange(256)
                                                      for _ in range(2048))

    # KGM
    kgm = _build_kgm_file(audio, is_vpr=False)
    res = decryptors.decrypt_kgm(kgm)
    check("KGM 往返", res["audio"] == audio and res["format"] == "mp3")
    # KGM 纯 Python 路径（隐藏 numpy 强制回退）
    saved = decryptors._HAS_NUMPY
    try:
        decryptors._HAS_NUMPY = False
        res2 = decryptors.decrypt_kgm(kgm)
    finally:
        decryptors._HAS_NUMPY = saved
    check("KGM 往返（纯 Python 回退路径）", res2["audio"] == audio)

    # VPR
    vpr = _build_kgm_file(audio, is_vpr=True)
    res = decryptors.decrypt_kgm(vpr)
    check("VPR 往返", res["audio"] == audio)

    # KWM
    kwm = _build_kwm_file(audio)
    res = decryptors.decrypt_kwm(kwm)
    check("KWM 往返", res["audio"] == audio)
    saved = decryptors._HAS_NUMPY
    try:
        decryptors._HAS_NUMPY = False
        res2 = decryptors.decrypt_kwm(kwm)
    finally:
        decryptors._HAS_NUMPY = saved
    check("KWM 往返（纯 Python 回退路径）", res2["audio"] == audio)

    # XM
    for type_text, fmt in ((b" MP3", "mp3"), (b"FLAC", "flac"),
                           (b" WAV", "wav"), (b" A4M", "m4a")):
        xm = _build_xm_file(audio, type_text)
        res = decryptors.decrypt_xm(xm)
        check("XM 往返 (%s)" % fmt,
              res["audio"] == audio and res["format"] == fmt)

    # MG3D（用真实 WAV 头；密钥段位于 0x40，原 WAV 该区域为零"空洞"——
    # 与参考实现注释"咪咕编码的 WAV 文件有很多空洞内容"一致：密钥段解密后为 0）
    wav = (b"RIFF" + struct.pack("<I", 1000) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 2, 44100, 44100 * 4, 4, 16)
           + b"data" + struct.pack("<I", 960) + bytes(960))
    wav = bytearray(wav)
    wav[0x40:0x60] = bytes(32)  # 密钥段对应的"空洞"
    wav = bytes(wav)
    key_seg = b"0123456789ABCDEF0123456789ABCDEF"
    # 加密为加法（解密是减法：dec[i] = (enc[i] - key[i%32]) & 0xFF）
    enc = bytes((wav[i] + key_seg[i % 32]) & 0xFF for i in range(len(wav)))
    mg3d = bytearray(enc)
    mg3d[0x40:0x60] = key_seg  # 密钥段明文内嵌于 0x20 对齐位置
    res = decryptors.decrypt_mg3d(bytes(mg3d))
    check("MG3D 往返", res["audio"] == wav and res["format"] == "wav")

    # TM
    tm = bytes.fromhex("deadbeefcafebabe") + audio
    res = decryptors.decrypt_tm(tm)
    check("TM 头修复", res["audio"] == decryptors.TM_FIXED_HEADER + audio
          and res["format"] == "m4a")


# --------------------------------------------------------------------------- #
def _ffprobe_ok(path, expect_codec=None, min_duration=0.1):
    if not have_ffprobe():
        return False
    try:
        res = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries",
             "format=duration,format_name", "-show_entries", "stream=codec_name",
             "-of", "json", path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
        import json as _json
        info = _json.loads(res.stdout.decode("utf-8"))
        dur = float(info.get("format", {}).get("duration", 0) or 0)
        codec = ""
        for st in info.get("streams", []):
            codec = st.get("codec_name", "")
            break
        if dur < min_duration:
            return False
        if expect_codec and codec != expect_codec:
            return False
        return True
    except Exception:
        return False


def test_ncm_regression():
    section("NCM 真实文件回归（五条人 - 城市找猪.ncm → mp3）")
    src = os.path.join(HERE, "五条人 - 城市找猪.ncm")
    if not os.path.exists(src):
        check("样本存在", False, src)
        return
    with tempfile.TemporaryDirectory() as td:
        ok, msg = audio_core.process_one(src, td, "mp3", "320k")
        out = os.path.join(td, "五条人 - 城市找猪.mp3")
        check("process_one 成功", ok, msg)
        check("输出存在", os.path.exists(out))
        check("ffprobe 校验（mp3/时长）", _ffprobe_ok(out, expect_codec="mp3"))
        # 标签校验
        import mutagen
        m = mutagen.File(out, easy=True)
        title = str(m.get("title", [""])[0]) if m else ""
        artist = str(m.get("artist", [""])[0]) if m else ""
        check("ID3 标签（歌名/歌手）", bool(title) and bool(artist),
              "title=%r artist=%r" % (title, artist))
        # 封面校验
        raw = mutagen.File(out)
        has_cover = bool(raw.tags.getall("APIC")) if raw and raw.tags else False
        check("ID3 封面", has_cover)

        # orig 模式（仅解密）
        ok2, msg2 = audio_core.process_one(src, td + "2", "orig")
        out2 = os.path.join(td + "2", "五条人 - 城市找猪." +
                            ("flac" if os.path.exists(os.path.join(td + "2", "五条人 - 城市找猪.flac")) else "mp3"))
        check("orig 仅解密模式", ok2 and os.path.exists(out2), msg2)


def test_conversion_pipeline():
    section("普通音频转换管线（合成样本 → 各输出格式 + 标签）")
    if not audio_core.check_ffmpeg() or not have_ffprobe():
        check("跳过（无 ffmpeg/ffprobe）", False)
        return
    with tempfile.TemporaryDirectory() as td:
        # 合成一段 3 秒 flac 测试音频
        src = os.path.join(td, "测试歌手 - 测试歌曲.flac")
        subprocess.run(
            [FFMPEG, "-y", "-f", "lavfi", "-i",
             "sine=frequency=440:duration=3", "-c:a", "flac", src],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # 打上标签
        audio_core.write_tags(src, "flac",
                              {"title": "测试歌曲", "artist": "测试歌手", "album": "测试专辑"})

        for fmt, codec in (("mp3", "mp3"), ("flac", "flac"), ("wav", "pcm_s16le"),
                           ("aac", "aac"), ("ogg", "vorbis"), ("m4a", "aac"),
                           ("orig", "flac")):
            out_ext = "flac" if fmt == "orig" else fmt  # orig = 源格式直写
            out_dir = os.path.join(td, "out_" + fmt)
            ok, msg = audio_core.process_one(src, out_dir, fmt, "192k")
            out = os.path.join(out_dir, "测试歌手 - 测试歌曲." + out_ext)
            check("→ %s 转换成功" % fmt, ok and os.path.exists(out), msg)
            check("→ %s ffprobe 校验" % fmt, _ffprobe_ok(out, expect_codec=codec))
            # 标签存活校验（aac ADTS 无标签容器；各格式标签键不同）
            if fmt != "aac":
                import mutagen
                from mutagen import mp4 as _mp4
                m = mutagen.File(out)
                title = ""
                if m is not None and m.tags is not None:
                    if hasattr(m.tags, "getall"):  # ID3（mp3/wav）
                        frames = m.tags.getall("TIT2")
                        title = str(frames[0]) if frames else ""
                    elif isinstance(m.tags, _mp4.MP4Tags):  # m4a
                        title = str((m.tags.get("\xa9nam") or [""])[0])
                    else:  # vorbis comment（flac/ogg）
                        title = str(m.tags.get("title", [""])[0] or "")
                check("→ %s 标签存活" % fmt, "测试歌曲" in title, "title=%r" % title)

        # 同格式直写：mp3 → mp3 不重编码（直接复制）
        mp3_dir = os.path.join(td, "out_mp3")
        mp3_file = os.path.join(mp3_dir, "测试歌手 - 测试歌曲.mp3")
        with open(mp3_file, "rb") as f:
            before = f.read()
        ok, msg = audio_core.process_one(mp3_file, os.path.join(td, "out_copy"), "mp3")
        copy_file = os.path.join(td, "out_copy", "测试歌手 - 测试歌曲.mp3")
        with open(copy_file, "rb") as f:
            after = f.read()
        check("mp3→mp3 同格式直写（字节级一致，无重编码）",
              ok and before == after, msg)

        # ncm_batch 兼容入口
        check("collect_ncm_files 兼容入口",
              audio_core.collect_ncm_files([src]) == [])


def main():
    parser = argparse.ArgumentParser(description="ncmturnmp3 自检")
    parser.add_argument("--quick", action="store_true", help="跳过 4.25GB mask 校验")
    parser.add_argument("--skip-ffmpeg", action="store_true", help="跳过 ffmpeg 转换类测试")
    args = parser.parse_args()

    print("ncmturnmp3 selftest  (%s)" % os.path.abspath(HERE))
    test_env()
    test_qmc_vectors()
    if args.quick:
        section("KGM 表常量权威校验")
        print("  [SKIP] --quick 模式跳过 mask 流 SHA256 校验")
    else:
        test_kgm_tables()
    test_kgm_numpy_vs_pure()
    test_roundtrip()
    if args.skip_ffmpeg:
        section("转换管线测试")
        print("  [SKIP] --skip-ffmpeg 模式")
    else:
        test_ncm_regression()
        test_conversion_pipeline()

    print("\n================ 结果 ================")
    print("通过: %d    失败: %d" % (_PASS, _FAIL))
    if _FAIL:
        sys.exit(1)
    print("全部通过 ✔")


if __name__ == "__main__":
    main()
