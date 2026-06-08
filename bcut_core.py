# bcut_core.py
# 这个文件包含所有核心功能函数，不包含任何与用户交互直接相关的 print（除了调试可能保留，但我们会提供回调日志机制，为方便命令行暂时保留 print，GUI 时可以重定向）。
import os
import glob
import json
import re
import copy
import random
import time

def find_latest_draft(drafts_dir=None):
    """
    找到最新的必剪草稿文件夹
    返回草稿文件夹路径，如果没有找到则返回 None
    """
    if drafts_dir is None:
        drafts_dir = os.path.expanduser("~/Documents/Bcut Drafts")
    draft_folders = glob.glob(os.path.join(drafts_dir, "*/"))
    if not draft_folders:
        return None
    latest = max(draft_folders, key=os.path.getmtime)
    return latest

def find_latest_bjson(draft_folder):
    """
    在草稿文件夹中找到最新的 .bjson 文件
    返回 .bjson 文件完整路径，如果没有找到则返回 None
    """
    if not os.path.isdir(draft_folder):
        return None
    all_files = os.listdir(draft_folder)
    bjson_files = [f for f in all_files if f.endswith('.bjson')]
    if not bjson_files:
        return None
    # 按修改时间排序
    bjson_with_mtime = [(os.path.getmtime(os.path.join(draft_folder, f)), os.path.join(draft_folder, f)) for f in bjson_files]
    bjson_with_mtime.sort(reverse=True)
    return bjson_with_mtime[0][1]

