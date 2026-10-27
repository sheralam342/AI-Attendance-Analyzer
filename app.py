import streamlit as st
import pandas as pd
from openai import OpenAI
from docx import Document

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
    except Exception as e:
        st.error(f"Error reading Word file: {e}")
        return None

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Attendance Word File", type=["docx"])

if uploaded_file is not None:
    df = extract_table_from_word(uploaded_file)

    if df is None:
        st.error("❌ No table found! Please ensure your data is inside a **Table** in the Word document.")
    else:
        st.subheader("📋 Extracted Attendance Data")
        st.write(df)

        # Validation: Now we need at least 3 columns (Roll No, Name, and at least 1 Day)
        if df.shape[1] < 3:
            st.error("Error: The table must have at least three columns (Roll No, Student Name, and Attendance dates).")
        else:
            # Logic: Col 0 = Roll No, Col 1 = Name, Col 2+ = Attendance
            roll_numbers = df.iloc[:, 0]
            names = df.iloc[:, 1]
            attendance_data = df.iloc[:, 2:]
            
            total_days = attendance_data.shape[1]
            present_days = attendance_data.apply(lambda row: (row.astype(str) == 'P').sum(), axis=1)
            percentage = (present_days / total_days) * 100

            # Create Summary Table including Roll Number
            summary_df = pd.DataFrame({
                'Roll No': roll_numbers,
                'Student Name': names,
                'Attendance %': percentage
            })

            # Filtering: Find students below 75%
            low_attendance = summary_df[summary_df['Attendance %'] < 75]

            st.subheader("⚠️ Low Attendance List (< 75%)")
            if not low_attendance.empty:
                st.table(low_attendance)
                
                st.divider()
                st.subheader("🤖 AI Report Generator")
                
                if api_key:
                    if st.button("Generate AI Warning Reports"):
                        with st.spinner("OpenRouter AI is analyzing..."):
                            try:
                                client = OpenAI(
                                    base_url="https://openrouter.ai/api/v1",
                                    api_key=api_key,
                                )
                                
                                # Convert low attendance list to text for AI
                                student_list_text = low_attendance.to_string(index=False)
                                
                                # Enhanced Prompt including Roll Numbers
                                prompt = f"""
                                I am a teacher. The following students have attendance below 75%:
                                {student_list_text}
                                
                                Please write a professional and firm warning email to these students. 
                                Make sure to mention their **Roll Number** and **Name** clearly so there is no confusion.
                                Explain that they are at risk of being barred from exams. 
                                Give them a tip on how to improve their attendance.
                                """
                                
                                response = client.chat.completions.create(
                                    model="meta-llama/llama-3-8b-instruct", 
                                    messages=[
                                        {"role": "system", "content": "You are a professional academic advisor."},
                                        {"role": "user", "content": prompt},
                                    ],
                                )
                                st.markdown("### 📩 Generated AI Report:")
                                st.write(response.choices[0].message.content)
                            except Exception as e:
                                st.error(f"AI API Error: {e}")
                else:
                    st.info("Please enter your OpenRouter API key in the sidebar.")
            else:
                st.success("All students have 75% or more attendance! 🎉")
