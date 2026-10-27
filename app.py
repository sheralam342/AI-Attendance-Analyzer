import streamlit as st
import pandas as pd
from openai import OpenAI
from docx import Document
import time # Added to make the workflow visible

# Page configuration
st.set_page_config(page_title="AI Attendance Pro", page_icon="🎓")

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

# --- HELPER FUNCTION TO EXTRACT TABLE FROM WORD ---
def extract_table_from_word(file):
    doc = Document(file)
    if not doc.tables:
        return None
    table = doc.tables[0]
    data = []
    for row in table.rows:
        data.append([cell.text.strip() for cell in row.cells])
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Attendance Word File", type=["docx"])

if uploaded_file is not None:
    # =========================================================================
    # REAL-TIME WORKFLOW PROCESS START
    # =========================================================================
    with st.status("🚀 Processing Attendance Workflow...", expanded=True) as status:
        # Step 1: Extraction
        st.write("🔍 Step 1: Extracting table from Word document...")
        time.sleep(1) # Slight delay so the teacher can see the process
        df = extract_table_from_word(uploaded_file)
        
        if df is None:
            status.update(label="❌ Workflow Failed!", state="error", expanded=True)
            st.error("No table found in the document.")
            st.stop()
        st.write("✅ Table extracted successfully.")

        # Step 2: Calculation
        st.write("🧮 Step 2: Calculating attendance percentages...")
        time.sleep(1)
        
        if df.shape[1] < 3:
            status.update(label="❌ Workflow Failed!", state="error", expanded=True)
            st.error("Table must have Roll No, Name, and Attendance columns.")
            st.stop()
            
        roll_numbers = df.iloc[:, 0]
        names = df.iloc[:, 1]
        attendance_data = df.iloc[:, 2:]
        total_days = attendance_data.shape[1]
        present_days = attendance_data.apply(lambda row: (row.astype(str) == 'P').sum(), axis=1)
        percentage = (present_days / total_days) * 100
        
        summary_df = pd.DataFrame({
            'Roll No': roll_numbers,
            'Student Name': names,
            'Attendance %': percentage
        })
        st.write("✅ Percentages calculated.")

        # Step 3: Filtering
        st.write("🎯 Step 3: Filtering students with < 75% attendance...")
        time.sleep(1)
        low_attendance = summary_df[summary_df['Attendance %'] < 75]
        st.write(f"✅ Found {len(low_attendance)} students with low attendance.")
        
        # Final Status*
