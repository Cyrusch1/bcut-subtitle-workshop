import os
import sys
import glob
import json
import re

# 强制 UTF-8 输出，避免 Windows GBK 编码问题
sys.stdout.reconfigure(encoding='utf-8')

# ========== 1. 自动找到最新必剪草稿 ==========
drafts_dir = os.path.expanduser("~/Documents/Bcut Drafts")
draft_folders = glob.glob(os.path.join(drafts_dir, "*/"))

if not draft_folders:
    print("❌ 没有找到任何必剪草稿，请先在必剪里保存一个草稿。")
    exit()

latest_folder = max(draft_folders, key=os.path.getmtime)
print(f"✅ 找到草稿文件夹：{latest_folder}")

# ========== 2. 找到草稿里最新的 .bjson 字幕文件 ==========
all_files = os.listdir(latest_folder)
bjson_files = [f for f in all_files if f.endswith('.bjson')]

if not bjson_files:
    print("❌ 在草稿文件夹中没有找到任何 .bjson 文件")
    exit()

# 按修改时间排序，取最新的
bjson_files_with_mtime = []
for f in bjson_files:
    full_path = os.path.join(latest_folder, f)
    mtime = os.path.getmtime(full_path)
    bjson_files_with_mtime.append((mtime, full_path))

bjson_files_with_mtime.sort(reverse=True)
latest_bjson_path = bjson_files_with_mtime[0][1]

print(f"✅ 找到最新的字幕文件：{os.path.basename(latest_bjson_path)}")
bjson_path = latest_bjson_path
print(f"✅ 找到字幕文件：{bjson_path}")

# ========== 3. 读取SRT文件，提取完整字幕信息（序号、时间轴、文字）==========
srt_file = "test.srt"

