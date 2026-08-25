---
name: Screen OCR
description: A quiet Windows utility for local screen capture and editable OCR results.
colors:
  action-blue: "#2563EB"
  action-blue-hover: "#1D4ED8"
  action-blue-pressed: "#1E40AF"
  action-blue-soft: "#E7EEFF"
  canvas: "#F7F8FA"
  surface: "#FFFFFF"
  utility-panel: "#EEF1F6"
  text-strong: "#101828"
  text-body: "#172033"
  text-muted: "#536078"
  text-status: "#344054"
  action-blue-ink: "#1746A2"
  border: "#C9D1DF"
  border-hover: "#AAB6C8"
  border-input: "#BEC8D8"
  error: "#B42318"
  success: "#18794E"
  selection-fill: "#BFDBFE"
  selection-text: "#102A56"
  capture-scrim: "rgba(8, 15, 28, 0.62)"
  capture-label: "rgba(15, 23, 42, 0.92)"
  capture-outline: "#60A5FA"
typography:
  headline:
    fontFamily: "Microsoft YaHei UI, Microsoft YaHei, sans-serif"
    fontSize: "27px"
    fontWeight: 650
  title:
    fontFamily: "Microsoft YaHei UI, Microsoft YaHei, sans-serif"
    fontSize: "21px"
    fontWeight: 650
  body:
    fontFamily: "Microsoft YaHei UI, Microsoft YaHei, sans-serif"
    fontSize: "14px"
    fontWeight: 400
  label:
    fontFamily: "Microsoft YaHei UI, Microsoft YaHei, sans-serif"
    fontSize: "14px"
    fontWeight: 600
rounded:
  compact: "6px"
  control: "9px"
  overlay-hint: "10px"
  panel: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  control-y: "9px"
  field: "10px"
  dialog: "14px"
  panel-x: "16px"
  section: "18px"
  window: "24px"
  main-window: "32px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 15px"
  button-primary-hover:
    backgroundColor: "{colors.action-blue-hover}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
  button-primary-pressed:
    backgroundColor: "{colors.action-blue-pressed}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-body}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 15px"
  text-editor:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-strong}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "10px"
  shortcut-badge:
    backgroundColor: "{colors.action-blue-soft}"
    textColor: "#1746A2"
    typography: "{typography.label}"
    rounded: "{rounded.compact}"
    padding: "5px 9px"
---

# Design System: Screen OCR

## Overview

**Creative North Star: "The Quiet Capture Instrument"**

Screen OCR is a compact, code-led Windows utility whose interface recedes behind a single job: frame text, recognize it locally, and return an editable result. Its visual language is calm and native-adjacent rather than branded or promotional—light neutral ground, dark readable type, compact controls, and one bright blue action channel.

The working windows remain flat and low-noise. Capture mode deliberately reverses that restraint: a translucent navy scrim turns the desktop into a spotlight surface, while a crisp blue outline identifies the live selection. High-contrast mode is not restyled; the application defers to the Windows system theme so user-selected colors and control treatments remain authoritative.

**Key Characteristics:**

- Compact, task-first Windows utility density.
- Bright blue reserved for capture, confirmation, selection, and keyboard focus.
- Flat neutral surfaces separated by tone and fine borders rather than decoration.
- Microsoft YaHei UI throughout for consistent Chinese and Latin rendering.
- A screen-spotlight overlay that preserves context while isolating the capture region.

## Colors

The palette pairs cool, nearly white surfaces with ink-like navy text and a focused Windows blue accent.

### Primary

- **Capture Blue:** The sole action color, used for the main capture and copy buttons, keyboard focus borders, the app icon, and capture-selection feedback.
- **Deep Capture Blue:** Darker hover and pressed states keep the primary action unmistakable without adding effects.
- **Shortcut Wash:** A pale blue field marks shortcut values and selected menu items without competing with the primary action.

### Neutral

- **Quiet Canvas:** The uninterrupted application and dialog background.
- **Clean Surface:** Inputs, menus, and secondary controls sit on white for precise separation from the canvas.
- **Utility Mist:** The shortcut information panel groups reference content by tone rather than by a card shadow.
- **Ink:** Used for titles and editable text where legibility is most important.
- **Slate Body:** The default body color; muted slate carries supporting text and metadata.
- **Cool Hairline:** A fine boundary for controls and fields.
- **Capture Navy:** The desktop-dimming scrim and measurement/hint labels during region selection.

### Named Rules

**The One Action Color Rule.** Bright blue communicates capture, copy, selection, or focus; it is not general decoration.

**The System Contrast Rule.** When Windows high-contrast mode is active, omit the custom palette and allow the system theme to render the interface.

## Typography

**Display Font:** Microsoft YaHei UI (with Microsoft YaHei and sans-serif fallbacks)  
**Body Font:** Microsoft YaHei UI (with Microsoft YaHei and sans-serif fallbacks)

**Character:** The single-family system is practical, compact, and bilingual by default. Weight and size create hierarchy; ornamental type treatments are absent.

### Hierarchy

- **Headline** (650, 27px): Main-window task statement.
- **Title** (650, 21px): Dialog headings such as the recognition result.
- **Body** (400, 14px): Supporting copy, status, metadata, editor content, and capture guidance.
- **Label** (600, 14px): Buttons, field labels, and shortcut values.

### Named Rules

**The One Family Rule.** Keep all interface copy in Microsoft YaHei UI; express hierarchy through size, weight, color, and placement.

## Layout

