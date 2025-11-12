from fpdf import FPDF

# ===== OMR generation additions =====
import sys
import math

# Create and configure the PDF before using it anywhere
pdf = FPDF()
pdf.set_auto_page_break(False)
pdf.add_page()
pdf.set_font("Arial", size=12)

def get_num_questions():
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            pass
    while True:
        try:
            return int(input("Enter number of questions: ").strip())
        except ValueError:
            print("Invalid number, try again.")

def get_institute_info():
    # Read from CLI flags if provided; otherwise prompt
    name = None
    logo = None
    qr = None
    for arg in sys.argv[1:]:
        if arg.startswith("--name="):
            name = arg.split("=", 1)[1]
        elif arg.startswith("--logo="):
            logo = arg.split("=", 1)[1]
        elif arg.startswith("--qr="):
            qr = arg.split("=", 1)[1]
    if not name:
        try:
            entered = input("Enter institute name (leave blank for default): ").strip()
            if entered:
                name = entered
        except Exception:
            pass
    if not name:
        name = "Your Institute Name"
    # ask for logo/qr only if not provided by flags
    if logo is None:
        try:
            entered = input("Optional logo path (leave blank to skip): ").strip()
            if entered:
                logo = entered
        except Exception:
            pass
    if qr is None:
        try:
            entered = input("Optional QR image path (leave blank to skip): ").strip()
            if entered:
                qr = entered
        except Exception:
            pass
    if logo == "":
        logo = None
    if qr == "":
        qr = None
    return name, logo, qr

num_questions = get_num_questions()
institute_name, logo_path, qr_path = get_institute_info()

# Style constants for a cleaner look
PRIMARY_DRAW = (0, 0, 0)
MUTED_TEXT = (90, 90, 90)
LIGHT_DRAW = (170, 170, 170)
BORDER_LINE_W = 0.6
THIN_LINE_W = 0.2
BUBBLE_LINE_W = 0.3
# Added extended palette
ACCENT_DRAW = (0, 60, 140)
BG_HEADER = (230, 235, 245)
BG_INFO = (245, 245, 245)
BG_INSTR = (240, 240, 240)

def apply_theme():
    pdf.set_draw_color(*PRIMARY_DRAW)
    pdf.set_text_color(*PRIMARY_DRAW)
    pdf.set_line_width(THIN_LINE_W)

# Layout settings
page_width, page_height = 210, 297  # A4 in mm
margin = 10
inner_width = page_width - 2 * margin
inner_height = page_height - 2 * margin
columns = 5
column_width = inner_width / columns
# Adjusted sizing for proper alignment
bubble_size = 4
bubble_gap = 2
number_width = 6
# Uniform vertical spacing (slightly tighter)
question_row_height = bubble_size + 5  # was bubble_size + 6
bubble_y_offset = 2  # vertical padding before drawing bubbles

# Options for each question (default A-E)
options = ["A", "B", "C", "D", "E"]

# New clearer group_width formula and centering
def get_column_start(col):
	# group_width is: number area + gap + bubbles (including internal gaps)
	group_width = number_width + 2 + (len(options) * bubble_size) + ((len(options) - 1) * bubble_gap)
	base = margin + col * column_width
	return base + max(0, (column_width - group_width) / 2), group_width

def get_bubble_x_positions(col):
    x_col_start, group_width = get_column_start(col)
    opt_start_x = x_col_start + number_width + 2
    positions = [opt_start_x + i * (bubble_size + bubble_gap) for i in range(len(options))]
    return x_col_start, positions

def draw_column_option_headers(start_y, cols):
    """
    Draw option letters (A, B, C, ...) above each bubble column header for the given
    number of columns used on the page.
    """
    pdf.set_font("Arial", size=8)
    apply_theme()
    # small vertical offset to position the header text above bubble centers
    header_y = start_y
    for col in range(cols):
        x_col_start, positions = get_bubble_x_positions(col)
        # draw each option centered over its bubble
        for i, opt in enumerate(options):
            px_center = positions[i] + bubble_size / 2.0
            text_w = pdf.get_string_width(opt)
            px = px_center - text_w / 2.0
            pdf.text(px, header_y, opt)

# Compute capacity per column (after template sets start_y)
# questions_per_column is computed later

