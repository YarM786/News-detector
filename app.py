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
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }
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
    .result-emoji { font-size: 4rem; }
    .confidence-text {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
    }
    .info-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
    }
    .info-card h4 { color: #f093fb; margin-bottom: 0.5rem; }
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
    }
    .stTextArea textarea::placeholder {
        color: rgba(180, 160, 220, 0.6) !important;
        -webkit-text-fill-color: rgba(180, 160, 220, 0.6) !important;
        font-style: italic !important;
    }
    .stTextArea textarea:focus {
        border-color: #f093fb !important;
        box-shadow: 0 0 12px rgba(240, 147, 251, 0.3) !important;
    }
    p, span, div, h1, h2, h3, h4, h5, label { color: #ffffff; }
    .stTextInput input {
        background: rgba(30, 20, 60, 0.95) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1.5px solid rgba(240, 147, 251, 0.5) !important;
        border-radius: 10px !important;
    }
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
    [data-testid="stFileUploader"] label { color: #f093fb !important; font-weight: 600 !important; }
    [data-testid="stFileUploader"] span { color: #ccbbee !important; }
    .stRadio label { color: #ffffff !important; font-size: 1rem !important; }
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
    text = text.strip()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def detect_language(text):
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if urdu_chars > 10:
        return "urdu"
    return "english"


def try_model(api_url, text, timeout=25):
    headers = {"Content-Type": "application/json"}
    payload = {"inputs": text[:512]}
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def parse_result(result):
    if not result:
        return None, None
    try:
        predictions = result[0] if isinstance(result[0], list) else result
        label_map = {}
        for item in predictions:
            label_map[item['label'].upper()] = item['score']

        fake_score = 0
        real_score = 0

        for key, val in label_map.items():
            if any(f in key for f in ['FAKE', 'LABEL_1', 'FALSE', 'MISINFORMATION', 'UNRELIABLE']):
                fake_score = max(fake_score, val)
            elif any(r in key for r in ['REAL', 'LABEL_0', 'TRUE', 'RELIABLE', 'LEGITIMATE']):
                real_score = max(real_score, val)

        if fake_score == 0 and real_score == 0:
            fake_score = label_map.get('NEGATIVE', label_map.get('NEG', 0))
            real_score = label_map.get('POSITIVE', label_map.get('POS', 0))

        if fake_score == 0 and real_score == 0:
            return None, None

        if fake_score > real_score:
            return "FAKE", fake_score
        else:
            return "REAL", real_score
    except Exception:
        return None, None


def analyze_with_huggingface(text):
    # MODEL 1: XLM-RoBERTa Large — Facebook (100+ Languages)
    result1 = try_model(
        "https://api-inference.huggingface.co/models/facebook/xlm-roberta-large-xnli",
        text
    )
    label, confidence = parse_result(result1)
    if label:
        return label, confidence, "🌍 XLM-RoBERTa Large — Facebook (100+ Languages)"

    # MODEL 2: Multilingual Fake News BERT
    result2 = try_model(
        "https://api-inference.huggingface.co/models/dlenafv/fakenews-multilang-bert",
        text
    )
    label, confidence = parse_result(result2)
    if label:
        return label, confidence, "🤖 Multilingual BERT Fake News Detector"

    # MODEL 3: Fake News BERT
    result3 = try_model(
        "https://api-inference.huggingface.co/models/jy46604790/Fake-News-Bert-Detect",
        text
    )
    label, confidence = parse_result(result3)
    if label:
        return label, confidence, "🧠 Fake News BERT Detector"

    # MODEL 4: XLM-R Fine-tuned on Fake News
    result4 = try_model(
        "https://api-inference.huggingface.co/models/DGurgurov/xlm-r_fakenews",
        text
    )
    label, confidence = parse_result(result4)
    if label:
        return label, confidence, "🔬 XLM-R Fake News Fine-tuned Model"

    # MODEL 5: Multilingual Fallback
    result5 = try_model(
        "https://api-inference.huggingface.co/models/Narrativaai/fake-news-detection-spanish-en",
        text
    )
    label, confidence = parse_result(result5)
    if label:
        return label, confidence, "🌐 Narrativa Multilingual Model"

    return None, None, None


def rule_based_analysis(text):
    text_lower = text.lower()
    words = text.split()

    fake_indicators = [
        "you won't believe", "they don't want you to know",
        "share before deleted", "wake up sheeple", "crisis actor",
        "miracle cure", "doctors hate", "100% proven",
        "scientists baffled", "they lied to us", "fake media",
        "illuminati", "click here now", "hoax", "coverup conspiracy",
        "banned video", "deep state hiding"
    ]

    real_indicators = [
        "according to", "reported by", "confirmed by", "said in a statement",
        "official statement", "press release", "sources say", "told dawn",
        "told the media", "told reporters", "in a statement",
        "study shows", "researchers found", "data shows", "survey found",
        "published in", "peer reviewed", "experts say", "statistics show",
        "dawn.com", "geo news", "ary news", "the news", "express tribune",
        "bbc urdu", "radio pakistan", "app news agency", "ispr",
        "prime minister", "chief minister", "federal cabinet",
        "national assembly", "senate", "supreme court", "high court",
        "election commission", "state bank of pakistan", "imf", "world bank",
        "ministry of", "spokesperson", "foreign office",
        "islamabad", "karachi", "lahore", "peshawar", "quetta",
        "balochistan", "sindh", "punjab", "pakistan", "waziristan"
    ]

    fake_count = sum(1 for phrase in fake_indicators if phrase in text_lower)
    real_count = sum(1 for phrase in real_indicators if phrase in text_lower)

    exclamation = text.count('!')
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
    word_count = len(words)
    length_bonus = 0.3 if word_count > 150 else 0.1 if word_count > 80 else 0.0

    fake_score = (fake_count * 0.4) + (exclamation * 0.08) + (caps_words * 0.04)
    real_score = (real_count * 0.2) + length_bonus

    fake_score = min(fake_score, 0.95)
    real_score = min(real_score, 0.95)

    if fake_score == 0 and real_score == 0:
        fake_score = 0.25 if word_count > 100 else 0.50
        real_score = 0.75 if word_count > 100 else 0.50

    total = fake_score + real_score
    fake_score /= total
    real_score /= total

    if fake_score > real_score:
        return "FAKE", fake_score
    else:
        return "REAL", real_score


def detect_fake_news(text):
    cleaned = preprocess_text(text)
    lang = detect_language(cleaned)
    label, confidence, model_name = analyze_with_huggingface(cleaned)
    if label is None:
        label, confidence = rule_based_analysis(cleaned)
        method = "⚙️ Rule-Based Analysis (Offline Mode)"
    else:
        method = f"{model_name} | Language: {lang.upper()}"
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
if "final_text" not in st.session_state:
    st.session_state.final_text = ""


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
    st.markdown("### 🌍 AI Models Used")
    st.markdown("""
    <div class='info-card'>
        <h4>Model 1</h4>
        <p style='color:#ccc; font-size:0.82rem;'>XLM-RoBERTa Large by Facebook — 100+ Languages</p>
    </div>
    <div class='info-card'>
        <h4>Model 2</h4>
        <p style='color:#ccc; font-size:0.82rem;'>Multilingual BERT Fake News</p>
    </div>
    <div class='info-card'>
        <h4>Model 3</h4>
        <p style='color:#ccc; font-size:0.82rem;'>Fake News BERT Detector</p>
    </div>
    <div class='info-card'>
        <h4>Model 4</h4>
        <p style='color:#ccc; font-size:0.82rem;'>XLM-R Fine-tuned Fake News</p>
    </div>
    <div class='info-card'>
        <h4>Model 5</h4>
        <p style='color:#ccc; font-size:0.82rem;'>Narrativa Multilingual Model</p>
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
    st.markdown("<p style='color:#666; font-size:0.75rem; text-align:center;'>Final Year Project<br>Fake News Detection System<br>NLP & Transformers</p>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────
st.markdown('<h1 class="main-title">🔍 Real-Time Fake News Detector</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by 5 Multilingual AI Models | Supports 100+ Languages</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔎 Analyze News", "📜 History", "📖 About"])

# ─── TAB 1 ───
with tab1:
    st.markdown("### 📥 Choose Input Method")
    input_method = st.radio(
        "",
        ["✍️ Type / Paste Text", "📂 Upload File from Laptop"],
        horizontal=True,
        key="input_method"
    )

    news_input = ""

    # ── Text Input ──
    if input_method == "✍️ Type / Paste Text":
        st.markdown("### 📝 Enter News Article or Text")

        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            if st.button("📰 Load Real News Example"):
                st.session_state.final_text = (
                    "According to a new study published in the Journal of Science, researchers found "
                    "that regular exercise of at least 30 minutes per day significantly reduces the risk "
                    "of cardiovascular disease. The study analyzed data from over 50,000 participants "
                    "across 10 countries. Experts say findings confirm previous research and recommend "
                    "moderate physical activity as part of a healthy lifestyle."
                )
        with ex_col2:
            if st.button("⚠️ Load Fake News Example"):
                st.session_state.final_text = (
                    "BREAKING: Shocking secret they don't want you to know! Scientists have been BANNED "
                    "from telling the truth about miracle cure that cures all diseases overnight! "
                    "Share before this gets deleted! Wake up sheeple, this is 100% PROVEN!"
                )

        news_input = st.text_area(
            label="✏️ Type or Paste your news article here:",
            value=st.session_state.final_text,
            placeholder="Paste news article here... کوئی بھی خبر یہاں paste کریں...",
            height=250,
            key="news_text_area"
        )
        st.session_state.final_text = news_input

    # ── File Upload ──
    else:
        st.markdown("### 📂 Upload News Article from Your Laptop")
        st.markdown("""
        <div class='info-card'>
            <h4>📋 Supported File Types</h4>
            <p style='color:#ccc; font-size:0.9rem;'>
            ✅ .txt &nbsp;|&nbsp; ✅ .pdf &nbsp;|&nbsp; ✅ .docx &nbsp;|&nbsp; ✅ .csv
            </p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "📁 Click 'Browse files' to select from your laptop",
            type=["txt", "pdf", "docx", "csv"],
            accept_multiple_files=False,
            key="file_uploader"
        )

        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            file_ext = file_name.split(".")[-1].lower()

            st.markdown(f"""
            <div class='info-card'>
                <h4>✅ File Loaded!</h4>
                <p style='color:#ccc;'>
                📁 <strong>{file_name}</strong> &nbsp;|&nbsp;
                📦 {file_size/1024:.1f} KB &nbsp;|&nbsp;
                🔖 {file_ext.upper()}
                </p>
            </div>
            """, unsafe_allow_html=True)

            extracted_text = ""
            try:
                import io
                if file_ext == "txt":
                    extracted_text = uploaded_file.read().decode("utf-8", errors="ignore")
                elif file_ext == "pdf":
                    try:
                        import PyPDF2
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        for page in pdf_reader.pages:
                            extracted_text += page.extract_text() or ""
                    except ImportError:
                        st.error("❌ Run: pip install PyPDF2")
                elif file_ext == "docx":
                    try:
                        import docx
                        doc = docx.Document(io.BytesIO(uploaded_file.read()))
                        extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    except ImportError:
                        st.error("❌ Run: pip install python-docx")
                elif file_ext == "csv":
                    try:
                        import pandas as pd
                        df = pd.read_csv(io.BytesIO(uploaded_file.read()))
                        text_cols = df.select_dtypes(include="object").columns.tolist()
                        if text_cols:
                            extracted_text = " ".join(df[text_cols[0]].dropna().astype(str).tolist())
                    except ImportError:
                        st.error("❌ Run: pip install pandas")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

            if extracted_text.strip():
                st.session_state.final_text = extracted_text
                news_input = extracted_text
                st.success(f"✅ {len(extracted_text.split())} words extracted!")
                st.markdown(f"""
                <div style='background:rgba(30,20,60,0.95); border:1.5px solid rgba(240,147,251,0.5);
                border-radius:12px; padding:1.2rem; max-height:200px; overflow-y:auto;
                color:#ffffff; font-size:0.9rem; -webkit-text-fill-color:#ffffff;'>
                {extracted_text[:800]}{"..." if len(extracted_text) > 800 else ""}
                </div>""", unsafe_allow_html=True)

                edited = st.text_area("✏️ Edit if needed:", value=extracted_text, height=120, key="edited_text")
                news_input = edited
                st.session_state.final_text = edited
        else:
            st.markdown("""
            <div style='background:rgba(30,20,60,0.7); border:2px dashed rgba(240,147,251,0.4);
            border-radius:14px; padding:2.5rem; text-align:center; color:#ccbbee;'>
                <p style='font-size:3rem; margin:0;'>📂</p>
                <p style='font-size:1rem;'>Click "Browse files" to pick a file from your laptop</p>
            </div>""", unsafe_allow_html=True)

    # ── Analyze Button ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        analyze_btn = st.button("🚀 Analyze Now", key="analyze")

    if not news_input.strip() and st.session_state.get("final_text", "").strip():
        news_input = st.session_state.final_text

    # ── Result ──
    if analyze_btn and news_input.strip():
        if len(news_input.strip().split()) < 5:
            st.warning("⚠️ Please enter at least 5 words.")
        else:
            with st.spinner("🤖 AI Models analyzing... Please wait..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.015)
                    progress.progress(i + 1)
                label, confidence, method = detect_fake_news(news_input)
                word_count, sentence_count = get_word_stats(news_input)
            progress.empty()

            st.session_state.total_checked += 1
            if label == "FAKE":
                st.session_state.fake_count += 1
            else:
                st.session_state.real_count += 1

            st.session_state.history.insert(0, {
                "text": news_input[:100] + "..." if len(news_input) > 100 else news_input,
                "label": label,
                "confidence": confidence,
                "time": datetime.now().strftime("%H:%M:%S"),
                "method": method
            })

            st.markdown("---")
            st.markdown("### 📊 Analysis Result")

            if label == "FAKE":
                st.markdown(f"""
                <div class='result-fake'>
                    <div class='result-emoji'>❌</div>
                    <p class='result-title'>FAKE NEWS</p>
                    <p class='confidence-text'>Confidence: {confidence*100:.1f}%</p>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='result-real'>
                    <div class='result-emoji'>✅</div>
                    <p class='result-title'>REAL NEWS</p>
                    <p class='confidence-text'>Confidence: {confidence*100:.1f}%</p>
                </div>""", unsafe_allow_html=True)

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("🏷️ Verdict", label)
            d2.metric("📊 Confidence", f"{confidence*100:.1f}%")
            d3.metric("📝 Words", word_count)
            d4.metric("📜 Sentences", sentence_count)

            st.markdown(f"""
            <div class='info-card'>
                <h4>🤖 Detection Method</h4>
                <p style='color:#ccc;'>{method}</p>
            </div>""", unsafe_allow_html=True)

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
            st.warning("⚠️ Please upload a file first.")
        else:
            st.warning("⚠️ Please enter some text before analyzing.")


# ─── TAB 2: History ───
with tab2:
    st.markdown("### 📜 Analysis History")
    if not st.session_state.history:
        st.info("No history yet. Go to Analyze tab to get started!")
    else:
        for item in st.session_state.history:
            css_class = "history-item-fake" if item["label"] == "FAKE" else "history-item-real"
            icon = "❌" if item["label"] == "FAKE" else "✅"
            st.markdown(f"""
            <div class='{css_class}'>
                <strong>{icon} {item['label']}</strong> &nbsp;|&nbsp;
                Confidence: <strong>{item['confidence']*100:.1f}%</strong> &nbsp;|&nbsp;
                {item['time']}<br>
                <span style='color:#ccc; font-size:0.85rem;'>{item['text']}</span>
            </div>""", unsafe_allow_html=True)


# ─── TAB 3: About ───
with tab3:
    st.markdown("### 📖 About This Project")
    st.markdown("""
    <div class='info-card'>
        <h4>🎓 Final Year Project</h4>
        <p style='color:#ccc;'>Real-Time Fake News Detection System using NLP and Transformer Models.</p>
    </div>
    <div class='info-card'>
        <h4>🌍 Multilingual Support</h4>
        <p style='color:#ccc;'>Uses 5 AI models including Facebook XLM-RoBERTa that supports 100+ languages
        including Urdu, Arabic, Hindi, English, and more.</p>
    </div>
    <div class='info-card'>
        <h4>🛠️ Technologies</h4>
        <p style='color:#ccc;'>Python • Streamlit • HuggingFace • XLM-RoBERTa • BERT • NLP</p>
    </div>
    <div class='info-card'>
        <h4>⚠️ Disclaimer</h4>
        <p style='color:#ccc;'>For educational purposes. Always verify news from reliable sources.</p>
    </div>
    """, unsafe_allow_html=True)
