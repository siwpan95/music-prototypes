# -*- coding: utf-8 -*-
"""
main.py —— 加密音乐转换器（图形界面 + 命令行）

功能（基于联网调研主流音乐平台加密格式生态后全面拓展）：
  输入：ncm / qmc 全家族(qmc0/qmc3/qmcflac/mflac/mgg... v1+v2 自动识别) /
        tm 缓存 / kgm / kgma / vpr / kwm / xm / mg3d / 普通音频
        (mp3/flac/wav/m4a/aac/ogg/oga/opus/wma/ape)
  输出：mp3(默认) / flac / wav / aac / ogg / m4a / 原始格式（仅解密不转码）
        码率可调（默认 320k，仅对有损转码生效；同格式自动直写不重编码）
  标签：歌名/歌手/专辑/封面 自动保留或补全

核心逻辑见 audio_core.py + decryptors.py（GUI 与命令行共用）。
本程序完全本地运行，不联网。
"""
import os
import sys
import ctypes
import argparse
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# 显式把脚本目录加入 sys.path（兼容 PYTHONSAFEPATH / 任意 CWD 调用方式）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio_core


class WindowsFileDropper:
    """Windows 下用 WM_DROPFILES 给 tk 窗口加拖拽（无第三方依赖）。

    通过 ctypes 子类化根窗口的窗口过程，拦截 WM_DROPFILES 消息，
    用 DragQueryFile/DragFinish 取回被拖入的文件/文件夹路径列表后回调。
    仅转发未处理的消息给原窗口过程，避免破坏 tk 事件循环。
    """

    WM_DROPFILES = 0x0233
    WM_DESTROY = 0x0002
    GWL_WNDPROC = -4

    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.hwnd = root.winfo_id()

        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32

        # 明确设置原型，避免 64 位下返回值被截断成 32 位导致崩溃
        SetWindowLongPtrW = user32.SetWindowLongPtrW
        SetWindowLongPtrW.restype = ctypes.c_void_p
        SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        CallWindowProcW = user32.CallWindowProcW
        CallWindowProcW.restype = ctypes.c_long
        CallWindowProcW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_long,
        ]
        DragQueryFileW = shell32.DragQueryFileW
        DragQueryFileW.restype = ctypes.c_uint
        DragQueryFileW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_long
        )

        def wndproc(hwnd, msg, wparam, lparam):
            try:
                if msg == self.WM_DROPFILES:
                    self._on_drop(wparam)
                    return 0
                if msg == self.WM_DESTROY:
                    # 窗口销毁时还原原子类化，避免后续消息打到已失效的回调
                    self._restore_wndproc()
                return CallWindowProcW(self._old_wndproc, hwnd, msg, wparam, lparam)
            except OSError:
                # 销毁阶段 tk 内部窗口过程可能已释放；吞掉以免产生回调噪音
                return 0

        self._wndproc = WNDPROC(wndproc)
        shell32.DragAcceptFiles(self.hwnd, True)
        self._old_wndproc = SetWindowLongPtrW(self.hwnd, self.GWL_WNDPROC, self._wndproc)

    def _restore_wndproc(self):
        if getattr(self, "_old_wndproc", None) is None:
            return
        try:
            user32 = ctypes.windll.user32
            user32.SetWindowLongPtrW.restype = ctypes.c_void_p
            user32.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            user32.SetWindowLongPtrW(self.hwnd, self.GWL_WNDPROC, self._old_wndproc)
            self._old_wndproc = None
        except Exception:
            pass

    def _on_drop(self, hdrop):
        shell32 = ctypes.windll.shell32
        count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
        paths = []
        for i in range(count):
            length = shell32.DragQueryFileW(hdrop, i, None, 0)
            buf = ctypes.create_unicode_buffer(length + 1)
            shell32.DragQueryFileW(hdrop, i, buf, length + 1)
            paths.append(buf.value)
        shell32.DragFinish(hdrop)
        if paths:
            self.callback(paths)


