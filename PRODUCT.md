# Product

<!-- impeccable:product-schema 1 -->

## Platform

windows

## Stack

Delegated: Python 3.13, PySide6 Qt Widgets, PaddleOCR/PaddlePaddle, and PyInstaller on 64-bit Windows. The user chose code-first delivery.

## Users

The primary user is the owner of the application, using it personally on a Windows desktop to extract text visible in other applications.

## Product Purpose

Capture a user-drawn region of the current display, recognize its text locally, copy it to the clipboard, and make it available for quick correction. Success means the workflow is reachable globally, does not upload screenshots, and remains usable across common Windows display scales.

## Positioning

The tool combines a low-friction Windows screen-selection workflow with offline OCR for Simplified Chinese, Traditional Chinese, English, Japanese, and Korean, while keeping translation as a provider-neutral future pipeline stage.

## Operating Context

The application runs as a Windows tray utility. The user starts capture from Ctrl+Shift+S or the main window, drags with the left mouse button on one display, and receives editable text that is copied automatically.

## Capabilities and Constraints

- One-display-per-capture selection; any connected display may be used.
- Offline OCR and in-memory screenshots only.
- Global hotkey, system tray, optional per-user login startup, configurable automatic copy.
- Plain-text reading order rather than layout reconstruction.
- Translation, history, cloud sync, tables, specialist handwriting, and cross-display selections are outside v1.
- Future translation targets Simplified Chinese (`zh-Hans`) through an asynchronous provider interface.

## Evidence on Hand

No brand assets, benchmark corpus, or external claims were supplied. The application must not fabricate recognition accuracy claims.

## Product Principles

- Capture should feel immediate from any application.
- Private screen content stays on the machine.
- Original OCR text remains available even when later pipeline stages fail.
- Failure states explain what can be retried or changed.
- Future translation providers must not couple to capture or OCR UI code.

## Accessibility & Inclusion

Use keyboard-reachable controls, visible focus, readable contrast, and Windows scaling support. Escape always cancels capture.