def parse_srt_file(srt_path):
    """
    解析 SRT 文件，返回列表，每个元素为 dict:
        {'index': int, 'start': int(ms), 'end': int(ms), 'text': str}
    如果解析失败，抛出异常
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    blocks = content.split('\n\n')
    subtitles = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) < 3:
            continue
        try:
            idx = int(lines[0].strip())
        except ValueError:
            idx = len(subtitles) + 1
        time_line = lines[1].strip()
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_line)
        if not match:
            # 时间轴格式错误，跳过这一条
            continue
        start_h, start_m, start_s, start_ms = map(int, match.group(1,2,3,4))
        start_ms_total = start_h*3600000 + start_m*60000 + start_s*1000 + start_ms
        end_h, end_m, end_s, end_ms = map(int, match.group(5,6,7,8))
        end_ms_total = end_h*3600000 + end_m*60000 + end_s*1000 + end_ms
        text_lines = lines[2:]
        text = '\n'.join(text_lines).strip()
        subtitles.append({
            'index': idx,
            'start': start_ms_total,
            'end': end_ms_total,
            'text': text
        })
    return subtitles

def find_subtitles_array(data):
    """
    从必剪的 JSON 数据中定位字幕数组（支持多种版本）
    返回字幕列表（list of dict），如果找不到返回 None
    """
    try:
        # 新版本路径：timelineWidget.timeline.captionTracks[0].captions
        timeline = data.get('timelineWidget', {}).get('timeline', {})
        caption_tracks = timeline.get('captionTracks', [])
        if caption_tracks and len(caption_tracks) > 0:
            captions = caption_tracks[0].get('captions', [])
            if captions:
                return captions

        # 旧版本路径：timelineWidget.tracks (type=subtitle/text -> segments)
        tracks = data.get('timelineWidget', {}).get('tracks', [])
        for track in tracks:
            if track.get('type') in ['subtitle', 'text']:
                return track.get('segments', [])

        return None
    except Exception:
        return None

def generate_id():
    """生成类似必剪的 idString 和 uid"""
    base = str(int(time.time() * 1000000)) + str(random.randint(10000, 99999))
    return base

def apply_srt_to_caption(caption, srt_item):
    """将一条 SRT 数据应用到必剪字幕条目上"""
    caption['captionText'] = srt_item['text']
    if 'assetInfo' in caption and isinstance(caption['assetInfo'], dict):
        caption['assetInfo']['content'] = srt_item['text']
        caption['assetInfo']['displayName'] = srt_item['text']
        caption['assetInfo']['duration'] = srt_item['end'] - srt_item['start']
    caption['inPoint'] = srt_item['start']
    caption['outPoint'] = srt_item['end']
    caption['idString'] = generate_id()
    caption['uid'] = generate_id()
    return caption

def replace_subtitles_with_srt(bjson_path, srt_data):
    """
    读取 bjson 文件，用 srt_data 替换字幕数组（数量以 SRT 为准）
    返回 (是否成功, 原字幕数量, 新字幕数量, 错误信息)
    """
    try:
        with open(bjson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, 0, 0, f"读取 bjson 失败: {e}"
    
    subtitles_arr = find_subtitles_array(data)
    if subtitles_arr is None:
        return False, 0, 0, "未找到字幕数组，可能格式不匹配"
    
    orig_count = len(subtitles_arr)
    new_count = len(srt_data)
    
    # 准备模板
    template = None
    if orig_count > 0:
        template = copy.deepcopy(subtitles_arr[0])
    
    new_subtitles = []
    for i, srt_item in enumerate(srt_data):
        if i < orig_count:
            new_caption = apply_srt_to_caption(subtitles_arr[i], srt_item)
        elif template is not None:
            new_caption = copy.deepcopy(template)
            new_caption = apply_srt_to_caption(new_caption, srt_item)
        else:
            return False, orig_count, 0, f"无法创建第{i+1}条字幕：没有模板可用"
        new_subtitles.append(new_caption)
    
    # 替换原数组
    subtitles_arr.clear()
    subtitles_arr.extend(new_subtitles)
    
    # 备份并写入
    backup_path = bjson_path + ".bak"
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(bjson_path, backup_path)
        with open(bjson_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, orig_count, new_count, backup_path
    except Exception as e:
        return False, orig_count, new_count, f"写入失败: {e}"

def export_subtitles_to_srt(bjson_path, output_path=None):
    """
    从 bjson 文件中提取字幕并保存为 SRT 文件
    返回 (是否成功, srt文件路径, 字幕条数, 错误信息)
    """
    try:
        with open(bjson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, None, 0, f"读取 bjson 失败: {e}"
    
    subtitles_arr = find_subtitles_array(data)
    if subtitles_arr is None:
        return False, None, 0, "未找到字幕数组"
    
    # 生成 SRT 内容
    srt_lines = []
    for idx, cap in enumerate(subtitles_arr, start=1):
        # 时间轴转换：毫秒 -> HH:MM:SS,mmm
        start_ms = cap.get('inPoint', 0)
        end_ms = cap.get('outPoint', 0)
        def ms_to_srt(ms):
            h = ms // 3600000
            m = (ms % 3600000) // 60000
            s = (ms % 60000) // 1000
            mill = ms % 1000
            return f"{h:02d}:{m:02d}:{s:02d},{mill:03d}"
        start_str = ms_to_srt(start_ms)
        end_str = ms_to_srt(end_ms)
        # 文字
        text = cap.get('captionText', '')
        if not text:
            # 尝试其他字段
            text = cap.get('text', '')
        srt_lines.append(str(idx))
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(text)
        srt_lines.append('')  # 空行
    
    srt_content = '\n'.join(srt_lines)
    
    if output_path is None:
        # 自动生成路径：放在 bjson 所在文件夹，文件名加 _export.srt
        base = os.path.splitext(bjson_path)[0]
        output_path = f"{base}_export.srt"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        return True, output_path, len(subtitles_arr), None
    except Exception as e:
        return False, None, len(subtitles_arr), f"保存失败: {e}"

def is_bjson_locked(bjson_path):
    """检测 bjson 文件是否被其他进程（如必剪）占用"""
    try:
        # 尝试以读写模式打开，不实际修改
        with open(bjson_path, 'r+', encoding='utf-8') as f:
            pass
        return False
    except PermissionError:
        return True
    except Exception:
        # 其他错误视为未锁定（或不确定）
        return False