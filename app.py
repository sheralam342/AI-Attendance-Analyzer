import streamlit as st
import pandas as pd
from openai import OpenAI
from docx import Document
import time

# Page configuration
st.set_page_config(page_title="AI Attendance Pro", page_icon="🎓", layout="wide")

st.title("🎓 AI Attendance Analyzer")
st.write("Upload your attendance **Word Document (.docx)** and use **OpenRouter AI** to generate reports.")

# --- SIDEBAR: API CONFIGURATION ---
st.sidebar.header("⚙️ API Configuration")
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    st.sidebar.success("Using API Key from Secrets ✅")
else:
    api_key = st.sidebar.text_input("Enter OpenRouter API Key", type="password")
    if not api_key:
        st.sidebar.warning("Please enter your API key to enable AI features.")

# --- SMART EXTRACTION FUNCTION ---
def extract_attendance_table(file):
    try:
        doc = Document(file)
        for table in doc.tables:
            data = []
            for row in table.rows:
                data.append([cell.text.strip().replace('\n', ' ') for cell in row.cells])
            
            if len(data) > 1 and len(data[0]) >= 3:
                # Create initial DataFrame
                df = pd.DataFrame(data)
                
                # --- SMART FILTERING START ---
                # We look for the row that actually contains 'Roll' or 'Student' to use as the header
                header_row_index = 0
                for i, row in enumerate(data):
                    if "roll" in row[0].lower() or "student" in row[1].lower():
                        header_row_index = i
                        break
                
                # Set the correct header and remove rows above it
                df.columns = data[header_row_index]
                df = df.iloc[header_row_index + 1:].reset_index(drop=True)
                
                # Remove rows that don't have any attendance marks (P or A)
                # This removes "Subject: _____" or empty rows
                def is_student_row(row):
                    # Check if any cell from the 3rd column onwards contains 'P' or 'A'
                    attendance_cells = [str(cell).upper() for cell in row[2:]]
                    return 'P' in attendance_cells or
