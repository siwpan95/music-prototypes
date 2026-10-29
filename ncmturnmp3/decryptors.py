# -*- coding: utf-8 -*-
"""
decryptors.py —— 各平台加密音频格式的纯本地解密器集合（含音频格式嗅探）

支持的加密格式（密钥/算法全部内置于本地，无任何运行时联网）：
  - 网易云 .ncm            （AES + 改良 RC4，沿用项目原有实现）
  - QQ 音乐 QMCv1          .qmc0/.qmc2/.qmc3/.qmcflac/.qmcogg/.qmcra/.tkm
                            .bkcmp3/.bkcflac/.bkcwav/.bkcogg/.bkcaac
                            以及十六进制命名缓存 .666c6163/.6d7033/.6f6767/.6d3461/.776176
                            （静态密码盒 XOR）
  - QQ 音乐 QMCv2          .mflac/.mflac0/.mflac1/.mgg/.mgg0/.mgg1/.mggl/.mmp4
                            （文件尾内嵌 ekey，TEA 派生 → Map/RC4 流密码；
                             含 EncV2 双重 TEA 变体；qmcflac/qmcogg 也可能是 v2，
                             统一由文件尾特征自动识别，不依赖扩展名判断版本）
  - QQ 音乐 Tm 缓存        .tm0/.tm2/.tm3/.tm6（修复 8 字节 ftyp 头即得 m4a）
  - 酷狗 .kgm/.kgma/.vpr   （v2 纯计算掩码表算法，表常量见 crypto_tables.py）
  - 酷我 .kwm              （yeelion 头 + 32 字节 XOR 掩码）
  - 虾米 .xm               （ifmt 头 + 字节减法/取反）
  - 咪咕 .mg3d             （密钥自含于文件的 WAV 减法加密）
  - 普通音频               .mp3/.flac/.wav/.m4a/.aac/.ogg/.oga/.opus/.wma/.ape
                            （不解密，仅参与格式转换管线）

算法出处（开源公开实现，逐函数对照移植，字节表由 tools/extract_tables.py
程序化提取，selftest.py 内置官方测试向量与 mask 流 SHA256 双重校验）：
  - QMC: unlock-music (MIT) src/decrypt/qmc.ts / qmc_cipher.ts / qmc_key.ts / utils/tea.ts
  - KGM: jsxiaosi/kugou-crypto (MIT, @jixun/kugou-crypto 镜像) src/utils/*
  - KWM/XM/MG3D/TM: unlock-music (MIT) src/decrypt/kwm.ts / xm.ts / mg3d.ts / tm.ts

线程安全：本模块所有解密入口均为无共享可变状态的纯函数，可多线程并发调用。
"""
import base64
import io
import json
import math
import os
import struct

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Util.strxor import strxor as XOR

from crypto_tables import (
    KGM_TABLE_1,
    KGM_TABLE_2,
    KGM_TABLE_V2,
    KGM_VPR_KEY,
    QMC_STATIC_BOX,
    QMC_MIX_KEY_1,
    QMC_MIX_KEY_2,
)

try:  # numpy 可用则走向量化快路径（大文件快 1~2 个数量级）
    import numpy as _np

    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _np = None
    _HAS_NUMPY = False


# --------------------------------------------------------------------------- #
# 音频格式嗅探（魔数表与 unlock-music/src/decrypt/utils.ts 保持一致）
# --------------------------------------------------------------------------- #
FLAC_MAGIC = b"fLaC"
MP3_ID3_MAGIC = b"ID3"
OGG_MAGIC = b"OggS"
M4A_MAGIC = b"ftyp"
WAV_MAGIC = b"RIFF"
WMA_MAGIC = bytes.fromhex("3026b2758e66cf11a6d900aa0062ce6c")
AAC_MAGIC = b"\xff\xf1"
AAC_MAGIC2 = b"\xff\xf9"
DFF_MAGIC = b"FRM8"

# 各格式"已解密后的标准音频扩展名"
AUDIO_EXTS = ("mp3", "flac", "wav", "m4a", "aac", "ogg", "oga", "opus", "wma", "ape")

# 加密输入扩展名 → 解密器路由（全部小写，不带点）
NCM_EXTS = {"ncm"}
QMC_EXTS = {
    "qmc0", "qmc1", "qmc2", "qmc3", "qmc4", "qmc6", "qmc8",
    "qmcflac", "qmcogg", "qmcra", "tkm",
    "bkcmp3", "bkcflac", "bkcwav", "bkcogg", "bkcaac",
    "mflac", "mflac0", "mflac1", "mgg", "mgg0", "mgg1", "mggl", "mmp4",
    "666c6163", "6d7033", "6f6767", "6d3461", "776176",  # QQ 音乐十六进制命名缓存
}
TM_EXTS = {"tm0", "tm2", "tm3", "tm6"}
KGM_EXTS = {"kgm", "kgma", "vpr"}
KWM_EXTS = {"kwm"}
XM_EXTS = {"xm"}
MG3D_EXTS = {"mg3d"}

