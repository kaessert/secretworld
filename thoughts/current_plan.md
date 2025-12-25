# Implementation Plan: Stylized Borders and Frames

## Summary
Create a centralized `frames.py` module with reusable border/frame utilities to replace ad-hoc border code across the codebase. This provides consistent UI presentation for dream sequences, world events, combat announcements, and other dramatic moments.

## Spec

A new `src/cli_rpg/frames.py` module providing:

1. **FrameStyle enum** - Frame character sets:
   - `DOUBLE` - Double-line box (`╔═╗║╚╝`) for major announcements (world events, boss encounters)
   - `SINGLE` - Single-line box (`┌─┐│└┘`) for standard UI (map already uses this)
   - `SIMPLE` - ASCII equals/dashes (`═══`) for subtle framing (dreams)

2. **frame_text()** function - Main framing utility:
   - Parameters: `text: str`, `style: FrameStyle`, `width: Optional[int]`, `title: Optional[str]`, `color: Optional[str]`
   - Auto-wraps text to width, pads lines, applies frame characters
   - Returns framed string (does NOT print - caller decides printing method)

3. **Convenience functions** for common patterns:
   - `frame_announcement(text, title)` - Double frame, gold color (world events)
   - `frame_dream(text)` - Simple frame, magenta color (dreams)
   - `frame_combat_intro(text)` - Double frame, red color (boss fights, shadow creature)

## Test File: `tests/test_frames.py`

### FrameStyle tests
- `test_frame_styles_have_required_characters()` - Each style has top/bottom/left/right/corners

### frame_text() tests
- `test_frame_text_wraps_single_line()` - Short text fits in frame
- `test_frame_text_wraps_multiline()` - Long text wraps correctly
- `test_frame_text_with_title()` - Title appears in top border
- `test_frame_text_with_custom_width()` - Respects width parameter
- `test_frame_text_with_color()` - Color codes applied to frame chars
- `test_frame_text_without_color()` - Works when colors disabled
- `test_frame_text_double_style()` - Uses `╔═╗║╚╝` chars
- `test_frame_text_single_style()` - Uses `┌─┐│└┘` chars
- `test_frame_text_simple_style()` - Uses `═` horizontal lines only

### Convenience function tests
- `test_frame_announcement_uses_double_gold()` - Double style, gold color
- `test_frame_dream_uses_simple_magenta()` - Simple style, magenta color
- `test_frame_combat_intro_uses_double_red()` - Double style, red color

### Integration tests
- `test_frame_with_ansi_color_in_text()` - Colored text inside frame aligns correctly

## Implementation Steps

1. **Create `src/cli_rpg/frames.py`**:
   - Import `FrameStyle` enum with DOUBLE, SINGLE, SIMPLE
   - Import `textwrap` for word wrapping
   - Import `colors` module for colorization
   - Implement `frame_text()` with text wrapping, padding, and framing logic
   - Implement convenience functions

2. **Create `tests/test_frames.py`**:
   - Test all frame styles produce valid output
   - Test text wrapping and alignment
   - Test color integration
   - Test edge cases (empty text, very long text)

3. **Refactor `dreams.py`**:
   - Replace manual `"═" * 40` border with `frame_dream()` call
   - Update `format_dream()` to use new framing utility

4. **Refactor `world_events.py`**:
   - Replace manual `"=" * width` border in `format_event_notification()` with `frame_announcement()`

5. **Refactor `shadow_creature.py`**:
   - Replace manual `"=" * 50` border with `frame_combat_intro()`

6. **Update ISSUES.md**:
   - Mark "Stylized borders and frames for different UI elements" as MVP IMPLEMENTED

## File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/frames.py` | New file - frame utilities |
| `tests/test_frames.py` | New file - tests for frames module |
| `src/cli_rpg/dreams.py` | Refactor to use `frame_dream()` |
| `src/cli_rpg/world_events.py` | Refactor to use `frame_announcement()` |
| `src/cli_rpg/shadow_creature.py` | Refactor to use `frame_combat_intro()` |
| `ISSUES.md` | Mark feature as implemented |