class ConverterApp:
    def __init__(self, root):
        self.root = root
        root.title("加密音乐转换器（NCM/QMC/KGM/KWM/XM → MP3/FLAC/... 含元数据）")
        root.geometry("700x560")
        root.resizable(False, False)

        # 检查 ffmpeg（仅重编码/格式转换需要；仅解密模式不需要）
        self.ffmpeg_ok = audio_core.check_ffmpeg()

        # 输入选择（支持多选文件 / 文件夹，可手动增删、手填粘贴）
        tk.Label(root, text="选择文件或文件夹（可多次添加）：", anchor="w").pack(
            fill=tk.X, padx=10, pady=(10, 0))
        list_frame = tk.Frame(root)
        list_frame.pack(fill=tk.X, padx=10, pady=5)
        self.input_listbox = tk.Listbox(list_frame, height=4, selectmode=tk.EXTENDED)
        self.input_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.input_listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_listbox.config(yscrollcommand=scroll.set)
        self.input_paths = []  # 已选输入路径（文件或文件夹）

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
        tk.Button(btn_frame, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="清空", command=self.clear_inputs).pack(side=tk.LEFT, padx=2)

        # 直接手填 / 粘贴路径后添加
        paste_frame = tk.Frame(root)
        paste_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
        self.path_var = tk.StringVar()
        tk.Entry(paste_frame, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(paste_frame, text="添加此路径", command=self.add_manual_path).pack(side=tk.LEFT, padx=2)
        tk.Label(
            root,
            text="提示：可直接把文件 / 文件夹拖入窗口；支持 ncm / qmc 系列 / mflac / mgg / "
                 "kgm / vpr / kwm / xm / mg3d / tm 及常见音频格式。",
            fg="#666666",
            font=("TkDefaultFont", 8),
        ).pack(anchor="w", padx=10, pady=(0, 4))

        # 输出目录选择（可选，默认在源文件同目录生成）
        tk.Label(root, text="输出目录（留空则与源文件同目录）：", anchor="w").pack(
            fill=tk.X, padx=10, pady=(6, 0))
        frame2 = tk.Frame(root)
        frame2.pack(fill=tk.X, padx=10, pady=5)
        self.out_dir_var = tk.StringVar()
        tk.Entry(frame2, textvariable=self.out_dir_var, width=52).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(frame2, text="选择", command=self.select_out_dir).pack(side=tk.LEFT, padx=2)

        # 输出格式 + 码率
        f3 = tk.Frame(root)
        f3.pack(fill=tk.X, padx=10, pady=(6, 0))
        tk.Label(f3, text="输出格式：").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value=audio_core.DEFAULT_OUTPUT_FORMAT)
        fmt_names = [n if n != "orig" else "orig（原始格式·仅解密）"
                     for n in audio_core.OUTPUT_FORMAT_NAMES]
        self.format_combo = tk.OptionMenu(f3, self.format_var, *fmt_names,
                                          command=self._on_format_change)
        self.format_combo.config(width=22)
        self.format_combo.pack(side=tk.LEFT, padx=4)
        tk.Label(f3, text="  码率（有损格式）：").pack(side=tk.LEFT)
        self.bitrate_var = tk.StringVar(value=audio_core.DEFAULT_BITRATE)
        self.bitrate_entry = tk.Entry(f3, textvariable=self.bitrate_var, width=8)
        self.bitrate_entry.pack(side=tk.LEFT, padx=4)

        # 转换按钮
        self.convert_btn = tk.Button(
            root, text="开始转换", command=self.start_conversion, bg="#4CAF50", fg="white"
        )
        self.convert_btn.pack(pady=8)

        # 输出日志区域
        self.log_area = scrolledtext.ScrolledText(root, height=13, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        self._on_format_change(self.format_var.get())

        # 启用窗口拖拽（Windows 平台；其他平台静默跳过）
        self.dropper = None
        if sys.platform.startswith("win"):
            try:
                self.dropper = WindowsFileDropper(self.root, self.on_drop)
            except Exception as e:
                self.log("拖拽功能不可用：" + str(e))

    # ------------------------------------------------------------------ #
    def _on_format_change(self, value):
        """输出格式切换时更新码率输入可用性（无损/仅解密格式无码率概念）。"""
        fmt = (value or "").split("（")[0].strip()
        lossy = fmt in audio_core.OUTPUT_FORMATS and audio_core.OUTPUT_FORMATS[fmt]["bitrate"]
        state = tk.NORMAL if lossy else tk.DISABLED
        self.bitrate_entry.config(state=state)
        if not self.ffmpeg_ok and fmt != "orig":
            self.log("⚠ 未检测到 ffmpeg：仅“orig（原始格式·仅解密）”模式可用，"
                     "其余输出格式需安装 imageio-ffmpeg（pip 一键）或 ffmpeg 加入 PATH。")

    def log(self, msg):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def _last_dir(self):
        if self.input_paths:
            return os.path.dirname(self.input_paths[-1]) or "."
        return "."

    def add_files(self):
        paths = filedialog.askopenfilenames(
            initialdir=self._last_dir(),
            filetypes=audio_core.FILE_DIALOG_PATTERNS,
        )
        for p in paths:
            if p not in self.input_paths:
                self.input_paths.append(p)
                self.input_listbox.insert(tk.END, p)

    def add_folder(self):
        path = filedialog.askdirectory(initialdir=self._last_dir())
        if path and path not in self.input_paths:
            self.input_paths.append(path)
            self.input_listbox.insert(tk.END, path)

    def remove_selected(self):
        for idx in reversed(self.input_listbox.curselection()):
            del self.input_paths[idx]
            self.input_listbox.delete(idx)

    def clear_inputs(self):
        self.input_paths.clear()
        self.input_listbox.delete(0, tk.END)

    def add_manual_path(self):
        p = self.path_var.get().strip()
        if not p:
            return
        if not os.path.exists(p):
            messagebox.showwarning("警告", "路径不存在：" + p)
            return
        if p not in self.input_paths:
            self.input_paths.append(p)
            self.input_listbox.insert(tk.END, p)
            self.path_var.set("")

    def select_out_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.out_dir_var.set(path)

    def on_drop(self, paths):
        """拖拽回调：把拖入的文件/文件夹加入输入列表，并自动开始转换。"""
        added = 0
        for p in paths:
            p = p.strip().strip('"')
            if p and p not in self.input_paths:
                self.input_paths.append(p)
                self.input_listbox.insert(tk.END, p)
                added += 1
        if added:
            self.log(f"拖入 {added} 个路径，自动开始转换...")
            self.root.update_idletasks()
            # 拖拽后自动开始转换（仅在当前未在转换中时，避免重复启动线程）
            if str(self.convert_btn["state"]) != tk.DISABLED:
                self.start_conversion()

    def start_conversion(self):
        if not self.input_paths:
            messagebox.showwarning("警告", "请先添加要转换的文件或文件夹")
            return

        out_fmt = (self.format_var.get() or "mp3").split("（")[0].strip()
        if out_fmt not in audio_core.OUTPUT_FORMATS:
            out_fmt = audio_core.DEFAULT_OUTPUT_FORMAT
        if out_fmt != "orig" and not self.ffmpeg_ok:
            messagebox.showerror("错误", "未检测到 ffmpeg，无法转码。请安装 imageio-ffmpeg 或 ffmpeg 并加入 "
                                          "PATH，或选择 orig（原始格式·仅解密）模式。")
            return

        self.convert_btn.config(state=tk.DISABLED, text="转换中...")
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state=tk.DISABLED)

        # 后台线程执行转换，防止界面卡死
        threading.Thread(
            target=self.convert,
            args=(self.out_dir_var.get().strip() or None, out_fmt,
                  self.bitrate_var.get().strip() or audio_core.DEFAULT_BITRATE),
            daemon=True,
        ).start()

    def convert(self, out_dir, output_format, bitrate):
        files = audio_core.collect_files(self.input_paths)
        if not files:
            self.log("未找到任何可处理的文件（支持：ncm/qmc 系列/kgm/vpr/kwm/xm/mg3d/tm/常见音频）")
        else:
            self.log(f"找到 {len(files)} 个文件，开始转换（输出格式：{output_format}）...\n")

        success = 0
        failed = 0
        for i, path in enumerate(files, 1):
            name = os.path.basename(path)
            self.log(f"[{i}/{len(files)}] 正在处理：{name}")
            ok, msg = audio_core.process_one(path, out_dir, output_format, bitrate)
            if ok:
                success += 1
            else:
                failed += 1
            self.log(f"       [{'OK' if ok else 'FAIL'}] {msg}")

        summary = f"\n转换完成！成功：{success}，失败：{failed}"
        self.log(summary)
        self.convert_btn.config(state=tk.NORMAL, text="开始转换")
        messagebox.showinfo("完成", summary)


