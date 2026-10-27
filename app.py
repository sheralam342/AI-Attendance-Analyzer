import streamlit as st
import pandas as pd
from openai import OpenAI

# Page configuration
st.set_page_config(page_title="AI Attendance Pro", page_icon="🎓")

st.title("🎓 AI Attendance Analyzer")
st.write("Upload your attendance sheet and use **OpenRouter AI** to generate student warning reports.")

# --- SIDEBAR: API KEY ---
st.sidebar.header("⚙️ API Configuration")
api_key = st.sidebar.text_input("Enter OpenRouter API Key", type="password")

# Initialize OpenRouter Client
if api_key:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
else:
    st.sidebar.warning("Please enter your OpenRouter API key to enable AI features.")

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Attendance CSV", type="csv")

if uploaded_file is not None:
    # Read CSV
    df = pd.read_csv(uploaded_file)
    st.subheader("📋 Attendance Data")
    st.write(df)

    # Logic: First column is Student Name, others are attendance marks (P/A)
    names = df.iloc[:, 0]
    attendance_data = df.iloc[:, 1:]
    
    total_days = attendance_data.shape[1]
    # Count 'P' for present in each row
    present_days = attendance_data.apply(lambda row: (row == 'P').sum(), axis=1)
    percentage = (present_days / total_days) * 100

    # Create a summary table
    summary_df = pd.DataFrame({
        'Student Name': names,
        'Attendance %': percentage
    })

    # Filter students below 75%
    low_attendance = summary_df[summary_df['Attendance %'] < 75]

    st.subheader("⚠️ Low Attendance List (< 75%)")
    if not low_attendance.empty:
        st.table(low_attendance)
        
        st.divider()
        st.subheader("🤖 AI Report Generator")
        
        if api_key:
            if st.button("Generate AI Warning Reports"):
                with st.spinner("OpenRouter AI is analyzing data..."):
                    try:
                        # Convert the list of students to a string for the AI
                        student_list_text = low_attendance.to_string(index=False)
                        
                        prompt = f"""
                        I am a college teacher. The following students have attendance below 75%:
                        {student_list_text}
                        
                        Please write a professional, firm, but encouraging warning email 
                        to these students. Mention that attendance is mandatory to avoid 
                        being barred from final exams. Give them one piece of advice on 
                        how to manage their time better.
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
                        st.error(f"An error occurred: {e}")
        else:
            st.info("Please provide your OpenRouter API key in the sidebar to generate the report.")
    else:
        st.success("All students have 75% or more attendance! 🎉")