# ---------- Header/template drawing (based on reference image) ----------
def draw_crop_marks():
    pdf.set_fill_color(0)
    r = 2
    # small corner dots inside border
    pdf.ellipse(5 + r, 5 + r, r, r, style='F')
    pdf.ellipse(205 - r, 5 + r, r, r, style='F')
    pdf.ellipse(5 + r, 292 - r, r, r, style='F')
    pdf.ellipse(205 - r, 292 - r, r, r, style='F')

ROLL_DIGITS = 7  # number of roll number digit positions (boxes / columns)
def draw_roll_grid(x, y):
    # Layout constants
    box_w = 8.0
    box_h = 8.0
    box_gap = 1.0
    circle_d = 4.2
    row_step = 6.0
    label_gap = 2.0
    top_gap = 2.0
    padding = 3.0
    label_h = 5.0        # new: vertical space for "ROLL NO." inside block
    rows_digits = [str(d) for d in range(1, 10)] + ['0']

    # Label width (extra padding for visual alignment)
    pdf.set_font("Arial", size=8)
    label_width = pdf.get_string_width('0') + label_gap + 2.0

    # Boxes start below the label area now
    boxes_y = y + label_h

    # Draw title inside block above boxes
    pdf.set_font("Arial", "B", 9)
    pdf.set_draw_color(*LIGHT_DRAW)
    pdf.set_text_color(0, 0, 0)
    pdf.text(x, y + 3, "ROLL NO.")

    # Draw top boxes
    pdf.set_line_width(THIN_LINE_W)
    for i in range(ROLL_DIGITS):
        bx = x + i * (box_w + box_gap)
        pdf.rect(bx, boxes_y, box_w, box_h)

    # Grid origin (top of first circle row)
    grid_top = boxes_y + box_h + top_gap

    # Width/height of circle grid
    grid_width = label_width + ROLL_DIGITS * (circle_d + box_gap) - box_gap
    grid_height = len(rows_digits) * row_step

    # Rows (labels + circles)
    pdf.set_line_width(BUBBLE_LINE_W)
    for r, digit in enumerate(rows_digits):
        row_y_top = grid_top + r * row_step
        pdf.set_font("Arial", size=8)
        pdf.text(x + 2.0, row_y_top + circle_d / 2 + 1.2, digit)
        for c in range(ROLL_DIGITS):
            cx = x + label_width + c * (circle_d + box_gap)
            pdf.ellipse(cx, row_y_top, circle_d, circle_d)

    # Block outline sizing (include label area)
    boxes_total_w = ROLL_DIGITS * (box_w + box_gap) - box_gap
    content_w = max(boxes_total_w + label_width, grid_width)
    block_w = content_w + 2 * padding
    block_h = label_h + box_h + top_gap + grid_height + 2 * padding
    block_x = x - padding
    block_y = y - padding

    pdf.set_draw_color(*LIGHT_DRAW)
    pdf.set_line_width(THIN_LINE_W)
    pdf.rect(block_x, block_y, block_w, block_h)

    pdf.set_draw_color(*PRIMARY_DRAW)
    pdf.set_text_color(0, 0, 0)
    return block_w, block_h

def draw_info_boxes(x, y, w):
    # Shaded boxes for cleaner appearance
    pdf.set_line_width(THIN_LINE_W)
    h = 8
    pdf.set_font("Arial", size=10)
    labels = ["Name:", "Date:", "Center Code:"]
    for i, lbl in enumerate(labels):
        yy = y + i * (h + 2)
        pdf.set_fill_color(*BG_INFO)
        pdf.rect(x, yy, w, h, style="DF")
        pdf.text(x + 2, yy + h - 2, lbl)
    yy = y + len(labels) * (h + 2)
    pdf.set_fill_color(*BG_INFO)
    pdf.rect(x, yy, w, h + 8, style="DF")
    pdf.text(x + 2, yy + h - 2, "Candidate Signature:")
    yy2 = yy + h + 10
    instr_h = 24
    pdf.set_fill_color(*BG_INSTR)
    pdf.rect(x, yy2, w, instr_h, style="DF")
    pdf.set_font("Arial", size=9)
    pdf.set_xy(x + 3, yy2 + 3)
    pdf.multi_cell(
        w - 6,
        4,
        "Instructions:\n"
        "* Use blue/black pen - fill one bubble only.\n"
        "* Do not make stray marks / fold sheet.\n"
        "* Fill Roll No. boxes and darken circles.\n"
        "* Check that all bubbles are fully filled."
    )
    apply_theme()
    total_h = (len(labels) * (h + 2)) + (h + 10) + instr_h
    return total_h

