# ncmturnmp3 —— 加密音乐多格式转换器

把国内主流音乐平台下载的加密音频解密并转换为通用格式，纯本地运行、不联网、
不依赖任何第三方服务。GUI（tkinter）与命令行共用同一套核心逻辑。

## 支持的格式

### 输入（加密格式，自动识别并解密）

| 平台 | 扩展名 | 算法 |
| --- | --- | --- |
| 网易云 | `.ncm` | AES + 改良 RC4（内嵌元数据/封面） |
| QQ 音乐 v1 | `.qmc0` `.qmc2` `.qmc3` `.qmcflac` `.qmcogg` `.qmcra` `.tkm` `.bkcmp3` `.bkcflac` `.bkcwav` `.bkcogg` `.bkcaac` 及十六进制命名缓存 | 静态密码盒 XOR |
| QQ 音乐 v2 | `.mflac` `.mflac0` `.mflac1` `.mgg` `.mgg0` `.mgg1` `.mggl` `.mmp4`（qmcflac/qmcogg 亦可能是 v2，按文件尾自动识别） | 文件尾内嵌 ekey → TEA 派生 → Map/RC4 流密码（含 EncV2 双重 TEA 变体） |
| QQ 音乐缓存 | `.tm0` `.tm2` `.tm3` `.tm6` | 修复 8 字节 ftyp 头 |
| 酷狗 | `.kgm` `.kgma` `.vpr` | v2 纯计算掩码表（内置常量表，无需外置密钥文件） |
| 酷我 | `.kwm` | yeelion 头 + 32 字节 XOR 掩码 |
| 虾米 | `.xm` | ifmt 头 + 字节变换 |
| 咪咕 | `.mg3d` | 密钥自含于文件的 WAV 加法加密 |

### 输入（普通音频，参与格式转换）

`.mp3` `.flac` `.wav` `.m4a` `.aac` `.ogg` `.oga` `.opus` `.wma` `.ape`

### 输出格式

`mp3`（默认，码率可调默认 320k）/ `flac` / `wav` / `aac` / `ogg` / `m4a` /
`orig`（原始格式：仅解密不转码，无损最快）

智能行为：**目标格式与源音频格式相同时直接写出原始字节、不重编码**，
避免二次编码损失音质；码率参数仅对实际转码的有损格式生效。

### 元数据

歌名 / 歌手 / 专辑 / 封面自动保留：优先取加密文件内嵌元数据（ncm），
其次取解密后音频自带标签，最后回退"歌手 - 歌名"文件名解析；按输出格式
写入 ID3（mp3/wav）、VorbisComment+Picture（flac/ogg）、MP4 标签（m4a）。

## 使用

### GUI

双击运行或：

```bash
python main.py
```

支持文件/文件夹多选、拖拽入窗口自动转换、输出目录/格式/码率设置。

### 命令行

```bash
# 批量转换（mp3 320k）
python main.py D:\Music -o D:\Out

# 转成 flac
python ncm_batch.py "歌曲.mflac" -f flac

# 仅解密不转码（无需安装 ffmpeg）
python main.py D:\Music -f orig

# 交互式
python main.py -i
```

参数：`-o` 输出目录｜`-f` 输出格式（mp3/flac/wav/aac/ogg/m4a/orig）｜
`-b` 码率｜`-j` 并发线程数（默认 4）

### 拖拽

把文件/文件夹拖到 `ncm_convert.bat` 上即可（转换完自动打开输出目录）。

## 文件结构

```
main.py          GUI + CLI 入口
ncm_batch.py     CLI 批量入口（兼容旧 bat 调用名）
audio_core.py    转换管线核心（识别/转码/打标/调度）
decryptors.py    各平台解密算法（纯函数、线程安全、numpy 加速）
crypto_tables.py 解密用字节常量表（机器生成，见文件头溯源说明）
ncm_core.py      旧版核心模块的兼容层（已废弃，保留供旧脚本引用）
selftest.py      自检脚本（官方测试向量 + 权威哈希 + 回归测试）
tests/testdata/  QMC 官方测试向量（unlock-music 项目 testdata）
tools/           表提取脚本（从参考源码程序化生成 crypto_tables.py）
ref/             生成 crypto_tables.py 时的参考源码快照（不参与运行）
```

## 依赖

- Python 3.8+（本机验证于 3.14）
- `pycryptodome`、`mutagen`（必需）；`numpy`（强烈推荐，大文件解密提速 1~2 个数量级，
  缺失时自动回退纯 Python 实现）
- ffmpeg 加入 PATH（仅 `orig` 之外的重编码需要；`-f orig` 模式可不装）

```bash
pip install -r requirements.txt
```

## 验证

```bash
python selftest.py            # 全量自检（含 272MB/4.25GB mask 流 SHA256 权威校验）
python selftest.py --quick    # 快速自检
```

自检覆盖（当前 68 项全部通过）：

- QMC 官方测试向量字节级比对（密钥派生 / 三种流密码 / 分段偏移 / 完整解码器）
- KGM 表常量权威校验：按 unlock-music/cli 的 mask 生成管线本地生成
  272MB / 4.25GB mask 流，SHA256 与官方发布值完全一致
- KGM numpy 向量化实现与纯 Python 参考实现逐字节一致（含跨周期大偏移）
- KGM/VPR/KWM/XM/MG3D/TM 构造-解密往返（含纯 Python 回退路径）
- NCM 真实文件回归（ffprobe 时长校验 + ID3 标签/封面校验）
- 普通音频 → 全部输出格式转换 + 标签存活 + 同格式直写字节级一致

## 算法出处与说明

解密算法逐函数对照移植自以下开源项目（MIT License）的公开实现，
字节常量表由 `tools/extract_tables.py` 程化提取（零手工抄写）：

- unlock-music（qmc.ts / qmc_cipher.ts / qmc_key.ts / tea.ts / kwm.ts /
  xm.ts / mg3d.ts / tm.ts / utils.ts）
- @jixun/kugou-crypto（kgm 表与字节解密函数，其结果与 unlock-music/cli
  做过哈希级 1:1 对照）

本工具仅处理用户已合法下载到本地的文件，用于个人备份与格式兼容，
请遵守相关平台用户协议与版权法规，勿将解密结果用于传播。

## 已知限制

- QMCv2 仅支持文件尾内嵌 ekey 的文件（2019 年后 QQ 音乐客户端下载的
  mflac/mgg 普遍内嵌）；无内嵌 ekey 的文件会报错提示。
- QQ 音乐海外版 JOOX `.ofl_en` 需要用户提供 App UUID，未纳入支持。
- 裸 AAC（ADTS）输出无内嵌标签容器（格式本身不支持），选 `m4a` 可保留标签。
