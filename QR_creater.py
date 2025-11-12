import sys
import os
from datetime import datetime

# Try to import required libs; show installer hint if missing
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M, ERROR_CORRECT_L, ERROR_CORRECT_Q, ERROR_CORRECT_H
    from PIL import Image
except Exception as e:
    print("Missing dependency:", e)
    print("Install with: pip install qrcode[pil] pillow")
    sys.exit(1)

def parse_args():
    # Basic CLI support: python QR_creater.py "text" [out.png] [logo.png]
    text = None
    out = None
    logo = None
    if len(sys.argv) >= 2:
        text = sys.argv[1]
    if len(sys.argv) >= 3:
        out = sys.argv[2]
    if len(sys.argv) >= 4:
        logo = sys.argv[3]
    return text, out, logo

def prompt_if_none(text, out, logo):
    if not text:
        text = input("Enter QR content (text/URL): ").strip()
    if not out:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = f"qr_{ts}.png"
    if logo is None:
        logo_input = input("Optional logo path (leave blank to skip): ").strip()
        logo = logo_input if logo_input else None
    return text, out, logo

def choose_error_correction():
    # Let user choose or default to 'M'
    print("Choose error correction level: L (7%)  M (15%)  Q (25%)  H (30%)  [default M]")
    ch = input("Level: ").strip().upper()
    return {
        "L": ERROR_CORRECT_L,
        "M": ERROR_CORRECT_M,
        "Q": ERROR_CORRECT_Q,
        "H": ERROR_CORRECT_H
    }.get(ch, ERROR_CORRECT_M)

def create_qr(content, out_path, logo_path=None, box_size=20, border=5, ec_level=ERROR_CORRECT_M):
    qr = qrcode.QRCode(
        error_correction=ec_level,
        box_size=box_size,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # compute logo size (max 20% of QR width)
            qr_w, qr_h = img.size
            max_logo_w = int(qr_w * 0.20)
            max_logo_h = int(qr_h * 0.20)
            logo.thumbnail((max_logo_w, max_logo_h), Image.ANTIALIAS)

            # compute position and paste
            lx = (qr_w - logo.width) // 2
            ly = (qr_h - logo.height) // 2

            img_p = img.copy().convert("RGBA")
            img_p.paste(logo, (lx, ly), logo)
            img = img_p.convert("RGB")
        except Exception as e:
            print("Warning: failed to add logo:", e)

    img.save(out_path)
    return out_path

def main():
    text_arg, out_arg, logo_arg = parse_args()
    text, out, logo = prompt_if_none(text_arg, out_arg, logo_arg)

    # confirm options
    print("Output file:", out)
    if os.path.exists(out):
        resp = input("File exists — overwrite? (y/N): ").strip().lower()
        if resp != "y":
            print("Aborted.")
            return

    ec = choose_error_correction()
    # optional: let user choose size
    try:
        box_sz = int(input("Box size (pixels, default 20): ").strip() or "20")
    except Exception:
        box_sz = 20

    try:
        border = int(input("Border (modules, default 5): ").strip() or "5")
    except Exception:
        border = 5

    out_path = create_qr(text, out, logo_path=logo, box_size=box_sz, border=border, ec_level=ec)
    print("QR saved to:", out_path)

if __name__ == "__main__":
    main()
