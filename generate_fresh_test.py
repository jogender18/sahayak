import os
import shutil
import fitz # PyMuPDF
from PIL import Image
from database import init_db, create_agreement, get_agreement
from pdf_generator import generate_agreement_pdf

init_db()

fresh_test_data = {
    "owner_name": "Anil Sharma (Sharma Interiors)",
    "owner_phone": "+91 98111 22334",
    "worker_name": "Devendra Kumar (Master Carpenter)",
    "worker_phone": "+91 98222 33445",
    "work_description": "Full custom modular kitchen woodwork, cabinet fabrication, and laminate installation.",
    "wage_amount": "1200",
    "wage_unit": "per day",
    "payment_schedule": "weekly",
    "late_penalty": "Rs. 200 per day late compensation if payment is not cleared by Saturday evening.",
    "start_date": "2026-09-05",
    "duration": "8 Days",
    "work_location": "Flat 502, Skyline Towers, Sector 48, Gurgaon",
}

agreement_id = create_agreement(fresh_test_data)
print(f"Created fresh agreement ID: {agreement_id}")

agreement = get_agreement(agreement_id)

# Read public base url
public_url_file = os.path.join(os.path.dirname(__file__), "public_url.txt")
base_url = "http://127.0.0.1:5000"
if os.path.exists(public_url_file):
    with open(public_url_file, "r") as f:
        val = f.read().strip()
        if val.startswith("http"):
            base_url = val

verify_url = f"{base_url}/verify/{agreement_id}"
print(f"Public verify URL: {verify_url}")

# Generate PDF
pdf_buffer = generate_agreement_pdf(agreement, verify_url)
pdf_path = os.path.join(os.path.dirname(__file__), "fresh_wage_agreement_anil_devendra.pdf")
with open(pdf_path, "wb") as f:
    f.write(pdf_buffer.getvalue())

# Render high-resolution full page (200 DPI for ultra sharpness)
doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(dpi=200)
full_png_path = os.path.join(os.path.dirname(__file__), "fresh_pdf_anil_devendra_full.png")
pix.save(full_png_path)
print(f"Saved full page image: {full_png_path}")

# Load rendered image with PIL to create precise zoomed-in crops
img = Image.open(full_png_path)
width, height = img.size

# 1. Zoomed crop of Section 3 (WAGE AND PAYMENT) & Section 4 (PENALTY)
# Approximate vertical bounds: 33% to 54% of page height
box_wage = (int(width * 0.05), int(height * 0.33), int(width * 0.95), int(height * 0.52))
crop_wage = img.crop(box_wage)
wage_zoom_path = os.path.join(os.path.dirname(__file__), "fresh_pdf_wage_section_zoomed.png")
crop_wage.save(wage_zoom_path)
print(f"Saved wage section zoom: {wage_zoom_path}")

# 2. Zoomed crop of Section 6 (SIGNATURES, QR CODE & PUBLIC FOOTER)
# Approximate vertical bounds: 65% to 100% of page height
box_footer = (int(width * 0.05), int(height * 0.63), int(width * 0.95), int(height * 0.98))
crop_footer = img.crop(box_footer)
footer_zoom_path = os.path.join(os.path.dirname(__file__), "fresh_pdf_qr_footer_zoomed.png")
crop_footer.save(footer_zoom_path)
print(f"Saved QR and footer zoom: {footer_zoom_path}")

# Copy all 3 newly generated images to the brain directory
BRAIN_DIR = r"C:\Users\Rohit\.gemini\antigravity\brain\3d00a79a-8174-4a9e-89ef-0ec63ff87fa2"
shutil.copy2(full_png_path, os.path.join(BRAIN_DIR, "fresh_pdf_anil_devendra_full.png"))
shutil.copy2(wage_zoom_path, os.path.join(BRAIN_DIR, "fresh_pdf_wage_section_zoomed.png"))
shutil.copy2(footer_zoom_path, os.path.join(BRAIN_DIR, "fresh_pdf_qr_footer_zoomed.png"))

print("All fresh images successfully created and copied to brain directory!")