def parse_srt_full(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
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
            print(f"⚠️ 时间轴格式错误，跳过：{time_line}")
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

try:
    srt_data = parse_srt_full(srt_file)
    print(f"✅ 从SRT读取到 {len(srt_data)} 条完整字幕（含时间轴）")
    if srt_data:
        print(f"   例如第一条：从 {srt_data[0]['start']}ms 到 {srt_data[0]['end']}ms ，文字：“{srt_data[0]['text'][:20]}...”")
except FileNotFoundError:
    print(f"❌ 找不到文件 '{srt_file}'，请确认文件名和路径正确")
    exit()
except Exception as e:
    print(f"❌ 解析SRT时出错：{e}")
    exit()

# ========== 提前定义两个辅助函数（避免调用时未定义）==========
def print_timeline_structure(data, max_depth=3, current_depth=0):
    if current_depth > max_depth:
        return
    if isinstance(data, dict) and 'timelineWidget' in data:
        timeline = data['timelineWidget']
        print("🚀 探索 timelineWidget 的内部结构:")
        print(f"  timelineWidget 包含的顶层键: {list(timeline.keys())}")
        if 'tracks' in timeline:
            tracks = timeline['tracks']
            print(f"  找到 {len(tracks)} 个轨道")
            for idx, track in enumerate(tracks):
                print(f"    轨道 {idx} 包含的键: {list(track.keys())}")
                if 'segments' in track:
                    segments = track['segments']
                    print(f"      找到 {len(segments)} 个片段")
                    if len(segments) > 0:
                        print(f"      第一个片段样例: {segments[0]}")
        return
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'timelineWidget':
                print_timeline_structure({key: value}, max_depth, current_depth+1)
                break
            else:
                print_timeline_structure(value, max_depth, current_depth+1)
    elif isinstance(data, list):
        for item in data:
            print_timeline_structure(item, max_depth, current_depth+1)

def find_subtitles_array(data):
    """从新版本的必剪JSON结构中提取字幕数据"""
    try:
        # 优先尝试新版本路径：timelineWidget.timeline.captionTracks[0].captions
        timeline = data.get('timelineWidget', {}).get('timeline', {})
        caption_tracks = timeline.get('captionTracks', [])
        if caption_tracks and len(caption_tracks) > 0:
            captions = caption_tracks[0].get('captions', [])
            if captions:
                return captions

        # 尝试旧版本路径：timelineWidget.tracks (type=subtitle/text -> segments)
        tracks = data.get('timelineWidget', {}).get('tracks', [])
        for track in tracks:
            if track.get('type') in ['subtitle', 'text']:
                return track.get('segments', [])

        # 都找不到则返回 None
        return None
    except Exception as e:
        print(f"定位字幕数组时出错: {e}")
        return None

# ========== 4. 读取bjson文件 ==========
with open(bjson_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 🚀 调用调试函数，探索文件结构
print_timeline_structure(data)

# ========== 5. 定位字幕数组 ==========
subtitles_arr = find_subtitles_array(data)
if subtitles_arr is None:
    print("❌ 在bjson文件中没有找到字幕数组，可能必剪版本更新了格式")
    print("   尝试输出bjson的一小部分结构以供调试：")
    if isinstance(data, dict):
        print("   bjson顶层键：", list(data.keys())[:5])
    exit()

print(f"✅ 找到原有字幕 {len(subtitles_arr)} 条")

# ========== 6. 以SRT为准，重建字幕数组 ==========
import copy
import random
import time

if len(srt_data) != len(subtitles_arr):
    print(f"⚠️ 注意：SRT有{len(srt_data)}条，必剪原有{len(subtitles_arr)}条，将以SRT为准进行完整替换")

def generate_id():
    """生成类似必剪的 idString 和 uid"""
    base = str(int(time.time() * 1000000)) + str(random.randint(10000, 99999))
    return base

def apply_srt_to_caption(caption, srt_item):
    """将一条SRT数据应用到一条必剪字幕条目上"""
    # 文字
    caption['captionText'] = srt_item['text']
    
    # assetInfo
    if 'assetInfo' in caption and isinstance(caption['assetInfo'], dict):
        caption['assetInfo']['content'] = srt_item['text']
        caption['assetInfo']['displayName'] = srt_item['text']
        caption['assetInfo']['duration'] = srt_item['end'] - srt_item['start']
    
    # 时间轴
    caption['inPoint'] = srt_item['start']
    caption['outPoint'] = srt_item['end']
    
    # 更新 idString 和 uid（确保唯一性）
    caption['idString'] = generate_id()
    caption['uid'] = generate_id()
    
    return caption

# 使用第一条字幕作为模板
template = None
if len(subtitles_arr) > 0:
    template = copy.deepcopy(subtitles_arr[0])

# 重建字幕数组
new_subtitles = []
for i, srt_item in enumerate(srt_data):
    if i < len(subtitles_arr):
        # 有现成的条目，直接覆盖
        new_caption = apply_srt_to_caption(subtitles_arr[i], srt_item)
    elif template is not None:
        # 条目不够，用模板克隆新的
        new_caption = copy.deepcopy(template)
        new_caption = apply_srt_to_caption(new_caption, srt_item)
    else:
        print(f"❌ 无法创建第{i+1}条字幕：没有模板可用")
        exit()
    new_subtitles.append(new_caption)

# 替换回原来的字幕数组
subtitles_arr.clear()
subtitles_arr.extend(new_subtitles)

print(f"✅ 已按SRT完整替换为 {len(new_subtitles)} 条字幕")

# ========== 7. 备份并写入 ==========
backup_path = bjson_path + ".bak"
try:
    # 如果备份文件已存在，先删除（避免 WinError 183）
    if os.path.exists(backup_path):
        os.remove(backup_path)
    os.rename(bjson_path, backup_path)
    with open(bjson_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("🎉 成功！字幕已替换（文字+时间轴）。")
    print(f"原文件已备份为：{backup_path}")
    print("请打开必剪，加载这个草稿，检查字幕是否已经更新。")
except Exception as e:
    print(f"❌ 写入文件失败：{e}")
    print("请检查文件是否被必剪或其他程序占用，然后重试。")