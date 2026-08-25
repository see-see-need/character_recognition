# 屏幕文字识别

一款面向 Windows 的屏幕 OCR 工具。按 `Ctrl+Shift+S` 或点击“开始框选”，用鼠标左键拖出区域，松开后在本机识别文字并自动复制。

## 功能

- 简体中文、繁体中文、英文、日文和韩文自动识别
- 主窗口、全局快捷键与系统托盘入口
- 单显示器框选，适配 Windows DPI 缩放
- 可编辑结果、自动复制、可选开机启动
- 截图只在内存中处理，不上传屏幕内容
- 可通过 DeepSeek 将识别文字翻译为简体中文，支持手动或自动翻译
- 原文和译文分别可编辑、复制，翻译失败不会影响 OCR 原文

## 开发运行

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python scripts\prepare_models.py
.venv\Scripts\python -m screen_ocr
```

`prepare_models.py` 会在开发阶段下载三个官方 OCR 模型并复制到项目的 `models` 目录。准备完成后，应用识别过程不需要网络。

## 测试

```powershell
.venv\Scripts\python -m pytest
```

## 便携构建

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

输出位于 `dist\ScreenOCR`。请分发整个目录；不要只复制其中的 exe，否则 Qt 运行库和离线模型会缺失。

## DeepSeek 翻译

翻译使用 DeepSeek API，需要联网并消耗 DeepSeek 账户额度。在“设置”中填写 API Key；密钥会保存到当前 Windows 用户的凭据管理器，不会写入普通配置文件。

默认需要在识别结果中点击“翻译”。开启“识别后自动翻译为简体中文”后，每次 OCR 完成都会自动请求译文，修改原文后仍可点击“重新翻译”。应用只向 DeepSeek 发送文字，不会发送截图。
