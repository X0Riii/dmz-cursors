#!/usr/bin/env python3
"""Generate a preview image showing all DMZ cursor shapes."""
import cairo
import gi
import os

gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

# Assumes this script lives in the "build" directory of the repository.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(REPO, 'white', 'cursors_scalable')

# Logical order of cursor shapes for the preview
NAMES = [
    'default', 'pointer', 'text', 'vertical-text',
    'crosshair', 'cell', 'help', 'wait',
    'progress', 'move', 'all-scroll', 'all-resize',
    'n-resize', 's-resize', 'e-resize', 'w-resize',
    'ne-resize', 'nw-resize', 'se-resize', 'sw-resize',
    'ew-resize', 'ns-resize', 'nesw-resize', 'nwse-resize',
    'col-resize', 'row-resize', 'not-allowed', 'no-drop',
    'grab', 'grabbing', 'copy', 'alias',
    'dnd-ask', 'context-menu', 'zoom-in', 'zoom-out',
    'X_cursor',
]

COLS = 8
CELL_W = 96
CELL_H = 68
CURSOR = 40
FONT_SIZE = 9

rows = (len(NAMES) + COLS - 1) // COLS
W = COLS * CELL_W
H = rows * CELL_H

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surface)

# Background
ctx.set_source_rgb(0.98, 0.98, 0.98)
ctx.paint()

ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL,
                     cairo.FONT_WEIGHT_NORMAL)

for i, name in enumerate(NAMES):
    col = i % COLS
    row = i // COLS
    x0 = col * CELL_W
    y0 = row * CELL_H

    # Optional: light cell separator
    if col > 0:
        ctx.set_source_rgb(0.92, 0.92, 0.92)
        ctx.set_line_width(1)
        ctx.move_to(x0, y0)
        ctx.line_to(x0, y0 + CELL_H)
        ctx.stroke()

    # Render the cursor SVG
    svg_path = os.path.join(THEME, name, name + '.svg')
    handle = Rsvg.Handle.new_from_file(svg_path)
    cx = x0 + (CELL_W - CURSOR) / 2
    cy = y0 + 8
    viewport = Rsvg.Rectangle()
    viewport.x = cx
    viewport.y = cy
    viewport.width = CURSOR
    viewport.height = CURSOR
    handle.render_document(ctx, viewport)

    # Draw the label
    ctx.set_source_rgb(0.25, 0.25, 0.25)
    ctx.set_font_size(FONT_SIZE)
    ext = ctx.text_extents(name)
    lx = x0 + (CELL_W - ext[2]) / 2 - ext[0]
    ly = cy + CURSOR + 14
    ctx.move_to(lx, ly)
    ctx.show_text(name)

out_path = os.path.join(REPO, 'preview.png')
surface.write_to_png(out_path)
print(f'Wrote {out_path} ({W}x{H})')
