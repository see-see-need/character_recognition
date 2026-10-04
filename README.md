# character_recognition（屏幕文字识别）

一款面向 Windows 的屏幕 OCR 工具。按 `Ctrl+Shift+S` 或点击“开始框选”，用鼠标左键拖出区域，松开后在本机识别文字并自动复制。

本人小白，自用项目，全ai
## 功能

- 简体中文、繁体中文、英文、日文和韩文自动识别
- 主窗口、全局快捷键与系统托盘入口
- 单显示器框选，适配 Windows DPI 缩放
- 可编辑结果、自动复制、可选开机启动
- 截图只在内存中处理，不上传屏幕内容
- 可通过 DeepSeek 将识别文字翻译为简体中文，支持手动或自动翻译
- 原文和译文分别可编辑、复制，翻译失败不会影响 OCR 原文

## 持续翻译

主窗口或托盘点击“持续翻译”，框选一次后即可持续读取这个固定屏幕区域。
选区保留透明边框和屏幕原文，上方自动显示透明背景、带描边的简体中文译文；
不弹出识别结果窗、不提供编辑，也不会自动覆盖剪贴板。选区和译文允许鼠标穿透。
上方空间不足时译文移到下方或屏幕内，长译文使用工具条的“上一页／下一页”阅读。

画面每 500 毫秒检查一次，稳定后识别，连续变化最多等待 2 秒；文字相同不重复翻译。
首次加载 OCR 模型及网络翻译仍需要时间。新内容会取消过期翻译，避免排队。
网络错误重试耗尽后每 30 秒自动恢复；密钥或余额错误会显示提示，保存设置后恢复。
持续模式总是自动翻译，需要已配置 DeepSeek API Key，与普通模式自动翻译开关无关。

工具条可重新框选或停止，托盘也可停止。重新框选时按 Esc 恢复原区域。
普通框选和原快捷键保持原用途，启动时会结束持续模式。仅支持一个固定选区，
不跟随应用移动；显示器布局或缩放改变后需要重新框选。
截图只在本机内存中处理，仅识别文字发送至 DeepSeek。

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
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

也可以继续直接运行 `.venv\Scripts\python -m pytest`。测试脚本会使用项目虚拟环境，并在测试失败时返回失败状态。

## 便携构建

### GitHub 源码压缩包无法直接启动时

从 GitHub 的代码页下载 ZIP，得到的是源码，不是完整的 Windows 发行包。仓库中的 `dist/ScreenOCR/ScreenOCR.exe` 不能单独运行；完整便携版还需要同目录下的 `_internal` 运行文件和 OCR 模型。若启动时提示找不到 `dist/ScreenOCR/_internal/python313.dll`，说明下载内容缺少运行文件，并非单纯安装 Python 就能解决。

请先按下方命令从源码构建，再运行生成目录中的 `ScreenOCR.exe`。构建需要 Python 3.13，并会联网安装依赖及下载 OCR 模型。构建完成后请保留并分发整个 `dist/ScreenOCR` 目录，不要只复制 exe。也可以使用项目发布页面提供的完整安装包（如果有）。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

输出位于 `dist\ScreenOCR`。请分发整个目录；不要只复制其中的 exe，否则 Qt 运行库和离线模型会缺失。
构建前请退出正在从 `dist\ScreenOCR` 运行的旧版本，否则 Windows 会锁定其中的 DLL，构建脚本将以失败状态退出。

## DeepSeek 翻译

翻译使用 DeepSeek API，需要联网并消耗 DeepSeek 账户额度。在“设置”中填写 API Key；密钥会保存到当前 Windows 用户的凭据管理器，不会写入普通配置文件。

默认需要在识别结果中点击“翻译”。开启“识别后自动翻译为简体中文”后，每次 OCR 完成都会自动请求译文，修改原文后仍可点击“重新翻译”。应用只向 DeepSeek 发送文字，不会发送截图。

遇到临时网络故障、超时、请求限流或服务端错误时，翻译会自动退避重试，最多尝试 10 次（含首次请求），成功后立即返回译文，耗尽重试后才显示错误。API Key 无效、账户余额不足（HTTP 402）等错误会直接提示。网络持续不可用时，等待时间会相应延长。
