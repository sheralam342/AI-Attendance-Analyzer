import streamlit as st
import pandas as pd
from openai import OpenAI

# Page configuration
st.set_page_config(page_title="AI Attendance Pro", page_icon="🎓")

st.title("🎓 AI Attendance Analyzer")
st.write("Upload your attendance sheet and use **OpenRouter AI** to generate student reports.")

# --- SIDEBAR: API CONFIGURATION ---
st.sidebar.header("⚙️ API Configuration")
api_key = st.sidebar.text_input("Enter OpenRouter API Key", type="password")

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Attendance CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Load Data
        df = pd.read_csv(uploaded_file)
        st.subheader("📋 Uploaded Attendance Data")
        st.write(df)

        # 2. Data Validation (Ensure there is at least one name column and one date column)
        if df.shape[1] < 2:
            st.error("Error: The CSV must have at least two columns (Student Name and Attendance dates).")
        else:
            # Logic: First column = Name, the rest = Attendance marks (P/A)
            names = df.iloc[:, 0]
            attendance_data = df.iloc[:, 1:]
            
            # Calculate Total Days and Days Present
            total_days = attendance_data.shape[1]
            present_days = attendance_data.apply(lambda row: (row == 'P').sum(), axis=1)
            percentage = (present_days / total_days) * 100

            # Create Summary Table
            summary_df = pd.DataFrame({
                'Student Name': names,
                'Attendance %': percentage
            })

            # 3. Filtering: Find students below 75%
            low_attendance = summary_df[summary_df['Attendance %'] < 75]

            st.subheader("⚠️ Low Attendance List (< 75%)")
            if not low_attendance.empty:
                st.table(low_attendance)
                
                st.divider()
                st.subheader("🤖 AI Report Generator")
                
                # 4. AI Integration: Use OpenRouter to generate the warning
                if api_key:
                    if st.button("Generate AI Warning Reports"):
                        with st.spinner("OpenRouter AI is analyzing and writing..."):
                            try:
                                # Initialize OpenAI client for OpenRouter
                                client = OpenAI(
                                    base_url="https://openrouter.ai/api/v1",
                                    api_key=api_key,
                                )
                                
                                student_list_text = low_attendance.to_string(index=False)
                                
                                prompt = f"""
                                I am a teacher. The following students have attendance below 75%:
                                {student_list_text}
                                
                                Please write a professional, firm, but supportive warning email 
                                to these students. Explain that they are at risk of not being 
                                allowed to take exams. Give them a helpful tip on time management.
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
                    st.info("Please enter your OpenRouter API key in the sidebar to unlock AI reports.")
            else:
                st.success("All students have 75% or more attendance! 🎉")*