ENCRYPTED_EXTS = NCM_EXTS | QMC_EXTS | TM_EXTS | KGM_EXTS | KWM_EXTS | XM_EXTS | MG3D_EXTS
SUPPORTED_INPUT_EXTS = ENCRYPTED_EXTS | set(AUDIO_EXTS)

KGM_FILE_MAGIC = bytes.fromhex("7cd532eb86027f4ba8afa68e0fff9914")  # .kgm/.kgma
VPR_FILE_MAGIC = bytes.fromhex("0528bc96e9e45a4391aabdd07af53631")  # .vpr
KWM_FILE_MAGIC = b"yeelion-kuwo-tme"
KWM_FILE_MAGIC2 = b"yeelion-kuwo-\x00\x00\x00\x00"
XM_FILE_MAGIC = b"ifmt"
NCM_FILE_MAGIC = b"CTENFDAM"
TM_FIXED_HEADER = bytes.fromhex("0000002066747970")  # 00 00 00 20 "ftyp"


def sniff_audio_ext(data, fallback="mp3"):
    """根据文件头魔数判断已解密音频的实际格式。"""
    if not data:
        return fallback
    if data[:3] == MP3_ID3_MAGIC:
        return "mp3"
    if data[:4] == FLAC_MAGIC:
        return "flac"
    if data[:4] == OGG_MAGIC:
        return "ogg"  # ogg/oga/opus 统一按 ogg 容器处理
    if len(data) >= 8 and data[4:8] == M4A_MAGIC:
        return "m4a"
    if data[:4] == WAV_MAGIC:
        return "wav"
    if data[:16] == WMA_MAGIC:
        return "wma"
    if data[:2] in (AAC_MAGIC, AAC_MAGIC2):
        return "aac"
    if data[:4] == DFF_MAGIC:
        return "dff"
    # 裸 MPEG 帧同步（无 ID3 头的 mp3）：11111111 111xxxxx
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "mp3"
    return fallback


def looks_like_plain_audio(data):
    """判断字节流是否已是标准音频（用于未知扩展名文件的兜底识别）。"""
    return sniff_audio_ext(data, fallback=None) is not None


