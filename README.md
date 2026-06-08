# 必剪字幕工坊 (Bcut Subtitle Workshop)

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/Cyrusch1/bcut-subtitle-workshop)
[![Python](https://img.shields.io/badge/python-3.10%2B-green)](https://python.org)

为必剪视频剪辑软件设计的字幕辅助工具，支持 **SRT 字幕导入（含时间轴替换）** 和 **草稿字幕导出为 SRT**，并提供图形界面和命令行两种使用方式。

## ✨ 功能特点

- **导入 SRT 字幕到必剪草稿**：将外挂双语 SRT 字幕（文字 + 时间轴）直接覆写进必剪草稿，替换原有识别字幕。
- **导出必剪草稿字幕为 SRT**：从最新草稿中提取字幕，保存为标准 SRT 文件，方便二次编辑或翻译。
- **图形界面 (GUI)**：基于 `tkinter` 构建，一个字，“简单”（狗头）。
- **自动定位草稿**：无需手动查找，自动选择最新修改的草稿和字幕文件。

## 📦 安装与依赖
### 1. 克隆仓库
```bash
git clone https://github.com/Cyrusch1/bcut-subtitle-workshop.git
cd bcut-subtitle-workshop
```

2. 安装 Python 依赖
本项目核心功能仅使用 Python 标准库，无需额外安装。
图形界面使用 tkinter（Python 自带），无需额外安装。

注意：Python 版本要求 3.10 及以上。

🚀 使用方法
图形界面（推荐）
```bash
python bcut_gui.py
```

点击 “导入 SRT 到草稿”：选择 SRT 文件，确认后自动替换最新草稿的字幕。

点击 “导出草稿为 SRT”：选择保存路径，将草稿中的字幕导出为 SRT 文件。

操作过程中下方会显示进度条和状态信息，日志区域实时输出详情。

命令行
```bash
# 导入 SRT 文件到最新草稿
python bcut_cli.py import 字幕.srt

# 导出最新草稿的字幕为 SRT
python bcut_cli.py export -o 导出文件.srt

# 检查最新草稿状态（字幕条数）
python bcut_cli.py check
```
⚠️ 使用注意事项
替换前请关闭必剪中对应的草稿编辑窗口，否则替换可能无效（必剪会在关闭时覆盖文件）。

SRT 文件必须为 UTF-8 编码，时间轴格式为 HH:MM:SS,mmm --> HH:MM:SS,mmm。

如果 SRT 字幕条数与草稿原有字幕条数不一致，程序会以 SRT 为准进行完整替换（增加或删除条目）。

导入后如需恢复，请找到草稿文件夹中的 .bjson.bak 备份文件，去掉 .bak 后缀覆盖原文件。

📂 文件说明
文件	说明
bcut_core.py	核心逻辑库，包含所有文件操作、解析、替换等函数
bcut_cli.py	命令行入口，基于 argparse 实现子命令
bcut_gui.py	图形界面入口，基于 tkinter

🛠️ 开发计划
- 精细化控制（批量控制接口）
- 更精细的图形界面显示（导入srt字幕后显示字幕内容）
- 字幕编辑功能（1、覆盖草稿字幕前可以对srt文件进行审核编辑）
- 安全备份和恢复gui控件
- 整合生成双语字幕，字幕优化（调用翻译 API）

🤝 贡献
欢迎提交 Issue 和 Pull Request。如果你有任何改进建议或发现 bug，请随时联系。
