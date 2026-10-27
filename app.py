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

# --- HELPER FUNCTION ---
def extract_table_from_word(file):
    try:
        doc = Document(file)
        if not doc.tables:
            return None
        table = doc.tables[0]
        data = []
        for row in table.rows:
            data.append([cell.text.strip() for cell in row.cells])
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception:
        return None

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Attendance Word File", type=["docx"])

if uploaded_file is not None:
    # Initialize variables to avoid "not defined" errors
    df = None
    low_attendance = None

    # =========================================================================
    # REAL-TIME WORKFLOW PROCESS
    # =========================================================================
    with st.status("🚀 Processing Attendance Workflow...", expanded=True) as status:
        st.write("🔍 Step 1: Extracting table from Word document...")
        time.sleep(1)
        df = extract_table_from_word(uploaded_file)
        
        if df is None:
            status.update(label="❌ Workflow Failed!", state="error")
            st.error("No table found in the document.")
            st.stop()
        st.write("✅ Table extracted successfully.")

        st.write("🧮 Step 2: Calculating attendance percentages...")
        time.sleep(1)
        
        if df.shape[1] < 3:
            status.update(label="❌ Workflow Failed!", state="error")
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

        st.write("🎯 Step 3: Filtering students with < 75% attendance...")
        time.sleep(1)
        low_attendance = summary_df[summary_df['Attendance %'] < 75]
        st.write(f"✅ Found {len(low_attendance)} students with low attendance.")
        
        status.update(label="✅ Workflow Complete!", state="complete", expanded=False)
    
    # Notification that results are ready
    st.toast("Results have been generated! Scroll down to see them.", icon="🎉")

    # =========================================================================
    # DISPLAY RESULTS (Placed clearly below the status box)
    # =========================================================================
    st.markdown("---") # Adds a visual line
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Extracted Data")
        st.dataframe(df, use_container_width=True)

    with col2:
        st.subheader("⚠️ Low Attendance (< 75%)")
        if low_attendance is not None and not low_attendance.empty:
            st.table(low_attendance)
        else:
            st.success("All students have 75% or more attendance! 🎉")

    # AI SECTION
    if low_attendance is not None and not low_attendance.empty:
        st.divider()
        st.subheader("🤖 AI Report Generator")
        if api_key:
            if st.button("Generate AI Warning Reports", type="primary"):
                with st.spinner("*
