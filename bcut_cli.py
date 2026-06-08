# bcut_cli.py 命令行入口，使用 argparse 实现子命令：import、export、check。
import sys
import os
import argparse
from bcut_core import (
    find_latest_draft,
    find_latest_bjson,
    parse_srt_file,
    replace_subtitles_with_srt,
    export_subtitles_to_srt,
    is_bjson_locked
)

# 强制 UTF-8 输出（Windows）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='必剪字幕工坊 - 命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # import 子命令
    import_parser = subparsers.add_parser('import', help='导入 SRT 文件到最新草稿')
    import_parser.add_argument('srt_file', help='SRT 文件路径')
    
    # export 子命令
    export_parser = subparsers.add_parser('export', help='导出最新草稿的字幕为 SRT')
    export_parser.add_argument('-o', '--output', help='输出 SRT 文件路径（可选）')
    
    # check 子命令
    check_parser = subparsers.add_parser('check', help='检查最新草稿状态（是否被占用、字幕条数）')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # 1. 找到最新草稿
    draft_folder = find_latest_draft()
    if not draft_folder:
        print("❌ 没有找到任何必剪草稿，请先在必剪里保存一个草稿。")
        return
    
    print(f"✅ 找到草稿文件夹：{draft_folder}")
    
    # 2. 找到最新 bjson
    bjson_path = find_latest_bjson(draft_folder)
    if not bjson_path:
        print("❌ 在草稿文件夹中没有找到任何 .bjson 文件")
        return
    
    print(f"✅ 找到最新的字幕文件：{os.path.basename(bjson_path)}")
    
    # 3. 检查是否被占用（对于 import 和 check 尤其重要）
    if args.command in ['import', 'check']:
        if is_bjson_locked(bjson_path):
            print("⚠️ 警告：草稿文件正在被必剪使用，请先关闭必剪中的该草稿编辑窗口，否则替换可能失败。")
            if args.command == 'import':
                proceed = input("是否继续？(y/N): ").strip().lower()
                if proceed != 'y':
                    print("操作已取消。")
                    return
    
    # 执行子命令
    if args.command == 'import':
        srt_path = args.srt_file
        try:
            srt_data = parse_srt_file(srt_path)
            print(f"✅ 从 SRT 读取到 {len(srt_data)} 条完整字幕（含时间轴）")
            if srt_data:
                print(f"   例如第一条：从 {srt_data[0]['start']}ms 到 {srt_data[0]['end']}ms，文字：“{srt_data[0]['text'][:30]}...”")
        except FileNotFoundError:
            print(f"❌ 找不到 SRT 文件：{srt_path}")
            return
        except Exception as e:
            print(f"❌ 解析 SRT 出错：{e}")
            return
        
        success, orig_count, new_count, info = replace_subtitles_with_srt(bjson_path, srt_data)
        if success:
            print(f"🎉 成功！已按 SRT 完整替换字幕：原有 {orig_count} 条 → 新 {new_count} 条")
            print(f"原文件已备份为：{info}")
            print("请打开必剪，加载这个草稿，检查字幕是否已经更新。")
        else:
            print(f"❌ 替换失败：{info}")
    
    elif args.command == 'export':
        output = args.output
        success, out_path, count, error = export_subtitles_to_srt(bjson_path, output)
        if success:
            print(f"🎉 成功！已导出 {count} 条字幕到：{out_path}")
        else:
            print(f"❌ 导出失败：{error}")
    
    elif args.command == 'check':
        # 尝试解析 bjson 获取字幕条数
        try:
            import json
            with open(bjson_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            from bcut_core import find_subtitles_array
            subs = find_subtitles_array(data)
            if subs is not None:
                print(f"✅ 当前草稿包含 {len(subs)} 条字幕")
            else:
                print("⚠️ 未能解析字幕数组，可能格式不支持")
        except Exception as e:
            print(f"⚠️ 读取字幕信息失败：{e}")
        # 检查占用状态（前面已经检测过）
        if is_bjson_locked(bjson_path):
            print("⚠️ 草稿文件当前被必剪占用，请关闭编辑窗口后再进行导入/导出操作。")
        else:
            print("✅ 草稿文件未被占用，可以进行操作。")

if __name__ == "__main__":
    main()