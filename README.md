# AI-Attendance-Analyzer
# 🎓 AI Attendance Analyzer (OpenRouter AI)

This project is a smart attendance management system that automates the calculation of student attendance and uses a Large Language Model (LLM) via **OpenRouter** to generate professional academic warnings for students falling below the 75% threshold.

## 🚀 Features
- **CSV Processing:** Automatically reads attendance data from uploaded CSV files.
- **Smart Calculation:** Computes attendance percentages based on 'P' (Present) and 'A' (Absent) marks.
- **Threshold Detection:** Instantly identifies students with less than 75% attendance.
- **AI Generation:** Uses the **Llama-3 model (via OpenRouter)** to transform raw data into human-like, professional communication.

## 🛠️ System Workflow

```mermaid
graph TD
    A[User Uploads CSV File] --> B{Valid CSV?}
    B -- No --> C[Show Error Message]
    B -- Yes --> D[Pandas Processes Data]
    D --> E[Calculate Attendance % per Student]
    E --> F{Attendance < 75%?}
    F -- No --> G[Display 'All Students Passed']
    F -- Yes --> H[Generate Low Attendance List]
    H --> I{API Key Provided?}
    I -- No --> J[Prompt for API Key]
    I -- Yes --> K[Send Data to OpenRouter AI]
    K --> L[AI Generates Professional Warning Email]
    L --> M[Display Final Report to Teacher]
