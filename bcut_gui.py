import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from bcut_core import (
    find_latest_draft,
    find_latest_bjson,
    parse_srt_file,
    replace_subtitles_with_srt,
    export_subtitles_to_srt,
    find_subtitles_array,
)
import json

class BcutSubtitleWorkshop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("必剪字幕工坊 v2.0")
        self.root.geometry("800x650")
        self.root.resizable(False, False)

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # ========== 按钮区域 ==========
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_import = tk.Button(btn_frame, text="📥 导入 SRT 到草稿", width=20, height=2,
                                    command=self.import_srt_thread)
        self.btn_import.pack(side=tk.LEFT, padx=10)

        self.btn_export = tk.Button(btn_frame, text="📤 导出草稿为 SRT", width=20, height=2,
                                    command=self.export_srt_thread)
        self.btn_export.pack(side=tk.LEFT, padx=10)

        # ========== 状态栏（进度条 + 状态文字）==========
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=300)
        self.progress.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = tk.Label(status_frame, text="就绪", anchor='w')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ========== 日志显示区域 ==========
        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Consolas", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def on_closing(self):
        self.root.destroy()

    # ---------- 线程安全的 UI 更新 ----------
    def log(self, message):
        """在日志区域添加一行"""
        def _log():
            self.log_area.insert(tk.END, message + '\n')
            self.log_area.see(tk.END)
        self.root.after(0, _log)
        print(message)

    def set_status(self, text, is_error=False):
        """更新状态栏文字（可选错误样式）"""
        def _set():
            self.status_label.config(text=text, fg='red' if is_error else 'black')
        self.root.after(0, _set)

    def start_progress(self):
        """启动进度条（不确定模式）"""
        def _start():
            self.progress.start(10)
        self.root.after(0, _start)

    def stop_progress(self):
        """停止进度条"""
        def _stop():
            self.progress.stop()
        self.root.after(0, _stop)

    # ---------- 核心功能线程 ----------
    def import_srt_thread(self):
        threading.Thread(target=self.import_srt, daemon=True).start()

    def export_srt_thread(self):
        threading.Thread(target=self.export_srt, daemon=True).start()

    # ---------- 导入功能 ----------
    def import_srt(self):
        self.start_progress()
        self.set_status("正在选择 SRT 文件...")
        srt_path = filedialog.askopenfilename(
            title="选择 SRT 字幕文件",
            filetypes=[("SRT 文件", "*.srt"), ("所有文件", "*.*")]
        )
        if not srt_path:
            self.set_status("已取消")
            self.stop_progress()
            return

        self.log("--- 开始导入 ---")
        self.log(f"选择的 SRT 文件: {srt_path}")

        self.set_status("正在查找必剪草稿...")
        draft_folder = find_latest_draft()
        if not draft_folder:
            self.log("❌ 没有找到任何必剪草稿，请先在必剪里保存一个草稿。")
            self.set_status("失败：未找到草稿", is_error=True)
            self.stop_progress()
            return
        self.log(f"✅ 找到草稿文件夹：{draft_folder}")

        bjson_path = find_latest_bjson(draft_folder)
        if not bjson_path:
            self.log("❌ 在草稿文件夹中没有找到任何 .bjson 文件")
            self.set_status("失败：未找到字幕文件", is_error=True)
            self.stop_progress()
            return
        self.log(f"✅ 找到最新的字幕文件：{os.path.basename(bjson_path)}")

        self.set_status("正在解析 SRT 文件...")
        try:
            srt_data = parse_srt_file(srt_path)
            self.log(f"✅ 从 SRT 读取到 {len(srt_data)} 条完整字幕")
            if srt_data:
                self.log(f"   例如第一条：从 {srt_data[0]['start']}ms 到 {srt_data[0]['end']}ms")
        except Exception as e:
            self.log(f"❌ 解析 SRT 出错：{e}")
            self.set_status("解析 SRT 失败", is_error=True)
            self.stop_progress()
            return

        # 用户确认
        if not messagebox.askyesno("确认操作",
                                   "即将替换草稿中的字幕。\n请确保必剪软件中没有打开这个草稿，否则替换可能不生效。\n\n是否继续？"):
            self.log("操作已取消。")
            self.set_status("已取消")
            self.stop_progress()
            return

        self.set_status("正在替换字幕...")
        success, orig_count, new_count, info = replace_subtitles_with_srt(bjson_path, srt_data)
        if success:
            self.log(f"🎉 成功！已按 SRT 完整替换字幕：原有 {orig_count} 条 → 新 {new_count} 条")
            self.log(f"原文件已备份为：{info}")
            self.log("请打开必剪，加载这个草稿，检查字幕是否已经更新。")
            self.set_status("导入成功")
        else:
            self.log(f"❌ 替换失败：{info}")
            self.set_status("导入失败", is_error=True)

        self.log("--- 导入结束 ---\n")
        self.stop_progress()

    # ---------- 导出功能 ----------
    def export_srt(self):
        self.start_progress()
        self.set_status("正在查找草稿...")
        self.log("--- 开始导出 ---")

        draft_folder = find_latest_draft()
        if not draft_folder:
            self.log("❌ 没有找到任何必剪草稿。")
            self.set_status("失败：未找到草稿", is_error=True)
            self.stop_progress()
            return
        self.log(f"✅ 找到草稿文件夹：{draft_folder}")

        bjson_path = find_latest_bjson(draft_folder)
        if not bjson_path:
            self.log("❌ 没有找到任何字幕文件。")
            self.set_status("失败：未找到字幕文件", is_error=True)
            self.stop_progress()
            return
        self.log(f"✅ 找到最新的字幕文件：{os.path.basename(bjson_path)}")

        self.set_status("选择保存位置...")
        output_path = filedialog.asksaveasfilename(
            title="保存 SRT 文件为",
            defaultextension=".srt",
            filetypes=[("SRT 文件", "*.srt"), ("所有文件", "*.*")]
        )
        if not output_path:
            self.log("导出已取消。")
            self.set_status("已取消")
            self.stop_progress()
            return

        self.set_status("正在导出字幕...")
        success, out_path, count, error = export_subtitles_to_srt(bjson_path, output_path)
        if success:
            self.log(f"🎉 成功！已导出 {count} 条字幕到：{out_path}")
            self.set_status("导出成功")
        else:
            self.log(f"❌ 导出失败：{error}")
            self.set_status("导出失败", is_error=True)

        self.log("--- 导出结束 ---\n")
        self.stop_progress()

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = BcutSubtitleWorkshop()
    app.run()