# --------------------------------------------------------------------------- #
# 1. 网易云 NCM（沿用项目原有实现：AES + 改良 RC4，元数据与封面内嵌）
# --------------------------------------------------------------------------- #
def decrypt_ncm(ncm_path):
    """
    解密 ncm 文件，返回 dict(format/metadata/audio/cover)。
    与原 ncm_core.decrypt_ncm 完全一致（该实现已长期验证）。
    """
    core_key = bytes.fromhex("687a4852416d736f356b496e62617857")
    meta_key = bytes.fromhex("2331346c6a6b5f215c5d2630553c2728")

    with open(ncm_path, "rb") as f:
        header = f.read(8)
        if header != NCM_FILE_MAGIC:
            raise ValueError("不是有效的 NCM 文件：" + ncm_path)

        f.seek(2, 1)  # 跳过 2 字节未知

        # --- 解密 RC4 key ---
        key_length = struct.unpack("<I", f.read(4))[0]
        key_data = bytearray(f.read(key_length))
        key_data = bytes(bytearray([b ^ 0x64 for b in key_data]))
        cryptor = AES.new(core_key, AES.MODE_ECB)
        key_data = unpad(cryptor.decrypt(key_data), 16)[17:]
        key_length = len(key_data)

        # RC4 S-box 初始化
        key = bytearray(key_data)
        S = bytearray(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % key_length]) & 0xFF
            S[i], S[j] = S[j], S[i]

        # --- 解密 metadata ---
        meta_length = struct.unpack("<I", f.read(4))[0]
        if meta_length:
            meta_data = bytearray(f.read(meta_length))
            meta_data = bytes(bytearray([b ^ 0x63 for b in meta_data]))
            meta_data = base64.b64decode(meta_data[22:])
            cryptor = AES.new(meta_key, AES.MODE_ECB)
            meta_data = unpad(cryptor.decrypt(meta_data), 16).decode("utf-8")
            idx = meta_data.find(":")
            meta_data = json.loads(meta_data[idx + 1:])
        else:
            # 无元数据：根据文件大小猜测格式（ncmdump 的兜底逻辑）
            meta_data = {
                "format": "flac" if os.fstat(f.fileno()).st_size > 1024 ** 2 * 16 else "mp3"
            }

        f.seek(5, 1)  # 跳过 9 字节未知（crc32 + gap）

        # --- 读取内嵌封面 ---
        image_space = struct.unpack("<I", f.read(4))[0]
        image_size = struct.unpack("<I", f.read(4))[0]
        cover = f.read(image_size) if image_size else None
        f.seek(image_space - image_size, 1)

        # --- 读取加密音频数据 ---
        data = f.read()

    # 改良 RC4 流解密
    stream = [S[(S[i] + S[(i + S[i]) & 0xFF]) & 0xFF] for i in range(256)]
    stream = bytes(bytearray(stream * (len(data) // 256 + 1))[1: 1 + len(data)])
    audio = XOR(data, stream)

    fmt = meta_data.get("format", "mp3")
    if fmt not in AUDIO_EXTS:
        fmt = sniff_audio_ext(audio, fallback="mp3")
    return {"format": fmt, "metadata": meta_data, "audio": audio, "cover": cover}


# --------------------------------------------------------------------------- #
# 2. Tencent TEA（QMCv2 ekey 派生用），对照 unlock-music src/utils/tea.ts
# --------------------------------------------------------------------------- #
_TEA_DELTA = 0x9E3779B9
_M32 = 0xFFFFFFFF


class TeaCipher:
    """TEA 分组密码（32 轮）。与 unlock-music 的 TypeScript 实现（Go 移植）逐位一致。"""

    def __init__(self, key, rounds=64):
        if len(key) != 16:
            raise ValueError("TEA key 必须为 16 字节")
        if rounds & 1:
            raise ValueError("TEA 轮数必须为偶数")
        (self.k0, self.k1, self.k2, self.k3) = struct.unpack(">4I", key)
        self.rounds = rounds

    def decrypt_block(self, block):
        """解密单个 8 字节块，返回 8 字节。"""
        v0, v1 = struct.unpack(">2I", block)
        sum_ = (_TEA_DELTA * (self.rounds // 2)) & _M32
        for _ in range(self.rounds // 2):
            v1 = (v1 - ((((v0 << 4) & _M32) + self.k2) & _M32 ^ (v0 + sum_) & _M32
                        ^ (((v0 >> 5) & _M32) + self.k3) & _M32)) & _M32
            v0 = (v0 - ((((v1 << 4) & _M32) + self.k0) & _M32 ^ (v1 + sum_) & _M32
                        ^ (((v1 >> 5) & _M32) + self.k1) & _M32)) & _M32
            sum_ = (sum_ - _TEA_DELTA) & _M32
        return struct.pack(">2I", v0, v1)


def decrypt_tencent_tea(in_buf, key):
    """
    QQ 变体 TEA CBC 解密（带 PadLen/Salt/Zero 结构）。
    对照 unlock-music src/decrypt/qmc_key.ts::decryptTencentTea。
    """
    if len(in_buf) % 8 != 0:
        raise ValueError("TEA 输入长度不是 8 的倍数")
    if len(in_buf) < 16:
        raise ValueError("TEA 输入过短")

    blk = TeaCipher(key, 32)
    tmp = bytearray(blk.decrypt_block(in_buf[:8]))
    n_pad_len = tmp[0] & 0x07
    out_len = len(in_buf) - 1 - n_pad_len - 2 - 7
    if out_len < 0:
        raise ValueError("TEA 输出长度异常")
    out_buf = bytearray(out_len)

    iv_prev = bytes(8)
    iv_cur = in_buf[:8]
    in_pos = 8
    tmp_idx = 1 + n_pad_len

    def crypt_block():
        nonlocal iv_prev, iv_cur, in_pos, tmp_idx
        iv_prev = iv_cur
        iv_cur = in_buf[in_pos:in_pos + 8]
        for j in range(8):
            tmp[j] ^= iv_cur[j]
        tmp[:] = blk.decrypt_block(bytes(tmp))
        in_pos += 8
        tmp_idx = 0

    # 跳过 Salt（2 字节）
    i = 1
    while i <= 2:
        if tmp_idx < 8:
            tmp_idx += 1
            i += 1
        else:
            crypt_block()

    # 还原明文
    out_pos = 0
    while out_pos < out_len:
        if tmp_idx < 8:
            out_buf[out_pos] = tmp[tmp_idx] ^ iv_prev[tmp_idx]
            out_pos += 1
            tmp_idx += 1
        else:
            crypt_block()

    # 校验 Zero（与参考实现一致：仅校验当前位置）
    if tmp_idx < 8 and tmp[tmp_idx] != iv_prev[tmp_idx]:
        raise ValueError("TEA zero 校验失败（密钥错误）")
    return bytes(out_buf)


def simple_make_key(salt, length):
    """simpleMakeKey：QMCv2 ekey 派生用（tan 序列）。"""
    return bytes(0xFF & int(abs(math.tan(salt + i * 0.1)) * 100.0) for i in range(length))


def _decrypt_v2_key(key):
    """EncV2 变体：前缀 QQMusic EncV2,Key: → 双重 TEA + base64。"""
    if len(key) < 18 or key[:18] != b"QQMusic EncV2,Key:":
        return key
    out = decrypt_tencent_tea(key[18:], QMC_MIX_KEY_1)
    out = decrypt_tencent_tea(out, QMC_MIX_KEY_2)
    out = base64.b64decode(out)
    if len(out) < 16:
        raise ValueError("EncV2 密钥解码失败")
    return out


def qmc_derive_key(raw_key):
    """
    QMCv2 文件尾 ekey（base64 文本）→ 中间密钥。
    短密钥（≤300 字节）配 MapCipher，长密钥（>300）配 RC4Cipher。
    对照 unlock-music src/decrypt/qmc_key.ts::QmcDeriveKey。
    """
    raw_dec = base64.b64decode(raw_key)
    if len(raw_dec) < 16:
        raise ValueError("ekey 解码后过短")

    raw_dec = _decrypt_v2_key(raw_dec)

    simple_key = simple_make_key(106, 8)
    tea_key = bytearray(16)
    for i in range(8):
        tea_key[i << 1] = simple_key[i]
        tea_key[(i << 1) + 1] = raw_dec[i]
    sub = decrypt_tencent_tea(raw_dec[8:], bytes(tea_key))
    return raw_dec[:8] + sub


# --------------------------------------------------------------------------- #
# 3. QMC 流密码（Static / Map / RC4），对照 unlock-music src/decrypt/qmc_cipher.ts
# --------------------------------------------------------------------------- #
class QmcStaticCipher:
    """QMCv1 静态密码盒（qmc0/qmc3/tkm/bkcmp3 及无尾密钥的旧文件）。"""

    def decrypt(self, buf, offset=0):
        """就地解密 bytearray/memoryview[start:end] 区域。"""
        n = len(buf)
        if n == 0:
            return
        if _HAS_NUMPY:
            offs = _np.arange(offset, offset + n, dtype=_np.int64)
            offs = _np.where(offs > 0x7FFF, offs % 0x7FFF, offs)
            mask = _np.frombuffer(QMC_STATIC_BOX, dtype=_np.uint8)[
                (offs * offs + 27) & 0xFF
            ]
            arr = _np.frombuffer(buf, dtype=_np.uint8)
            arr ^= mask
        else:  # 纯 Python 回退
            for i in range(n):
                o = offset + i
                if o > 0x7FFF:
                    o %= 0x7FFF
                buf[i] ^= QMC_STATIC_BOX[(o * o + 27) & 0xFF]


class QmcMapCipher:
    """QMCv2 Map 流密码（短密钥）。"""

    def __init__(self, key):
        if not key:
            raise ValueError("QmcMapCipher: 密钥为空")
        self.key = bytes(key)
        self.n = len(self.key)

    @staticmethod
    def _rotate(value, bits):
        r = (bits + 4) % 8
        return ((value << r) | (value >> r)) & 0xFF

    def _mask_at(self, offset):
        if offset > 0x7FFF:
            offset %= 0x7FFF
        idx = (offset * offset + 71214) % self.n
        return self._rotate(self.key[idx], idx & 0x7)

    def decrypt(self, buf, offset=0):
        n = len(buf)
        if n == 0:
            return
        if _HAS_NUMPY:
            offs = _np.arange(offset, offset + n, dtype=_np.int64)
            offs = _np.where(offs > 0x7FFF, offs % 0x7FFF, offs)
            idx = (offs * offs + 71214) % self.n
            key_np = _np.frombuffer(self.key, dtype=_np.uint8)
            kv = key_np[idx % self.n]
            r = ((idx & 0x7) + 4) % 8
            rotated = ((_np.left_shift(kv, r) & 0xFF) | (_np.right_shift(kv, r))).astype(_np.uint8)
            arr = _np.frombuffer(buf, dtype=_np.uint8)
            arr ^= rotated
        else:
            for i in range(n):
                buf[i] ^= self._mask_at(offset + i)


class QmcRC4Cipher:
    """QMCv2 RC4 变体流密码（长密钥 >300 字节），分 5120 字节段处理。"""

    FIRST_SEGMENT_SIZE = 0x80
    SEGMENT_SIZE = 5120

    def __init__(self, key):
        if not key:
            raise ValueError("QmcRC4Cipher: 密钥为空")
        self.key = bytes(key)
        self.N = len(self.key)

        # 初始化种子盒（注意：S 盒长度为 N，值在 256 内循环）
        self.S = [i & 0xFF for i in range(self.N)]
        j = 0
        for i in range(self.N):
            j = (self.S[i] + j + self.key[i % self.N]) % self.N
            self.S[i], self.S[j] = self.S[j], self.S[i]

        # 初始化 hash 基数（单调递增乘积，uint32）
        self.hash = 1
        for i in range(self.N):
            value = self.key[i]
            if value == 0:
                continue
            next_hash = (self.hash * value) & _M32
            if next_hash == 0 or next_hash <= self.hash:
                break
            self.hash = next_hash

    def _segment_key(self, seg_id):
        """段密钥索引；seed==0 时参考实现表现为"不改字节"，返回 None。"""
        seed = self.key[seg_id % self.N]
        if seed == 0:
            return None
        idx = int((self.hash / ((seg_id + 1) * seed)) * 100.0)
        return idx % self.N

    def decrypt(self, buf, offset=0):
        """就地解密（buf 为 bytearray，支持任意起始 offset，跨段正确）。"""
        to_process = len(buf)
        processed = 0

        def post(len_seg):
            nonlocal to_process, processed, offset
            to_process -= len_seg
            processed += len_seg
            offset += len_seg
            return to_process == 0

        # 首段（< 0x80）
        if offset < self.FIRST_SEGMENT_SIZE:
            len_seg = min(len(buf), self.FIRST_SEGMENT_SIZE - offset)
            self._enc_first_segment(buf, processed, processed + len_seg, offset)
            if post(len_seg):
                return

        # 对齐段
        if offset % self.SEGMENT_SIZE != 0:
            len_seg = min(self.SEGMENT_SIZE - (offset % self.SEGMENT_SIZE), to_process)
            self._enc_segment(buf, processed, processed + len_seg, offset)
            if post(len_seg):
                return

        # 整段批量
        while to_process > self.SEGMENT_SIZE:
            self._enc_segment(buf, processed, processed + self.SEGMENT_SIZE, offset)
            post(self.SEGMENT_SIZE)

        # 末尾不满一段
        if to_process > 0:
            self._enc_segment(buf, processed, len(buf), offset)

    def _enc_first_segment(self, buf, lo, hi, offset):
        for i in range(lo, hi):
            seg_idx = self._segment_key(offset + (i - lo))
            if seg_idx is not None:
                buf[i] ^= self.key[seg_idx]

    def _enc_segment(self, buf, lo, hi, offset):
        S = self.S[:]  # 每段从主 S 盒拷贝重启
        N = self.N
        seg_key_idx = self._segment_key(offset // self.SEGMENT_SIZE)
        if seg_key_idx is None:
            # seed==0 → skipLen 退化为仅 offset 对齐部分（参考实现中该值不可用，
            # 实际密钥不会出现此情形，保守按 0 处理）
            skip_base = 0
        else:
            skip_base = seg_key_idx
        skip_len = (offset % self.SEGMENT_SIZE) + skip_base

        j = 0
        k = 0
        for i in range(-skip_len, hi - lo):
            j = (j + 1) % N
            k = (S[j] + k) % N
            S[k], S[j] = S[j], S[k]
            if i >= 0:
                buf[lo + i] ^= S[(S[j] + S[k]) % N]


# --------------------------------------------------------------------------- #
# 4. QMC 文件级解码（含文件尾 ekey 识别），对照 unlock-music src/decrypt/qmc.ts
# --------------------------------------------------------------------------- #
def decrypt_qmc(file_bytes, ext_hint=None):
    """
    解密 QMC 家族文件（v1/v2 由文件尾特征自动识别）。
    返回 dict(format/audio/song_id)。format 由解密结果魔数嗅探得出。
    """
    size = len(file_bytes)
    if size < 8:
        raise ValueError("QMC 文件过小")

    last4 = file_bytes[-4:]
    audio_size = size
    cipher = None
    song_id = None

    if last4 == b"QTag":
        # 旧版：末尾 8 字节 = QTag + 4 字节 BE key 长度，密钥与歌曲 ID 以逗号分隔明文存放
        key_size = struct.unpack(">I", file_bytes[-8:-4])[0]
        if key_size > size - 8:
            raise ValueError("QMC QTag 尾部长度异常")
        audio_size = size - key_size - 8
        raw_key = file_bytes[audio_size:size - 8]
        comma = raw_key.find(b",")
        if comma < 0:
            raise ValueError("QMC QTag 密钥格式异常")
        key_raw = raw_key[:comma]
        id_part = raw_key[comma + 1:]
        comma2 = id_part.find(b",")
        if comma2 >= 0:
            try:
                song_id = int(id_part[:comma2])
            except ValueError:
                song_id = None
        key_dec = qmc_derive_key(key_raw)
        cipher = QmcRC4Cipher(key_dec) if len(key_dec) > 300 else QmcMapCipher(key_dec)
    else:
        key_size = struct.unpack("<I", last4)[0]
        if 0 < key_size < 0x400:
            # QMCv2：末尾 4 字节 LE 长度 + base64 ekey
            audio_size = size - key_size - 4
            if audio_size <= 0:
                raise ValueError("QMC v2 尾部 ekey 长度异常")
            raw_key = file_bytes[audio_size:size - 4]
            key_dec = qmc_derive_key(raw_key)
            cipher = QmcRC4Cipher(key_dec) if len(key_dec) > 300 else QmcMapCipher(key_dec)
        else:
            # QMCv1 静态密码盒
            cipher = QmcStaticCipher()

    audio = bytearray(file_bytes[:audio_size])
    cipher.decrypt(audio, 0)

    fallback = {"qmcflac": "flac", "qmcogg": "ogg", "mflac": "flac", "mgg": "ogg",
                "tkm": "m4a", "bkcmp3": "mp3", "bkcflac": "flac"}.get(ext_hint or "", "mp3")
    fmt = sniff_audio_ext(bytes(audio[:64]), fallback=fallback)
    return {"format": fmt, "audio": bytes(audio), "song_id": song_id}


# --------------------------------------------------------------------------- #
# 5. 酷狗 KGM/KGMA/VPR（v2 纯计算掩码），对照 kugou-crypto src/utils/*
# --------------------------------------------------------------------------- #
def _kgm_mask_byte_at_offset(offset):
    """getMaskByteAtOffset：按偏移高低半字节逐级查表异或。"""
    value = 0
    o = offset
    while o >= 0x11:
        value ^= KGM_TABLE_1[o % 272]
        o >>= 4
        value ^= KGM_TABLE_2[o % 272]
        o >>= 4
    return value


def _kgm_mask_v2_at_offset(offset):
    """getMaskByteAtOffsetV2 = tableV2[o % 272] ^ getMaskByteAtOffset(o >> 4)。"""
    return KGM_TABLE_V2[offset % 272] ^ _kgm_mask_byte_at_offset(offset >> 4)


def _xor_lower_half_byte(x):
    return x ^ ((x & 0x0F) << 4)


def decrypt_kgm_byte_v2(enc_byte, file_key17, offset):
    """单个 KGM 音频字节解密（纯 Python 参考实现）。"""
    x = _kgm_mask_v2_at_offset(offset) ^ enc_byte ^ file_key17[offset % 17]
    return _xor_lower_half_byte(x)


def decrypt_vpr_byte(enc_byte, file_key17, offset):
    """单个 VPR 音频字节解密 = KGM 解密后再异或 vprKey。"""
    return decrypt_kgm_byte_v2(enc_byte, file_key17, offset) ^ KGM_VPR_KEY[offset % 17]


def _kgm_mask_v2_numpy(offsets):
    """numpy 向量化版本的 mask 计算（与纯 Python 版逐位一致，selftest 有对照测试）。"""
    o = offsets.astype(_np.int64)
    mask = _np.frombuffer(KGM_TABLE_V2, dtype=_np.uint8)[o % 272].astype(_np.int64)
    x = o >> 4
    k = 0
    while True:
        shift = 4 + 8 * k
        x = o >> shift
        if not (x >= 0x11).any():
            break
        t1 = _np.frombuffer(KGM_TABLE_1, dtype=_np.uint8)[x % 272].astype(_np.int64)
        t2 = _np.frombuffer(KGM_TABLE_2, dtype=_np.uint8)[(o >> (shift + 4)) % 272].astype(_np.int64)
        term = t1 ^ t2
        mask = mask ^ _np.where(x >= 0x11, term, 0)
        k += 1
        if shift > 64:  # 安全阀
            break
    return mask.astype(_np.uint8)


def decrypt_kgm(file_bytes, ext_hint=None):
    """
    解密酷狗 KGM/KGMA/VPR 文件。
    返回 dict(format/audio)。KGM 与 VPR 由文件头魔数区分（与扩展名无关）。
    """
    if file_bytes[:16] == VPR_FILE_MAGIC:
        is_vpr = True
    elif file_bytes[:16] == KGM_FILE_MAGIC:
        is_vpr = False
    else:
        raise ValueError("不是有效的 KGM/VPR 文件（魔数不符）")

    if len(file_bytes) < 0x30:
        raise ValueError("KGM 文件过小")

    header_len = struct.unpack("<I", file_bytes[0x10:0x14])[0]
    if header_len < 0x2C or header_len > len(file_bytes):
        raise ValueError("KGM 文件头长度异常: %d" % header_len)

    file_key17 = bytes(file_bytes[0x1C:0x2C]) + b"\x00"  # 16 字节文件私钥 + 0
    audio = file_bytes[header_len:]
    n = len(audio)

    if n == 0:
        raise ValueError("KGM 文件无音频数据")

    if _HAS_NUMPY:
        offs = _np.arange(n, dtype=_np.int64)
        mask = _kgm_mask_v2_numpy(offs)
        key_arr = _np.frombuffer(file_key17, dtype=_np.uint8)[offs % 17]
        v = mask ^ _np.frombuffer(audio, dtype=_np.uint8) ^ key_arr
        out = (v ^ (_np.left_shift(v & 0x0F, 4))).astype(_np.uint8)
        if is_vpr:
            out = out ^ _np.frombuffer(KGM_VPR_KEY, dtype=_np.uint8)[offs % 17]
        audio_out = out.tobytes()
    else:  # 纯 Python 回退（慢，但逻辑与参考实现完全一致）
        dec = decrypt_vpr_byte if is_vpr else decrypt_kgm_byte_v2
        audio_out = bytes(dec(audio[i], file_key17, i) for i in range(n))

    fmt = sniff_audio_ext(audio_out[:64], fallback="mp3")
    return {"format": fmt, "audio": audio_out}


# --------------------------------------------------------------------------- #
# 6. 酷我 KWM，对照 unlock-music src/decrypt/kwm.ts
# --------------------------------------------------------------------------- #
_KWM_PREDEFINED_KEY = b"MoOtOiTvINGwd2E6n0E1i7L5t2IoOoNk"


def _kwm_make_mask(file_key8):
    """由 8 字节文件密钥生成 32 字节 XOR 掩码。"""
    key_str = str(int.from_bytes(file_key8, "little"))
    if len(key_str) > 32:
        key_str = key_str[:32]
    elif len(key_str) < 32:
        key_str = (key_str * (32 // len(key_str) + 1))[:32]
    return bytes(_KWM_PREDEFINED_KEY[i] ^ ord(key_str[i]) for i in range(32))


def decrypt_kwm(file_bytes, ext_hint=None):
    """解密酷我 KWM 文件，返回 dict(format/audio)。"""
    if file_bytes[:16] != KWM_FILE_MAGIC and file_bytes[:16] != KWM_FILE_MAGIC2:
        # 新版部分文件可能直接就是 aac 明文（参考实现的兜底）
        if sniff_audio_ext(file_bytes[:64]) == "aac":
            return {"format": "aac", "audio": bytes(file_bytes)}
        raise ValueError("不是有效的 KWM 文件（魔数不符）")
    if len(file_bytes) < 0x400 + 8:
        raise ValueError("KWM 文件过小")

    file_key8 = file_bytes[0x18:0x20]
    mask = _kwm_make_mask(file_key8)
    audio = file_bytes[0x400:]

    if _HAS_NUMPY:
        mask_np = _np.frombuffer(mask, dtype=_np.uint8)
        offs = _np.arange(len(audio), dtype=_np.int64) % 32
        out = (_np.frombuffer(audio, dtype=_np.uint8) ^ mask_np[offs]).tobytes()
    else:
        out = bytes(audio[i] ^ mask[i % 32] for i in range(len(audio)))

    fmt = sniff_audio_ext(out[:64], fallback="mp3")
    return {"format": fmt, "audio": out}


# --------------------------------------------------------------------------- #
# 7. 虾米 XM，对照 unlock-music src/decrypt/xm.ts
# --------------------------------------------------------------------------- #
_XM_TYPE_MAP = {b" WAV": "wav", b"FLAC": "flac", b" MP3": "mp3", b" A4M": "m4a"}


def decrypt_xm(file_bytes, ext_hint=None):
    """解密虾米 XM 文件，返回 dict(format/audio)。"""
    if file_bytes[:4] != XM_FILE_MAGIC or file_bytes[8:12] != b"\xfe\xfe\xfe\xfe":
        raise ValueError("不是有效的 XM 文件（魔数不符）")
    if len(file_bytes) < 0x10:
        raise ValueError("XM 文件过小")

    type_text = file_bytes[4:8]
    if type_text not in _XM_TYPE_MAP:
        raise ValueError("未知的 XM 文件类型: %r" % type_text)
    fmt = _XM_TYPE_MAP[type_text]

    key = file_bytes[0x0F]
    data_offset = file_bytes[0x0C] | (file_bytes[0x0D] << 8) | (file_bytes[0x0E] << 16)
    audio = bytearray(file_bytes[0x10:])
    if data_offset > len(audio):
        data_offset = len(audio)

    if _HAS_NUMPY:
        arr = _np.frombuffer(audio, dtype=_np.uint8)
        dec = ((_np.int16(arr[data_offset:]) - key) & 0xFF) ^ 0xFF
        arr[data_offset:] = dec.astype(_np.uint8)
        out = bytes(arr)
    else:
        for cur in range(data_offset, len(audio)):
            audio[cur] = ((audio[cur] - key) & 0xFF) ^ 0xFF
        out = bytes(audio)

    return {"format": fmt, "audio": out}


# --------------------------------------------------------------------------- #
# 8. 咪咕 MG3D，对照 unlock-music src/decrypt/mg3d.ts（密钥自含于文件）
# --------------------------------------------------------------------------- #
def _is_upper_hex(b):
    return (0x30 <= b <= 0x39) or (0x41 <= b <= 0x46)


def _is_printable_ascii(b):
    return 0x20 <= b <= 0x7E


def decrypt_mg3d(file_bytes, ext_hint=None):
    """解密咪咕 MG3D 文件（WAV 减法加密，密钥为文件内 0x20 对齐的大写十六进制段）。"""
    if len(file_bytes) < 0x40:
        raise ValueError("MG3D 文件过小")

    def decrypt_segment(data):
        return bytes((data[i] - key[i % 0x20]) & 0xFF for i in range(len(data)))

    header = file_bytes[:0x100]
    found_key = None
    for seg in range(0x20, 0x20 * 20, 0x20):
        candidate = file_bytes[seg:seg + 0x20]
        if len(candidate) < 0x20 or not all(_is_upper_hex(b) for b in candidate):
            continue
        key = candidate
        temp = decrypt_segment(header)
        if temp[:4] != b"RIFF" or temp[8:16] != b"WAVEfmt ":
            continue
        fmt_chunk_size = struct.unpack("<I", temp[0x10:0x14])[0]
        if fmt_chunk_size not in (16, 18, 40):
            continue
        first_chunk_off = 0x14 + fmt_chunk_size
        if first_chunk_off + 4 > len(temp):
            continue
        if not all(_is_printable_ascii(b) for b in temp[first_chunk_off:first_chunk_off + 4]):
            continue
        found_key = candidate
        break

    if found_key is None:
        raise ValueError("MG3D 文件中未找到有效密钥段")

    key = found_key
    audio = bytes((file_bytes[i] - key[i % 0x20]) & 0xFF for i in range(len(file_bytes)))
    return {"format": "wav", "audio": audio}


# --------------------------------------------------------------------------- #
# 9. QQ 音乐 Tm 缓存（tm0/tm2/tm3/tm6），对照 unlock-music src/decrypt/tm.ts
# --------------------------------------------------------------------------- #
def decrypt_tm(file_bytes, ext_hint=None):
    """Tm 缓存文件：仅头部 8 字节被改写，修复后即为标准 m4a。"""
    if len(file_bytes) < 16:
        raise ValueError("Tm 文件过小")
    audio = TM_FIXED_HEADER + file_bytes[8:]
    return {"format": "m4a", "audio": audio}


# --------------------------------------------------------------------------- #
# 10. 统一入口：按扩展名/魔数路由
# --------------------------------------------------------------------------- #
def decrypt_file(path, ext=None):
    """
    解密单个加密音乐文件，返回 dict(format/audio/metadata/cover)。
      - format : 解密后音频的标准扩展名（魔数嗅探）
      - audio  : 解密后的音频字节
      - metadata/cover : 仅 ncm 有内嵌元数据，其余格式由上层用 mutagen 从解密
        结果中读取（此函数不读标签，保证纯字节操作、可并发）。
    """
    ext = (ext or os.path.splitext(path)[1].lstrip(".")).lower()
    with open(path, "rb") as f:
        data = f.read()

    if ext in NCM_EXTS or data[:8] == NCM_FILE_MAGIC:
        return decrypt_ncm(path)  # ncm 需要原路径（内部按结构解析）

    if ext in QMC_EXTS:
        return decrypt_qmc(data, ext_hint=ext)

    if ext in KGM_EXTS or data[:16] in (KGM_FILE_MAGIC, VPR_FILE_MAGIC):
        return decrypt_kgm(data, ext_hint=ext)

    if ext in KWM_EXTS or data[:16] in (KWM_FILE_MAGIC, KWM_FILE_MAGIC2):
        return decrypt_kwm(data)

    if ext in XM_EXTS or data[:4] == XM_FILE_MAGIC:
        return decrypt_xm(data)

    if ext in MG3D_EXTS:
        return decrypt_mg3d(data)

    if ext in TM_EXTS:
        return decrypt_tm(data)

    raise ValueError("不支持的加密格式: .%s" % ext)


def decrypt_plain(path):
    """普通音频文件：原样读入（不解密），返回与 decrypt_file 同构的结果。"""
    with open(path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    fmt = sniff_audio_ext(data, fallback=ext if ext in AUDIO_EXTS else "mp3")
    return {"format": fmt, "audio": data, "metadata": None, "cover": None}
