import streamlit as st
from PIL import Image, ImageDraw
import pytesseract
import re
import cv2
import numpy as np

# --- IMPORTANT: TESSERACT PATH CONFIGURATION ---
# If you are on Windows, you might need to set the path to your Tesseract installation.
# Uncomment the line below and change the path to where you installed Tesseract.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program-Files\Tesseract-OCR\tesseract.exe'


# --- CORE PROCESSING FUNCTION ---

def process_and_redact_image(image):
    """
    This function takes an image, performs OCR to find text and its location,
    identifies PII using regex, and draws black boxes to redact it.
    """
    
    # Convert the PIL image to an OpenCV image for processing
    open_cv_image = np.array(image.convert('RGB'))
    
    # Use Pytesseract to get all data about text, including bounding boxes
    # This is more powerful than just getting the text string
    ocr_data = pytesseract.image_to_data(open_cv_image, output_type=pytesseract.Output.DICT)

    # These are the regex patterns to find PII. We'll keep it simple for the demo.
    # This pattern looks for a 12-digit number, possibly with spaces.
    aadhaar_pattern = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
    # This pattern looks for a typical Indian PAN card format.
    pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
    # This pattern is a simple way to find names for the demo.
    # It looks for "Name:" followed by two capitalized words.
    name_pattern = re.compile(r'Name\s?:\s?([A-Z][a-z]+)\s([A-Z][a-z]+)')

    redacted_image = image.copy()
    draw = ImageDraw.Draw(redacted_image)
    
    found_pii = []

    # Loop through every detected text element
    n_boxes = len(ocr_data['level'])
    for i in range(n_boxes):
        text = ocr_data['text'][i]
        
        # Check if the text matches any of our PII patterns
        if aadhaar_pattern.search(text) or pan_pattern.search(text) or name_pattern.search(ocr_data['text'][i-2] + " " + ocr_data['text'][i-1] + " " + text): # A simple check for Name
            
            # If it's PII, get its coordinates
            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
            
            # Draw a black rectangle over the detected PII
            draw.rectangle([(x, y), (x + w, y + h)], fill='black', outline='black')
            
            # Log what we found for the audit trail
            found_pii.append({
                "text": text,
                "action": "REDACTED",
                "coordinates": f"({x},{y},{w},{h})"
            })

    return redacted_image, found_pii


# --- STREAMLIT USER INTERFACE ---

st.set_page_config(layout="wide")

st.title("Veridion Shield - Live Demo")
st.write("This is a simple local demo of the Veridion Shield concept. Upload a document to see AI-powered redaction in action.")

# Create a file uploader widget
uploaded_file = st.file_uploader("Choose a document image (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # If a file is uploaded, open it as an image
    original_image = Image.open(uploaded_file)
    
    st.info("Processing document... This may take a moment.")
    
    # Process the image using our function
    redacted_image, audit_log = process_and_redact_image(original_image)
    
    st.success("Processing Complete!")
    
    # Display the results side-by-side
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Before")
        st.image(original_image, caption="Original Uploaded Document", use_column_width=True)
        
    with col2:
        st.header("After (Anonymized)")
        st.image(redacted_image, caption="PII has been automatically redacted.", use_column_width=True)
        
    # Display the audit log
    st.header("Audit Log")
    st.write("This log shows exactly what PII was found and redacted, proving compliance.")
    st.json(audit_log if audit_log else {"status": "No PII found matching the demo patterns."})
