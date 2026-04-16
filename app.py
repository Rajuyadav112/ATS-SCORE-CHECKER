import os
import re
from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ACTION_VERBS = {
    "achieved", "improved", "trained", "managed", "created", "resolved", "developed",
    "increased", "decreased", "spearheaded", "launched", "negotiated", "implemented",
    "designed", "optimized", "directed", "led", "established", "coordinated", "executed",
    "accelerated", "adapted", "advocated", "analyzed", "architected", "championed",
    "conceptualized", "consolidated", "cultivated", "delivered", "devised", "empowered",
    "engineered", "enhanced", "facilitated", "forecasted", "formulated", "founded",
    "generated", "identified", "influenced", "initiated", "innovated", "maximized",
    "mentored", "mobilized", "modernized", "navigated", "originated", "outperformed",
    "overhauled", "pioneered", "quantified", "reconciled", "redesigned", "reengineered",
    "revitalized", "secured", "streamlined", "transformed", "unified", "upgraded"
}

FILLER_WORDS = {
    "responsibilities included", "duties included", "worked on", "helped with",
    "team player", "hard worker", "experienced in", "responsible for"
}

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            ext = page.extract_text()
            if ext:
                text += ext + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def check_structure(text):
    score = 25
    suggestions = []
    
    # Check for email
    if not re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
        score -= 5
        suggestions.append({"category": "Structure", "type": "error", "text": "Missing Email Address. Recruiters need a way to contact you."})
        
    # Check for phone
    if not re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text):
        score -= 5
        suggestions.append({"category": "Structure", "type": "error", "text": "Missing Phone Number. Always include a direct contact number."})
        
    # Check for LinkedIn
    if "linkedin.com" not in text.lower():
        score -= 5
        suggestions.append({"category": "Structure", "type": "warning", "text": "Consider adding a LinkedIn profile link. Most professional resumes include one."})
        
    # Check for standard sections
    text_lower = text.lower()
    sections = ['education', 'experience']
    for sec in sections:
        if sec not in text_lower:
            score -= 5
            suggestions.append({"category": "Structure", "type": "error", "text": f"Missing '{sec.capitalize()}' section. This is a standard requirement for ATS."})

    return max(0, score), suggestions

def check_impact(text):
    score = 35
    suggestions = []
    
    # 1. Metrics Check
    if not re.search(r'(\d+%|\$\d+|\b\d+\b)', text):
        score -= 15
        suggestions.append({"category": "Impact", "type": "error", "text": "No quantifiable achievements found globally. Use metrics (%, $, numbers) to show concrete impact."})
    else:
        # Contextual metrics check
        lines = text.split('\n')
        missing_metric_bullets = 0
        for line in lines:
            line_str = line.strip()
            # If it looks like a bullet point (enough words) but lacks metrics
            if len(line_str.split()) > 8 and not re.search(r'(\d+%|\$\d+|\b\d+\b)', line_str):
                # Only flag if it starts with an action verb (i.e., highly likely a bullet point)
                first_word = line_str.split()[0].lower()
                if first_word in ACTION_VERBS and missing_metric_bullets < 3:
                    score -= 2
                    snippet = line_str[:60] + "..." if len(line_str) > 60 else line_str
                    suggestions.append({"category": "Impact", "type": "warning", "text": f"This achievement lacks impact. Add numbers/metrics to: '{snippet}'"})
                    missing_metric_bullets += 1
        
    # 2. Action Verbs Check
    text_lower = text.lower()
    found_verbs = [verb for verb in ACTION_VERBS if f" {verb} " in text_lower or text_lower.startswith(f"{verb} ")]
    if len(found_verbs) < 5:
        score -= 10
        suggestions.append({"category": "Impact", "type": "warning", "text": f"Use more strong action verbs. You only have {len(found_verbs)}. Aim for at least 5 different strong verbs."})
    elif len(found_verbs) > 15:
        suggestions.append({"category": "Impact", "type": "success", "text": "Excellent use of diverse, strong action verbs."})

    return max(0, score), suggestions

def check_brevity(text):
    score = 20
    suggestions = []
    
    words = text.split()
    length = len(words)
    
    # Total Length
    if length < 350:
        score -= 10
        suggestions.append({"category": "Brevity", "type": "warning", "text": f"Your resume is too short ({length} words). Aim for 400-800 words to adequately convey your experience."})
    elif length > 1000:
        score -= 10
        suggestions.append({"category": "Brevity", "type": "warning", "text": f"Your resume is too long ({length} words). Condense it to be more concise (aim for under 800 words)."})
    else:
        suggestions.append({"category": "Brevity", "type": "success", "text": f"Perfect length ({length} words)! Keeps the recruiter engaged."})

    # Filler Words Contextual Check
    lines = text.split('\n')
    filler_flags = 0
    
    for line in lines:
        line_str = line.strip().lower()
        for filler in FILLER_WORDS:
            if filler in line_str and filler_flags < 3:
                score -= 4
                snippet = line.strip()[:60] + "..." if len(line.strip()) > 60 else line.strip()
                suggestions.append({"category": "Brevity", "type": "error", "text": f"Avoid passive filler '{filler}'. Found in: '{snippet}'. Start this bullet with an action verb instead."})
                filler_flags += 1
                break # Only flag one filler word per line to avoid compounding

    return max(0, score), suggestions

def check_job_match(text, job_description=""):
    score = 20
    suggestions = []
    
    if not job_description:
        return score, suggestions # Give full points if no JD provided to not unfairly penalize
        
    text_lower = text.lower()
    jd_words = set(re.findall(r'\b[a-z]{4,}\b', job_description.lower()))
    res_words = set(re.findall(r'\b[a-z]{4,}\b', text_lower))
    
    stop_words = {"this", "that", "with", "from", "your", "have", "will", "what", "where", "when"}
    jd_words = jd_words - stop_words
    
    if len(jd_words) > 0:
        overlap = jd_words.intersection(res_words)
        match_percentage = len(overlap) / len(jd_words)
        
        if match_percentage < 0.2:
            score -= 15
            suggestions.append({"category": "Job Match", "type": "error", "text": "Poor keyword match (<20%). Tailor your resume better to the Job Description."})
        elif match_percentage < 0.4:
            score -= 5
            suggestions.append({"category": "Job Match", "type": "warning", "text": "Moderate keyword match. Consider adding more keywords from the Job Description."})
        else:
            suggestions.append({"category": "Job Match", "type": "success", "text": "Great keyword alignment with the job description!"})
            
    return max(0, score), suggestions

def score_resume(text, job_description=""):
    suggestions = []
    
    s_score, s_sugg = check_structure(text)
    i_score, i_sugg = check_impact(text)
    b_score, b_sugg = check_brevity(text)
    j_score, j_sugg = check_job_match(text, job_description)
    
    total_score = s_score + i_score + b_score + j_score
    suggestions.extend(s_sugg + i_sugg + b_sugg + j_sugg)
    
    if total_score >= 90:
        suggestions.insert(0, {"category": "Overall", "type": "success", "text": "Outstanding resume! Highly competitive."})
        
    return total_score, suggestions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process PDF
        text = extract_text_from_pdf(filepath)
        
        # Clean up file after extraction
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if text is None:
            return jsonify({'error': 'Could not extract text from PDF. The file might be corrupted or image-based.'}), 500
            
        job_description = request.form.get('job_description', '')
        score, suggestions = score_resume(text, job_description)
        
        return jsonify({
            'score': score,
            'suggestions': suggestions
        })
    else:
        return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
