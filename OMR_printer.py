from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# Draw border for the whole page
pdf.rect(x=5, y=5, w=200, h=287)  # A4 page: 210x297mm, leaving 5mm margin

# Output PDF file
pdf.output("output.pdf")
