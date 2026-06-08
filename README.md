# 必剪字幕工坊 (Bcut Subtitle Workshop)

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/Cyrusch1/bcut-subtitle-workshop)
[![Python](https://img.shields.io/badge/python-3.10%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

为必剪视频剪辑软件设计的字幕辅助工具，支持 **SRT 字幕导入（含时间轴替换）** 和 **草稿字幕导出为 SRT**，并提供图形界面和命令行两种使用方式。

## 功能特点

- **导入 SRT 字幕到必剪草稿**：将外挂双语 SRT 字幕（文字 + 时间轴）直接覆写进必剪草稿，替换原有识别字幕。
- **导出必剪草稿字幕为 SRT**：从最新草稿中提取字幕，保存为标准 SRT 文件，方便二次编辑或翻译。
- **图形界面 (GUI)**：基于 `tkinter` 构建，操作直观，包含进度条和状态提示。
- **命令行 (CLI)**：提供 `import`、`export`、`check` 三个子命令，适合脚本化和批量处理。
- **自动定位草稿**：无需手动查找，自动选择最新修改的草稿和字幕文件。
- **安全备份**：导入前自动备份原 `.bjson` 文件，可随时恢复。

## 项目结构

```
bcut-subtitle-workshop/
├── bcut_core.py      # 核心功能模块（查找草稿、解析 SRT、替换/导出字幕）
├── bcut_cli.py       # 命令行入口
├── bcut_gui.py       # 图形界面入口
└── README.md
```

## 安装与依赖

### 1. 克隆仓库

```bash
git clone https://github.com/Cyrusch1/bcut-subtitle-workshop.git
cd bcut-subtitle-workshop
```

### 2. Python 版本要求

本项目核心功能仅使用 Python 标准库，无需额外安装第三方依赖。

图形界面使用 `tkinter`（Python 自带），无需额外安装。

> **注意**：Python 版本要求 3.10 及以上。

## 使用方法

### 图形界面（推荐）

```bash
python bcut_gui.py
```

打开窗口后：
- 点击 **「📥 导入 SRT 到草稿」** 选择 SRT 文件，自动导入到最新必剪草稿。
- 点击 **「📤 导出草稿为 SRT」** 将最新草稿的字幕导出为 SRT 文件。

### 命令行

```bash
# 导入 SRT 到最新草稿
python bcut_cli.py import path/to/subtitle.srt

# 导出最新草稿字幕为 SRT
python bcut_cli.py export -o output.srt

# 检查草稿状态（是否被占用、字幕条数）
python bcut_cli.py check
```

## 工作原理

1. 自动定位 `~/Documents/Bcut Drafts/` 下最新修改的草稿文件夹。
2. 在该文件夹中找到最新的 `.bjson` 字幕数据文件。
3. 读取 SRT / 提取 bjson 中的字幕数据。
4. 覆写字幕文字和时间轴，备份原文件（`*.bjson.bak`）。

## 注意事项

- 导入/导出前，请**关闭必剪中对应草稿的编辑窗口**，否则可能导致替换失败。
- 导入操作会覆写草稿中已有的识别字幕，操作前会自动备份。
- 如果必剪更新改变了 `.bjson` 的内部格式，本工具可能暂时失效（欢迎提 Issue）。

## License

MIT License