The application uses single-column native Qt layouts and fixed working-window proportions instead of a responsive web grid. The main window opens at 520 × 360 pixels with a 460 × 330 minimum, 32-pixel side margins, and an 18-pixel vertical rhythm. Its full-width 52-pixel capture button is the dominant control; shortcut and status information follow in reading order, while Settings settles at the lower-right edge.

The result dialog opens at 680 × 620 pixels with 24-pixel side margins and a 14-pixel rhythm. The editable original text area absorbs available height until translation is requested; then a separate editable Simplified Chinese area appears below it. Recapture and Translate stay left as alternate paths; Close and the blue Copy action align right. The settings dialog uses a compact 420-pixel minimum width, 24-pixel margins, and the same 14-pixel rhythm.

Capture is bound to one display at a time. Its overlay fills that display, uses the crosshair cursor, and updates the selected rectangle continuously; Escape cancels. Windows display scaling is handled by translating the logical selection into screenshot pixels.

## Elevation & Depth

The working interface uses no custom shadows. Depth comes from tonal layering: white controls on the quiet canvas, the utility panel on a slightly darker neutral, and one-pixel control borders. Capture mode uses contrast rather than elevation—the darkened desktop, restored pixels inside the selection, and a blue outline make the active region read as a cutout.

### Named Rules

**The Flat Utility Rule.** Do not add card shadows or floating chrome to ordinary windows; use tone, borders, and spacing to organize the task.

## Shapes

Controls use gently rounded 9-pixel corners, compact badges and menu items use 6 pixels, information panels use 12 pixels, and the capture hint uses 10 pixels. The geometry remains restrained and rectangular: enough curvature to soften a desktop utility, never enough to appear pill-like. The app icon is the exception, using a larger rounded-square silhouette to remain legible in the Windows tray.

## Components

### Buttons

- **Shape:** Compact rounded rectangles (9px) with a one-pixel border and semibold label.
- **Primary:** Capture Blue with white text and 9 × 15-pixel internal padding. The main capture button expands to the content width and a minimum height of 52 pixels.
- **Hover / Focus:** Primary actions deepen on hover and press. Keyboard focus becomes a two-pixel blue border while compensating padding preserves the control size.
- **Secondary:** White surface, dark slate text, and a cool hairline border. Hover and press states shift to progressively darker neutral fills.
- **Disabled:** Muted text, neutral fill, and subdued border communicate temporary unavailability without reducing geometry.

### Cards / Containers

- **Shortcut Panel:** A 12-pixel rounded utility-neutral strip with 16-pixel horizontal and 13-pixel vertical padding; its label and shortcut badge sit at opposite ends.
- **Shortcut Badge:** A compact 6-pixel rounded blue wash with darker blue semibold text and 5 × 9-pixel padding.
- **Shadow Strategy:** None; tonal contrast provides grouping.

### Inputs / Fields

- **Style:** White fields use a one-pixel cool border, 9-pixel corners, and 10-pixel padding. The result is plain text only and remains directly editable.
- **Focus:** A two-pixel Capture Blue border replaces the default stroke; one pixel of padding is removed to prevent a layout jump.
- **Selection:** Selected editor text uses a pale blue fill and deep navy text.
- **Error / Disabled:** Error metadata is dark red. Disabled controls use muted text and cool gray surfaces.

### Menus

Tray menus use the white surface, a fine cool border, and compact 6-pixel item corners. Selection uses the same pale blue and blue-ink treatment as the shortcut badge. The information architecture stays native and concise: open, capture, settings, and quit.

### Capture Overlay

The overlay is a frameless, always-on-top, full-display tool surface. A translucent navy scrim dims the captured desktop; the selected rectangle restores the original screenshot beneath a two-pixel light-blue outline. Before dragging, a centered dark hint explains the left-button gesture and Escape cancellation. During dragging, a compact dark label reports selection width × height. Selections under 4 pixels in either dimension reset instead of submitting.

### Result Workspace

The result dialog combines a title, one-line OCR metadata, a flexible original-text editor, and a compact action footer. Recognized text is selected and focused when the dialog opens. Translation is progressive disclosure: the lower translation workspace remains absent in manual mode until requested, then shows a contained loading, success, or recoverable error state. Its editor is independently editable and copyable. Automatic mode opens the same workspace immediately, while the action becomes “Translate again” after completion. Recapture preserves the workflow escape hatch, original Copy remains the primary completion action, and Close remains secondary.

## Do's and Don'ts

### Do:

- **Do** keep the capture or completion action visually dominant with the established blue hierarchy.
- **Do** preserve editable original OCR text and the visible recapture path even when translation is loading or fails.
- **Do** keep translation visually subordinate to the original and disclose when recognized text is sent online.
- **Do** use compact native controls, keyboard focus borders, and Escape cancellation.
- **Do** preserve the screen-spotlight treatment: dark context, restored selection, blue outline, and live dimensions.
- **Do** defer completely to Windows when high-contrast mode is active.
- **Do** reserve a clear future location for translation results without adding translation controls or claims before the feature ships.

### Don't:

- **Don't** introduce decorative gradients, shadows, oversized cards, or multiple accent colors.
- **Don't** use blue as ambient ornament; it must indicate action, selection, or focus.
- **Don't** replace Microsoft YaHei UI with a web font or a Latin-first display face.
- **Don't** reconstruct document layout inside the result editor; the shipped result is editable plain text.
- **Don't** style over Windows high-contrast preferences.
- **Don't** imply that screenshots are sent to DeepSeek or claim universal translation accuracy.
