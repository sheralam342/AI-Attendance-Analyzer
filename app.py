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
                    return 'P' in attendance_cells or 'A' in attendance_cells
                
                df = df[df.apply(is_student_row, axis=1)].reset_index(drop=True)
                # --- SMART FILTERING END ---
                
                if not df.empty:
                    return df
        return None
    except Exception as e:
        st.error(f"Error reading Word file: {e}")
        return None

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Attendance Word File", type=["docx"])

if uploaded_file is not None:
    df = None
    low_attendance = None

    with st.status("🚀 Processing Attendance Workflow...", expanded=True) as status:
        st.write("🔍 Step 1: Extracting and Cleaning Table...")
        time.sleep(1)
        df = extract_attendance_table(uploaded_file)
        
        if df is None or df.empty:
            status.update(label="❌ Workflow Failed!", state="error")
            st.error("❌ No valid student data found. Please ensure your table has P/A marks.")
            st.stop()
        st.write(f"✅ Found {len(df)} valid student records.")

        st.write("🧮 Step 2: Calculating attendance percentages...")
        time.sleep(1)
        
        try:
            # Use column positions to be safe
            roll_numbers = df.iloc[:, 0]
            names = df.iloc[:, 1]
            attendance_data = df.iloc[:, 2:]
            
            total_days = attendance_data.shape[1]
            # Count 'P' regardless of case
            present_days = attendance_data.apply(lambda row: row.astype(str).str.upper().eq('P').sum(), axis=1)
            percentage = (present_days / total_days) * 100
            
            summary_df = pd.DataFrame({
                'Roll No': roll_numbers,
                'Student Name': names,
                'Attendance %': percentage
            })
            st.write("✅ Percentages calculated successfully.")
        except Exception as e:
            status.update(label="❌ Calculation Error!", state="error")
            st.error(f"Error calculating data: {e}")
            st.stop()

        st.write("🎯 Step 3: Filtering students with < 75% attendance...")
        time.sleep(1)
        low_attendance = summary_df[summary_df['Attendance %'] < 75]
        st.write(f"✅ Found {len(low_attendance)} students with low attendance.")
        
        status.update(label="✅ Workflow Complete!", state="complete", expanded=False)
    
    st.toast("Results are ready below!", icon="🎉")

    # =========================================================================
    # DISPLAY RESULTS
    # =========================================================================
    st.markdown("---")
    st.subheader("📊 Final Attendance Summary")
    st.dataframe(summary_df, use_container_width=True)

    st.divider()
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("⚠️ Low Attendance (< 75%)")
        if low_attendance is not None and not low_attendance.empty:
            st.table(low_attendance)
        else:
            st.success("All students have 75% or more attendance! 🎉")

    with col2:
        st.subheader("🤖 AI Report Generator")
        if api_key:
            if low_attendance is not None and not low_attendance.empty:
                if st.button("Generate AI Warning Reports", type="primary"):
                    with st.spinner("OpenRouter AI is writing..."):
                        try:
                            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
                            student_list_text = low_attendance.to_string(index=False)
                            prompt = f"I am a teacher. The following students have attendance below 75%:\n{student_list_text}\nWrite a professional warning email. Mention Roll No and Name."
                            
                            response = client.chat.completions.create(
                                model="meta-llama/llama-3.1-8b-instruct", 
                                messages=[{"role": "system", "content": "You are a professional academic advisor."},
                                          {"role": "user", "content": prompt}]
                            )
                            st.markdown("### 📩 Generated AI Report:")
                            st.write(response.choices[0].message.content)
                        except Exception as e:
                            st.error(f"AI API Error: {e}")
            else:
                st.info("No students found with low attendance to report.")
        else:
            st.info("Please enter your OpenRouter API key in the sidebar.")