def cli_batch(input_paths, out_dir=None, output_format="mp3", bitrate="320k", jobs=4):
    """命令行批量转换模式（复用 audio_core）。支持多个输入路径与并发。"""
    if output_format != "orig" and not audio_core.check_ffmpeg():
        print("未检测到 ffmpeg：请 pip install imageio-ffmpeg（推荐）、或安装 ffmpeg 加入 PATH、或设环境变量 NCMTURNMP3_FFMPEG（也可用 -f orig 仅解密）",
              file=sys.stderr)
        return 1

    files = audio_core.collect_files(input_paths)
    if not files:
        print("未找到任何可处理的文件")
        return 0

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print(f"找到 {len(files)} 个文件，开始转换（输出格式：{output_format}，并发 {jobs}）...\n")
    success = 0
    failed = 0
    if jobs > 1 and len(files) > 1:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=jobs) as ex:
            for i, (ok, msg) in enumerate(
                ex.map(
                    lambda p: audio_core.process_one(p, out_dir, output_format, bitrate),
                    files,
                ),
                1,
            ):
                print(f"[{i}/{len(files)}] [{'OK' if ok else 'FAIL'}] {msg}")
                success += bool(ok)
                failed += (not ok)
    else:
        for i, path in enumerate(files, 1):
            name = os.path.basename(path)
            print(f"[{i}/{len(files)}] 正在处理：{name}")
            ok, msg = audio_core.process_one(path, out_dir, output_format, bitrate)
            success += bool(ok)
            failed += (not ok)
            print(f"       [{'OK' if ok else 'FAIL'}] {msg}")

    print(f"\n转换完成！成功：{success}，失败：{failed}")
    return 0


