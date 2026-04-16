# ATS Score Checker (Resume Ranker Pro)

An AI-powered, Flask-based resume scoring engine that instantly analyzes your CV and generates an ATS-friendly score alongside highly actionable, line-by-line feedback.

## Features

- **Contextual Line-Level Feedback**: The engine scans your resume line-by-line and extracts the exact sentences where filler words are used or measurable metrics are missing.
- **Strict 4-Pillar Scoring System**:
  - **Structure**: Checks for essential contact information (Email, Phone, LinkedIn) and core sections.
  - **Impact**: Evaluates the action verbs utilized and heavily prioritizes quantifiable achievements ($, %, numbers).
  - **Brevity**: Detects and penalizes passive voice and weak filler phrases (e.g., "responsibilities included").
  - **Job Match**: A keyword overlap metric that matches your text against a provided Job Description.
- **Premium User Interface**: Implements modern glassmorphism design, interactive scanning overlays to simulate deep processing, and distinct category cards for displaying the feedback properly.

## Tech Stack
- **Backend:** Python, Flask, PyPDF2
- **Frontend:** HTML5, CSS3 (Vanilla), Vanilla JavaScript
- **Fonts:** Google Fonts (Outfit)

## How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/Rajuyadav112/ATS-SCORE-CHECKER.git
   cd ATS-SCORE-CHECKER
   ```

2. **Run the application**
   ```bash
   python app.py
   ```

3. **Open in your browser**
   Navigate to `http://127.0.0.1:5000/`

## Usage
Simply drop in your PDF resume and (optionally) paste the job description you are aiming for. The AI will evaluate your layout, vocabulary, and impact instantly.
