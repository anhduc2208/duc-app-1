from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

def create_pdf_from_text(text_file, pdf_file):
    # Create PDF
    c = canvas.Canvas(pdf_file, pagesize=A4)
    width, height = A4
    
    # Set font
    c.setFont("Helvetica", 12)
    
    # Split text into lines
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Write text to PDF
    y = height - inch  # Start from top with 1 inch margin
    for line in lines:
        if line.strip():  # Skip empty lines
            # If line starts with a section header, make it bold
            if any(header in line for header in ['NGUYỄN VĂN A', 'HỌC VẤN', 'KINH NGHIỆM', 'KỸ NĂNG', 'CHỨNG CHỈ', 'DỰ ÁN']):
                c.setFont("Helvetica-Bold", 14)
                y -= 20  # Add extra space before sections
            else:
                c.setFont("Helvetica", 12)
            
            # Write the line
            c.drawString(inch, y, line.strip())
            y -= 15  # Move down for next line
            
            # If we're near the bottom of the page, start a new page
            if y < inch:
                c.showPage()
                y = height - inch
                c.setFont("Helvetica", 12)
    
    # Save the PDF
    c.save()

if __name__ == '__main__':
    create_pdf_from_text('sample_resumes/nguyen_van_a_cv.txt', 'sample_resumes/nguyen_van_a_cv.pdf')
