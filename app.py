import streamlit as st
import requests
import time
import re
from datetime import datetime

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fake News Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }

    /* Title */
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #f093fb, #f5576c, #fda085);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        color: #a0a0c0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Result boxes */
    .result-fake {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 65, 108, 0.4);
        margin: 1rem 0;
    }

    .result-real {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(56, 239, 125, 0.4);
        margin: 1rem 0;
    }

    .result-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: white;
        margin: 0;
    }

    .result-emoji {
        font-size: 4rem;
    }

    .confidence-text {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
    }

    /* Info cards */
    .info-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
    }

    .info-card h4 {
        color: #f093fb;
        margin-bottom: 0.5rem;
    }

    /* History item */
    .history-item-fake {
        background: rgba(255, 65, 108, 0.15);
        border-left: 4px solid #ff416c;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }

    .history-item-real {
        background: rgba(56, 239, 125, 0.15);
        border-left: 4px solid #38ef7d;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.9) !important;
    }

    /* Button */
    .stButton > button {
        background: linear-gradient(90deg, #f093fb, #f5576c);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.6rem 2rem;
        width: 100%;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(245, 87, 108, 0.5);
    }

    /* Text area */
    .stTextArea textarea {
        background: rgba(30, 20, 60, 0.95) !important;
        border: 1.5px solid rgba(240, 147, 251, 0.5) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 1rem !important;
        caret-color: #f093fb !important;
        -webkit-text-fill-color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif !important;
        line-height: 1.6 !important;
        letter-spacing: 0.3px !important;
    }

    /* Placeholder text */
    .stTextArea textarea::placeholder {
        color: rgba(180, 160, 220, 0.6) !important;
        -webkit-text-fill-color: rgba(180, 160, 220, 0.6) !important;
        font-style: italic !important;
    }

    /* Text area focus */
    .stTextArea textarea:focus {
        border-color: #f093fb !important;
        box-shadow: 0 0 12px rgba(240, 147, 251, 0.3) !important;
        outline: none !important;
    }

    /* Text area label */
    .stTextArea label {
        color: #f093fb !important;
        font-weight: 600 !important;
    }

    /* All general text */
    p, span, div, h1, h2, h3, h4, h5, label {
        color: #ffffff;
    }

    /* Streamlit default input text fix */
    .stTextInput input {
        background: rgba(30, 20, 60, 0.95) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1.5px solid rgba(240, 147, 251, 0.5) !important;
        border-radius: 10px !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(30, 20, 60, 0.95) !important;
        border: 2px dashed rgba(240, 147, 251, 0.5) !important;
        border-radius: 14px !important;
        padding: 1rem !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #f093fb !important;
        box-shadow: 0 0 16px rgba(240, 147, 251, 0.3) !important;
    }

    [data-testid="stFileUploader"] label {
        color: #f093fb !important;
        font-weight: 600 !important;
    }

    [data-testid="stFileUploader"] span {
        color: #ccbbee !important;
    }

    /* Radio buttons */
    .stRadio label {
        color: #ffffff !important;
        font-size: 1rem !important;
    }

    .stRadio [data-testid="stMarkdownContainer"] p {
        color: #f093fb !important;
        font-weight: 700 !important;
    }

    /* Metric */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

def preprocess_text(text):
    """Basic text cleaning"""
    text = text.strip()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def analyze_with_huggingface(text):
    """
    Uses HuggingFace Inference API (free, no key needed for public models).
    Model: hamzab/roberta-fake-news-classification
    """
    API_URL = "https://api-inference.huggingface.co/models/hamzab/roberta-fake-news-classification"
    headers = {"Content-Type": "application/json"}

    payload = {"inputs": text[:512]}  # truncate to 512 tokens

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            # Result is list of list of dicts: [[{label, score}, ...]]
            if isinstance(result, list) and len(result) > 0:
                predictions = result[0] if isinstance(result[0], list) else result
                label_map = {}
                for item in predictions:
                    label_map[item['label'].upper()] = item['score']

                fake_score = label_map.get('FAKE', label_map.get('LABEL_1', 0))
                real_score = label_map.get('REAL', label_map.get('LABEL_0', 0))

                if fake_score > real_score:
                    return "FAKE", fake_score
                else:
                    return "REAL", real_score
        return None, None
    except Exception:
        return None, None


def rule_based_analysis(text):
    """
    Fallback rule-based heuristic analysis when API is unavailable.
    """
    text_lower = text.lower()

    fake_indicators = [
        "breaking:", "shocking", "you won't believe", "they don't want you to know",
        "secret", "exposed", "coverup", "conspiracy", "miracle cure",
        "doctors hate", "click here", "share before deleted", "banned",
        "wake up", "sheeple", "deep state", "hoax", "crisis actor",
        "100% proven", "scientists baffled", "they lied", "fake media"
    ]

    real_indicators = [
        "according to", "researchers found", "study shows", "reported by",
        "official statement", "data shows", "analysis", "evidence",
        "confirmed", "verified", "sources say", "published in",
        "peer reviewed", "experts say", "statistics show"
    ]

    fake_count = sum(1 for word in fake_indicators if word in text_lower)
    real_count = sum(1 for word in real_indicators if word in text_lower)

    # Word count heuristic
    words = text.split()
    exclamation = text.count('!')
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)

    fake_score = fake_count * 0.15 + (exclamation * 0.05) + (caps_words * 0.05)
    real_score = real_count * 0.15

    fake_score = min(fake_score, 0.95)
    real_score = min(real_score, 0.95)

    if fake_score == 0 and real_score == 0:
        # neutral — slightly lean fake for demo
        fake_score = 0.45
        real_score = 0.55

    total = fake_score + real_score
    fake_score /= total
    real_score /= total

    if fake_score > real_score:
        return "FAKE", fake_score
    else:
        return "REAL", real_score


def detect_fake_news(text):
    """Main detection function — tries API first, falls back to rule-based."""
    cleaned = preprocess_text(text)

    label, confidence = analyze_with_huggingface(cleaned)

    if label is None:
        label, confidence = rule_based_analysis(cleaned)
        method = "Rule-Based Analysis (Offline Mode)"
    else:
        method = "RoBERTa AI Model (HuggingFace)"

    return label, confidence, method


def get_word_stats(text):
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    return len(words), len(sentences)


# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

if "total_checked" not in st.session_state:
    st.session_state.total_checked = 0

if "fake_count" not in st.session_state:
    st.session_state.fake_count = 0

if "real_count" not in st.session_state:
    st.session_state.real_count = 0


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Fake News Detector")
    st.markdown("---")

    st.markdown("### 📊 Session Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Total Checked", st.session_state.total_checked)
        st.metric("🔴 Fake News", st.session_state.fake_count)
    with col2:
        st.metric("🟢 Real News", st.session_state.real_count)
        accuracy_rate = (
            f"{(st.session_state.real_count / st.session_state.total_checked * 100):.0f}%"
            if st.session_state.total_checked > 0 else "N/A"
        )
        st.metric("📰 Real Rate", accuracy_rate)

    st.markdown("---")

    st.markdown("### ℹ️ How It Works")
    st.markdown("""
    <div class='info-card'>
    <h4>🤖 AI Model</h4>
    <p style='color:#ccc; font-size:0.85rem;'>Uses RoBERTa transformer model trained on fake news datasets via HuggingFace API.</p>
    </div>

    <div class='info-card'>
    <h4>🔄 Fallback Mode</h4>
    <p style='color:#ccc; font-size:0.85rem;'>If API is unavailable, rule-based NLP analysis is used automatically.</p>
    </div>

    <div class='info-card'>
    <h4>📋 Best Results</h4>
    <p style='color:#ccc; font-size:0.85rem;'>Enter at least 50 words for better accuracy. Works best with English text.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.total_checked = 0
        st.session_state.fake_count = 0
        st.session_state.real_count = 0
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='color:#666; font-size:0.75rem; text-align:center;'>Final Year Project<br>Fake News Detection System<br>Using NLP & Transformers</p>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────
st.markdown('<h1 class="main-title">🔍 Real-Time Fake News Detector</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by RoBERTa Transformer Model | NLP-Based Classification System</p>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔎 Analyze News", "📜 History", "📖 About"])

# ─── TAB 1: Analyze ───
with tab1:

    # ── Input Method Selector ──
    st.markdown("### 📥 Choose Input Method")
    input_method = st.radio(
        "",
        ["✍️ Type / Paste Text", "📂 Upload File from Laptop"],
        horizontal=True,
        key="input_method"
    )

    # Always initialize news_input from session state
    if "final_text" not in st.session_state:
        st.session_state.final_text = ""

    news_input = ""

    # ─────────────────────────────
    # ── Option 1: Text Input ──
    # ─────────────────────────────
    if input_method == "✍️ Type / Paste Text":
        st.markdown("### 📝 Enter News Article or Text")

        # Example news buttons
        st.markdown("##### 💡 Try Example News:")
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            if st.button("📰 Load Real News Example"):
                st.session_state.final_text = (
                    "According to a new study published in the Journal of Science, researchers have found "
                    "that regular exercise of at least 30 minutes per day significantly reduces the risk of "
                    "cardiovascular disease. The study analyzed data from over 50,000 participants across "
                    "10 countries over a period of 5 years. Experts say the findings confirm previous research "
                    "and recommend moderate physical activity as part of a healthy lifestyle."
                )
        with ex_col2:
            if st.button("⚠️ Load Fake News Example"):
                st.session_state.final_text = (
                    "BREAKING: Shocking secret they don't want you to know! Scientists have been BANNED from "
                    "telling the truth about miracle cure that cures all diseases overnight! The deep state is "
                    "covering this up!! Share before this gets deleted! You won't believe what doctors are hiding "
                    "from you. Wake up sheeple, this is 100% PROVEN and they lied to us all along!!!"
                )

        news_input = st.text_area(
            label="✏️ Type or Paste your news article here:",
            value=st.session_state.final_text,
            placeholder="Paste your news article, social media post, or any text here...\n\nمثال: کوئی بھی خبر یہاں paste کریں...",
            height=250,
            key="news_text_area"
        )
        # Keep session state in sync
        st.session_state.final_text = news_input

    # ─────────────────────────────────────────
    # ── Option 2: File Upload from Laptop ──
    # ─────────────────────────────────────────
    else:
        st.markdown("### 📂 Upload News Article from Your Laptop")

        st.markdown("""
        <div class='info-card'>
            <h4>📋 Supported File Types</h4>
            <p style='color:#ccc; font-size:0.9rem;'>
            ✅ <strong>.txt</strong> — Plain text file &nbsp;|&nbsp;
            ✅ <strong>.pdf</strong> — PDF document &nbsp;|&nbsp;
            ✅ <strong>.docx</strong> — Word document &nbsp;|&nbsp;
            ✅ <strong>.csv</strong> — CSV file
            </p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "📁 Click 'Browse files' to select a file from your laptop",
            type=["txt", "pdf", "docx", "csv"],
            accept_multiple_files=False,
            key="file_uploader",
            help="Select any .txt, .pdf, .docx or .csv file from your computer"
        )

        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            file_ext = file_name.split(".")[-1].lower()

            # File info
            st.markdown(f"""
            <div class='info-card'>
                <h4>✅ File Loaded from Your Laptop!</h4>
                <p style='color:#ccc;'>
                    📁 <strong>File Name:</strong> {file_name}<br>
                    📦 <strong>File Size:</strong> {file_size / 1024:.1f} KB<br>
                    🔖 <strong>File Type:</strong> {file_ext.upper()}
                </p>
            </div>
            """, unsafe_allow_html=True)

            extracted_text = ""

            try:
                import io

                # ── TXT ──
                if file_ext == "txt":
                    raw = uploaded_file.read()
                    extracted_text = raw.decode("utf-8", errors="ignore")

                # ── PDF ──
                elif file_ext == "pdf":
                    try:
                        import PyPDF2
                        pdf_bytes = io.BytesIO(uploaded_file.read())
                        pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                        for page in pdf_reader.pages:
                            extracted_text += page.extract_text() or ""
                        if not extracted_text.strip():
                            st.warning("⚠️ PDF has no extractable text. Please use a text-based PDF.")
                    except ImportError:
                        st.error("❌ PyPDF2 missing. Run: pip install PyPDF2")

                # ── DOCX ──
                elif file_ext == "docx":
                    try:
                        import docx
                        doc_bytes = io.BytesIO(uploaded_file.read())
                        doc = docx.Document(doc_bytes)
                        extracted_text = "\n".join(
                            [para.text for para in doc.paragraphs if para.text.strip()]
                        )
                    except ImportError:
                        st.error("❌ python-docx missing. Run: pip install python-docx")

                # ── CSV ──
                elif file_ext == "csv":
                    try:
                        import pandas as pd
                        csv_bytes = io.BytesIO(uploaded_file.read())
                        df = pd.read_csv(csv_bytes)
                        text_cols = df.select_dtypes(include="object").columns.tolist()
                        if text_cols:
                            extracted_text = " ".join(
                                df[text_cols[0]].dropna().astype(str).tolist()
                            )
                            st.info(f"ℹ️ Reading from column: **{text_cols[0]}**")
                        else:
                            st.warning("⚠️ No text column found in CSV.")
                    except ImportError:
                        st.error("❌ pandas missing. Run: pip install pandas")

            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

            # ── Show extracted text and store it ──
            if extracted_text.strip():
                st.session_state.final_text = extracted_text
                news_input = extracted_text

                word_count_preview = len(extracted_text.split())
                st.success(f"✅ Successfully extracted **{word_count_preview} words** from your file!")

                st.markdown("#### 👁️ Extracted Text Preview:")
                preview_text = extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else "")
                st.markdown(f"""
                <div style='background:rgba(30,20,60,0.95);
                            border:1.5px solid rgba(240,147,251,0.5);
                            border-radius:12px;
                            padding:1.2rem;
                            max-height:220px;
                            overflow-y:auto;
                            color:#ffffff;
                            font-size:0.92rem;
                            line-height:1.7;
                            -webkit-text-fill-color:#ffffff;'>
                {preview_text}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Editable version of extracted text
                edited = st.text_area(
                    "✏️ Edit extracted text if needed:",
                    value=extracted_text,
                    height=150,
                    key="edited_upload_text"
                )
                news_input = edited
                st.session_state.final_text = edited

        else:
            # No file uploaded yet
            st.markdown("""
            <div style='background:rgba(30,20,60,0.7);
                        border: 2px dashed rgba(240,147,251,0.4);
                        border-radius:14px;
                        padding:2.5rem;
                        text-align:center;
                        color:#ccbbee;'>
                <p style='font-size:3rem; margin:0;'>📂</p>
                <p style='font-size:1.1rem; margin:0.5rem 0;'>No file selected yet</p>
                <p style='font-size:0.85rem; color:#998bbb;'>Click the <strong>"Browse files"</strong> button above to pick a file from your laptop</p>
            </div>
            """, unsafe_allow_html=True)
            news_input = ""

    # ── Analyze Button ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        analyze_btn = st.button("🚀 Analyze Now", key="analyze")

    # Use session state as fallback if news_input is empty
    if not news_input.strip() and st.session_state.get("final_text", "").strip():
        news_input = st.session_state.final_text

    # ─── Analysis ───
    if analyze_btn and news_input.strip():
        if len(news_input.strip().split()) < 5:
            st.warning("⚠️ Please enter at least 5 words for accurate analysis.")
        else:
            with st.spinner("🤖 AI is analyzing the news... Please wait..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.015)
                    progress.progress(i + 1)

                label, confidence, method = detect_fake_news(news_input)
                word_count, sentence_count = get_word_stats(news_input)

            progress.empty()

            # Update session stats
            st.session_state.total_checked += 1
            if label == "FAKE":
                st.session_state.fake_count += 1
            else:
                st.session_state.real_count += 1

            # Add to history
            st.session_state.history.insert(0, {
                "text": news_input[:100] + "..." if len(news_input) > 100 else news_input,
                "label": label,
                "confidence": confidence,
                "time": datetime.now().strftime("%H:%M:%S"),
                "method": method
            })

            st.markdown("---")
            st.markdown("### 📊 Analysis Result")

            # Result display
            if label == "FAKE":
                st.markdown(f"""
                <div class='result-fake'>
                    <div class='result-emoji'>❌</div>
                    <p class='result-title'>FAKE NEWS</p>
                    <p class='confidence-text'>Confidence: {confidence*100:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='result-real'>
                    <div class='result-emoji'>✅</div>
                    <p class='result-title'>REAL NEWS</p>
                    <p class='confidence-text'>Confidence: {confidence*100:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)

            # Details
            st.markdown("### 📈 Detailed Analysis")
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("🏷️ Verdict", label)
            d2.metric("📊 Confidence", f"{confidence*100:.1f}%")
            d3.metric("📝 Word Count", word_count)
            d4.metric("📜 Sentences", sentence_count)

            st.markdown(f"""
            <div class='info-card'>
                <h4>🤖 Detection Method</h4>
                <p style='color:#ccc;'>{method}</p>
            </div>
            """, unsafe_allow_html=True)

            # Confidence bar
            st.markdown("### 📉 Confidence Breakdown")
            fake_val = confidence if label == "FAKE" else 1 - confidence
            real_val = confidence if label == "REAL" else 1 - confidence

            col_f, col_r = st.columns(2)
            with col_f:
                st.markdown("🔴 **Fake Probability**")
                st.progress(fake_val)
                st.markdown(f"**{fake_val*100:.1f}%**")
            with col_r:
                st.markdown("🟢 **Real Probability**")
                st.progress(real_val)
                st.markdown(f"**{real_val*100:.1f}%**")

    elif analyze_btn:
        if input_method == "📂 Upload File from Laptop":
            st.warning("⚠️ Please upload a file first from your laptop, then click Analyze Now.")
        else:
            st.warning("⚠️ Please enter or paste some text before analyzing.")


# ─── TAB 2: History ───
with tab2:
    st.markdown("### 📜 Analysis History")

    if not st.session_state.history:
        st.info("No analysis history yet. Go to the **Analyze News** tab to get started!")
    else:
        for i, item in enumerate(st.session_state.history):
            css_class = "history-item-fake" if item["label"] == "FAKE" else "history-item-real"
            icon = "❌" if item["label"] == "FAKE" else "✅"
            st.markdown(f"""
            <div class='{css_class}'>
                <strong>{icon} {item['label']}</strong> &nbsp;|&nbsp;
                Confidence: <strong>{item['confidence']*100:.1f}%</strong> &nbsp;|&nbsp;
                Time: {item['time']}<br>
                <span style='color:#ccc; font-size:0.85rem;'>{item['text']}</span>
            </div>
            """, unsafe_allow_html=True)


# ─── TAB 3: About ───
with tab3:
    st.markdown("### 📖 About This Project")

    st.markdown("""
    <div class='info-card'>
        <h4>🎓 Final Year Project</h4>
        <p style='color:#ccc;'>
        This is a Real-Time Fake News Detection System built as a Final Year Project 
        in Computer Science. It uses state-of-the-art NLP techniques and Transformer 
        models to classify news articles as genuine or misinformation.
        </p>
    </div>

    <div class='info-card'>
        <h4>🤖 AI Model Used</h4>
        <p style='color:#ccc;'>
        <strong>Primary:</strong> RoBERTa (Robustly Optimized BERT Approach) — 
        A transformer model fine-tuned on fake news datasets via HuggingFace.<br><br>
        <strong>Fallback:</strong> Rule-based NLP heuristic analysis using linguistic 
        patterns and keyword detection.
        </p>
    </div>

    <div class='info-card'>
        <h4>🛠️ Technologies Used</h4>
        <p style='color:#ccc;'>
        Python • Streamlit • HuggingFace Transformers • RoBERTa • 
        Natural Language Processing (NLP) • REST API
        </p>
    </div>

    <div class='info-card'>
        <h4>⚠️ Disclaimer</h4>
        <p style='color:#ccc;'>
        This tool is for educational purposes. AI predictions may not always be 100% accurate. 
        Always verify news from multiple reliable sources.
        </p>
    </div>
    """, unsafe_allow_html=True)
