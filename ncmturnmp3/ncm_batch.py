# -*- coding: utf-8 -*-
"""
ncm_batch.py —— 批量转换命令行入口（文件名保留 ncm_batch 以兼容旧 bat/习惯用法）

与 main.py 共用 audio_core.py：
  - 支持 ncm / qmc 全家族 / tm 缓存 / kgm / kgma / vpr / kwm / xm / mg3d / 常见音频输入；
  - 输出格式可选（-f），码率可选（-b），支持并发（-j）；
  - 元数据（歌名/歌手/专辑/封面）自动保留。
本程序完全本地运行，不联网。
"""
import os
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor

# 显式把脚本目录加入 sys.path（兼容 PYTHONSAFEPATH / 任意 CWD 调用方式）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio_core


def main():
    parser = argparse.ArgumentParser(
        description="批量转换加密音乐/音频文件（保留元数据，纯本地运行）"
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="加密音乐/音频文件或包含它们的目录（可传多个，也支持拖拽到 bat）",
    )
    parser.add_argument("-o", "--output", default=None, help="输出目录（默认与源文件同目录）")
    parser.add_argument("-f", "--format", default="mp3", dest="output_format",
                        choices=audio_core.OUTPUT_FORMAT_NAMES,
                        help="输出格式（默认 mp3；orig = 原始格式仅解密不转码）")
    parser.add_argument("-b", "--bitrate", default="320k", help="码率，默认 320k（有损格式生效）")
    parser.add_argument("-j", "--jobs", type=int, default=4, help="并发线程数，默认 4")
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        sys.exit(1)

    if args.output_format != "orig" and not audio_core.check_ffmpeg():
        print("未检测到 ffmpeg：请 pip install imageio-ffmpeg（推荐，免配置）、或安装 ffmpeg 加入 PATH、或设环境变量 NCMTURNMP3_FFMPEG（也可用 -f orig 仅解密）", file=sys.stderr)
        sys.exit(1)

    files = audio_core.collect_files(args.input)
    if not files:
        print("未找到任何可处理的文件")
        sys.exit(0)

    if args.output:
        os.makedirs(args.output, exist_ok=True)

    print(f"找到 {len(files)} 个文件，开始转换"
          f"（输出格式：{args.output_format}，并发 {args.jobs}）...\n")
    success = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for i, (ok, msg) in enumerate(
            ex.map(
                lambda p: audio_core.process_one(p, args.output, args.output_format, args.bitrate),
                files,
            ),
            1,
        ):
            status = "[OK]" if ok else "[FAIL]"
            print(f"[{i}/{len(files)}] {status} {msg}")
            if ok:
                success += 1
            else:
                failed += 1

    print(f"\n转换完成！成功：{success}，失败：{failed}")


if __name__ == "__main__":
    main()