def draw_header_and_boxes():
    # Optional logo
    if logo_path:
        try:
            pdf.image(logo_path, x=margin, y=margin - 3, h=14)
        except Exception:
            pass

    # Title ribbon (kept, but increase ribbon_h slightly and space below)
    ribbon_h = 16
    pdf.set_fill_color(*BG_HEADER)
    pdf.rect(margin, margin - 4, inner_width, ribbon_h, style="F")
    pdf.set_font("Arial", "B", 15)
    pdf.set_text_color(*ACCENT_DRAW)
    pdf.set_xy(margin, margin - 2)
    pdf.cell(inner_width, 7, institute_name, 0, 2, "C")
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*MUTED_TEXT)
    pdf.cell(inner_width, 6, "OMR ANSWER SHEET", 0, 2, "C")
    apply_theme()

    # Increase top_y to leave extra breathing room under ribbon/QR/logo
    left_x = margin
    top_y = margin + ribbon_h + 6
    grid_w, grid_h = draw_roll_grid(left_x, top_y)

    gap = 8
    right_x = left_x + grid_w + gap
    right_w = inner_width - (grid_w + gap)
    # ensure right_w is not negative
    if right_w < 40:
        right_w = max(40, inner_width - grid_w - gap)

    info_h = draw_info_boxes(right_x, top_y, right_w)

    header_h = max(grid_h, info_h) + 6
    return margin + ribbon_h + header_h

def draw_qr_bottom():
    if qr_path:
        try:
            qr_max_w = 26
            qr_max_h = 26
            # Border starts at (5,5) with size 200x287
            pad = 3
            qr_x = 5 + 200 - qr_max_w - pad
            qr_y = 5 + 287 - qr_max_h - pad
            pdf.image(qr_path, x=qr_x, y=qr_y, w=qr_max_w, h=qr_max_h)
            pdf.set_draw_color(*LIGHT_DRAW)
            pdf.set_line_width(THIN_LINE_W)
            pdf.rect(qr_x - 1.5, qr_y - 1.5, qr_max_w + 3, qr_max_h + 3)
            apply_theme()
        except Exception:
            pass

def draw_static_page_template():
    pdf.set_draw_color(*PRIMARY_DRAW)
    pdf.set_line_width(BORDER_LINE_W)
    pdf.rect(x=5, y=5, w=200, h=287)
    draw_crop_marks()
    y_questions_start = draw_header_and_boxes()
    draw_qr_bottom()
    return y_questions_start + 4

# ---------- Question drawing ----------
def draw_question(q_index, col, row, start_y):
	# ensure font is set before measurements
	pdf.set_font("Arial", size=8)
	x_col_start, positions = get_bubble_x_positions(col)
	y = start_y + row * question_row_height
	bubble_top = y + bubble_y_offset
	num_text = f"{q_index}."
	tw = pdf.get_string_width(num_text)
	# vertical center of number aligned to bubble center (small tweak)
	pdf.text(x_col_start + number_width - tw, bubble_top + bubble_size / 2 + 0.4, num_text)
	pdf.set_line_width(BUBBLE_LINE_W)
	for bx in positions:
		pdf.set_draw_color(*ACCENT_DRAW)
		pdf.ellipse(bx, bubble_top, bubble_size, bubble_size)
	# restore theme styling for subsequent text
	apply_theme()

# ---- Build pages (sequential fill; consistent rows per column) ----
q = 1
while q <= num_questions:
    start_y = draw_static_page_template()
    max_rows = int((page_height - start_y - margin) / question_row_height)
    if max_rows < 1:
        break
    remaining = num_questions - q + 1
    questions_this_page = min(remaining, max_rows * columns)
    cols_used = min(columns, math.ceil(questions_this_page / max_rows))
    draw_column_option_headers(start_y + bubble_y_offset - 3, cols_used)
    for i in range(questions_this_page):
        col = i // max_rows
        row = i % max_rows
        draw_question(q + i, col, row, start_y)
    q += questions_this_page
    if q <= num_questions:
        pdf.add_page()

# ===== end OMR additions =====

# Output PDF file
pdf.output("output.pdf")
