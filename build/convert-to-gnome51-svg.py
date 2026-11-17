#!/usr/bin/env python3
"""تحويل سمة DMZ النقطية إلى صيغة SVG الجديدة التي يتطلبها GNOME Shell 51."""
import os, struct, zlib, base64, json

XCURSOR_IMAGE_TYPE = 0xfffd0002
NOMINAL_SIZE = 24

def parse_xcursor(path):
    data = open(path, 'rb').read()
    magic, hlen, version, ntoc = struct.unpack('<IIII', data[:16])
    images = []
    off = 16
    for _ in range(ntoc):
        typ, subtype, pos = struct.unpack('<III', data[off:off+12]); off += 12
        if typ != XCURSOR_IMAGE_TYPE:
            continue
        ih = struct.unpack('<IIIIIIIII', data[pos:pos+36])
        w, h = ih[4], ih[5]
        xhot, yhot = ih[6], ih[7]
        npx = w * h
        pixels = data[pos+36:pos+36+npx*4]
        rgba = bytearray()
        for i in range(npx):
            # ملف Xcursor: بايتات [B,G,R,A] -> PNG: [R,G,B,A]
            b = pixels[4*i]; g = pixels[4*i+1]; r = pixels[4*i+2]; a = pixels[4*i+3]
            rgba += bytes((r, g, b, a))
        images.append((subtype, w, h, xhot, yhot, bytes(rgba)))
    return images

def make_png(width, height, rgba):
    def chunk(typ, data):
        c = typ + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)  # filter byte
        raw += rgba[y*stride:(y+1)*stride]
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')

def make_svg(png_bytes, size):
    b64 = base64.b64encode(png_bytes).decode()
    return ('<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<image width="{size}" height="{size}" xlink:href="data:image/png;base64,{b64}"/>'
            '</svg>')

# الاسم الحديث (الذي يطلبه GNOME) -> ملف DMZ الحقيقي
MAPPING = {
    'default': 'left_ptr', 'text': 'xterm', 'pointer': 'hand2',
    'move': 'move', 'wait': 'watch', 'crosshair': 'crosshair',
    'help': 'question_arrow', 'not-allowed': 'crossed_circle',
    'no-drop': 'dnd-none', 'grab': 'grabbing', 'grabbing': 'grabbing',
    'cell': 'plus', 'copy': 'copy', 'alias': 'dnd-link',
    'context-menu': 'left_ptr', 'vertical-text': 'xterm',
    'all-scroll': 'move', 'all-resize': 'move', 'dnd-ask': 'dnd-ask',
    'progress': 'left_ptr_watch', 'X_cursor': 'X_cursor',
    'n-resize': 'top_side', 's-resize': 'bottom_side',
    'e-resize': 'right_side', 'w-resize': 'left_side',
    'ne-resize': 'top_right_corner', 'nw-resize': 'top_left_corner',
    'se-resize': 'bottom_right_corner', 'sw-resize': 'bottom_left_corner',
    'ew-resize': 'sb_h_double_arrow', 'ns-resize': 'sb_v_double_arrow',
    'nesw-resize': 'fd_double_arrow', 'nwse-resize': 'bd_double_arrow',
    'col-resize': 'sb_h_double_arrow', 'row-resize': 'sb_v_double_arrow',
    'zoom-in': 'crosshair', 'zoom-out': 'crosshair',
}

def convert_theme(theme_name):
    icons_dir = os.path.expanduser(f'~/.local/share/icons/{theme_name}')
    cursors_dir = os.path.join(icons_dir, 'cursors')
    scalable_dir = os.path.join(icons_dir, 'cursors_scalable')
    created = 0
    for name, target in MAPPING.items():
        target_path = os.path.realpath(os.path.join(cursors_dir, target))
        if not os.path.isfile(target_path):
            print(f'  [{theme_name}] مفقود: {target} (لـ {name})')
            continue
        images = parse_xcursor(target_path)
        img = next((im for im in images if im[0] == NOMINAL_SIZE), None)
        if img is None:
            img = min(images, key=lambda im: abs(im[0] - NOMINAL_SIZE))
        subtype, w, h, xhot, yhot, rgba = img
        png = make_png(w, h, rgba)
        svg = make_svg(png, w)
        out_dir = os.path.join(scalable_dir, name)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f'{name}.svg'), 'w') as f:
            f.write(svg)
        meta = [{
            'filename': f'{name}.svg',
            'hotspot_x': float(xhot),
            'hotspot_y': float(yhot),
            'nominal_size': NOMINAL_SIZE,
        }]
        with open(os.path.join(out_dir, 'metadata.json'), 'w') as f:
            json.dump(meta, f, indent=4)
        created += 1
    print(f'{theme_name}: أُنشئ {created} مؤشر SVG')

if __name__ == '__main__':
    convert_theme('dmz-white')
    convert_theme('dmz-black')
    print('تم')