def interactive_cli():
    """交互式命令行：手动输入路径 / 输出目录 / 格式 / 码率。"""
    print("=== 加密音乐转换（ncm/qmc/kgm/kwm/xm/mg3d/tm → mp3/flac/... 纯本地）===")
    if not audio_core.check_ffmpeg():
        print("警告：未检测到 ffmpeg，仅支持 orig（原始格式·仅解密）输出。", file=sys.stderr)

    inputs = []
    print("请输入文件或文件夹路径（直接回车结束输入）：")
    while True:
        p = input(f"[{len(inputs) + 1}] 路径> ").strip().strip('"')
        if not p:
            break
        if not os.path.exists(p):
            print("  ! 路径不存在，已跳过。")
            continue
        inputs.append(p)

    if not inputs:
        print("未输入任何路径，已退出。")
        sys.exit(0)

    out_dir = input("输出目录（留空 = 与源文件同目录）> ").strip().strip('"') or None

    print("输出格式：mp3 / flac / wav / aac / ogg / m4a / orig（原始格式·仅解密）")
    while True:
        output_format = input("输出格式（默认 mp3）> ").strip().lower() or "mp3"
        if output_format in audio_core.OUTPUT_FORMAT_NAMES:
            break
        print("  ! 无效格式，请重新输入。")

    bitrate = audio_core.DEFAULT_BITRATE
    if audio_core.OUTPUT_FORMATS[output_format]["bitrate"]:
        bitrate = input("码率（默认 320k）> ").strip() or audio_core.DEFAULT_BITRATE

    files = audio_core.collect_files(inputs)
    if not files:
        print("未找到任何可处理的文件。")
        sys.exit(0)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print(f"\n找到 {len(files)} 个文件，开始转换（输出格式：{output_format}）...\n")
    success = 0
    failed = 0
    for i, (ok, msg) in enumerate(
        (audio_core.process_one(f, out_dir, output_format, bitrate) for f in files), 1
    ):
        print(f"[{i}/{len(files)}] [{'OK' if ok else 'FAIL'}] {msg}")
        success += bool(ok)
        failed += (not ok)

    print(f"\n转换完成！成功：{success}，失败：{failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="加密音乐转换器（无参数启动 GUI；-i 交互式；带参数则命令行批量转换）\n"
                    "输入支持：ncm / qmc 全家族 / tm 缓存 / kgm / kgma / vpr / kwm / xm / mg3d"
                    " / 常见音频；输出支持：mp3 / flac / wav / aac / ogg / m4a / orig",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="交互式命令行模式（手动输入路径）")
    parser.add_argument("input", nargs="*",
                        help="加密音乐文件/音频文件或包含它们的目录（可多个）")
    parser.add_argument("-o", "--output", default=None, help="输出目录（默认与源文件同目录）")
    parser.add_argument("-f", "--format", default="mp3", dest="output_format",
                        choices=audio_core.OUTPUT_FORMAT_NAMES,
                        help="输出格式（默认 mp3；orig = 原始格式仅解密不转码）")
    parser.add_argument("-b", "--bitrate", default="320k", help="码率，默认 320k（有损格式生效）")
    parser.add_argument("-j", "--jobs", type=int, default=4, help="并发线程数，默认 4")
    args = parser.parse_args()

    if args.interactive:
        interactive_cli()
    elif args.input:
        sys.exit(cli_batch(args.input, args.output, args.output_format, args.bitrate, args.jobs))
    else:
        root = tk.Tk()
        app = ConverterApp(root)
        root.mainloop()
