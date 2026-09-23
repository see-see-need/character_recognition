# Product

<!-- impeccable:product-schema 1 -->

## Platform

windows

## Stack

Delegated: Python 3.13, PySide6 Qt Widgets, PaddleOCR/PaddlePaddle, and PyInstaller on 64-bit Windows. The user chose code-first delivery.

## Users

The primary user is the owner of the application, using it personally on a Windows desktop to extract text visible in other applications.

## Product Purpose

Capture a user-drawn region of the current display, recognize its text locally, copy it to the clipboard, make it available for quick correction, and optionally translate the corrected text to Simplified Chinese. A separate continuous translation mode keeps reading one fixed region and displays Simplified Chinese alongside the unchanged screen content. Success means the workflow is reachable globally, never uploads screenshots, and remains usable across common Windows display scales.

## Positioning

The tool combines a low-friction Windows screen-selection workflow with offline OCR for Simplified Chinese, Traditional Chinese, English, Japanese, and Korean, plus an optional DeepSeek-backed Simplified Chinese translation stage.

## Operating Context

The application runs as a Windows tray utility. The user starts capture from Ctrl+Shift+S or the main window, drags with the left mouse button on one display, and receives editable text that is copied automatically.

Continuous translation has its own main-window and tray entry. The user selects one fixed region; a transparent frame and translation overlay leave the screen original visible and accept mouse input through to the application beneath. A separate interactive toolbar provides pagination, recapture, and stop; the tray also provides stop. This mode opens no result editor, offers no source editing, and never automatically copies text. Starting ordinary capture or its existing hotkey ends continuous mode. Cancelling a continuous recapture with Escape resumes the previous region. Continuous sessions are not restored after restarting the application.

## Capabilities and Constraints

- One-display-per-capture selection; any connected display may be used.
- Offline OCR and in-memory screenshots only.
- Global hotkey, system tray, optional per-user login startup, configurable automatic copy.
- Plain-text reading order rather than layout reconstruction.
- Translation targets Simplified Chinese (`zh-Hans`) through an asynchronous provider interface; only recognized text is sent to DeepSeek.
- Translation can be manual or automatic, while history, cloud sync, tables, specialist handwriting, and cross-display selections remain outside scope.
- Continuous mode always translates automatically, independently of the ordinary automatic-translation setting, and requires a configured DeepSeek API key. It monitors every 500 ms, submits after two stable samples or at most 2 seconds of continuous change, and does not repeat translation for unchanged recognized text. New recognized text cancels obsolete translation work; only the latest pending OCR region is retained.
- Continuous mode supports one fixed region, without following an application as it moves. Display layout or scale changes stop the session and require recapture. Temporary translation failures retry after 30 seconds once provider retries are exhausted; credential or balance errors wait for settings to be saved.

## Evidence on Hand

No brand assets, benchmark corpus, or external claims were supplied. The application must not fabricate recognition accuracy claims.

The continuous overlay review supports shipping within the offscreen layout and legibility scope only. Native mouse interaction, display scaling, and capture exclusion remain unverified on Windows; no detector ran the native Python application. These are verification limits, not additional product guarantees.

## Product Principles

- Capture should feel immediate from any application.
- Private screen content stays on the machine.
- In ordinary capture, original OCR text remains available and editable even when translation fails. In continuous mode, preserve the original screen content and keep the overlay non-editable.
- Failure states explain what can be retried or changed.
- Future translation providers must not couple to capture or OCR UI code.

## Accessibility & Inclusion

Use keyboard-reachable controls, visible focus, readable contrast, and Windows scaling support. Escape always cancels capture.
