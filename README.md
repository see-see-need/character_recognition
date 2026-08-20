# 屏幕文字识别

一款面向 Windows 的离线屏幕 OCR 工具。按 `Ctrl+Shift+S` 或点击“开始框选”，用鼠标左键拖出区域，松开后识别文字并自动复制。

## 功能

- 简体中文、繁体中文、英文、日文和韩文自动识别
- 主窗口、全局快捷键与系统托盘入口
- 单显示器框选，适配 Windows DPI 缩放
- 可编辑结果、自动复制、可选开机启动
- 截图只在内存中处理，不上传屏幕内容
- 预留异步翻译提供方接口，未来目标语言默认为简体中文

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

## 翻译扩展

翻译尚未启用。未来实现 `TranslationProvider.translate()`，将提供方注册到 `TextPipeline`，再打开 `translation.enabled` 即可接入。在线服务的密钥应由 `CredentialStore` 的 Windows Credential Manager 实现保存，不得写入普通配置文件。
