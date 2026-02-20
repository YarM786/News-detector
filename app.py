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
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        font-size: 1rem !important;
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
    st.markdown("### 📝 Enter News Article or Text")

    news_input = st.text_area(
        label="",
        placeholder="Paste your news article, social media post, or any text here to check if it's real or fake...\n\nمثال: کوئی بھی خبر یہاں paste کریں...",
        height=220,
        key="news_input"
    )

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        analyze_btn = st.button("🚀 Analyze Now", key="analyze")

    # Example news buttons
    st.markdown("#### 💡 Try Example News:")
    ex_col1, ex_col2 = st.columns(2)

    with ex_col1:
        if st.button("📰 Example: Real News"):
            st.session_state["example_text"] = (
                "According to a new study published in the Journal of Science, researchers have found "
                "that regular exercise of at least 30 minutes per day significantly reduces the risk of "
                "cardiovascular disease. The study analyzed data from over 50,000 participants across "
                "10 countries over a period of 5 years. Experts say the findings confirm previous research "
                "and recommend moderate physical activity as part of a healthy lifestyle."
            )
            st.rerun()

    with ex_col2:
        if st.button("⚠️ Example: Fake News"):
            st.session_state["example_text"] = (
                "BREAKING: Shocking secret they don't want you to know! Scientists have been BANNED from "
                "telling the truth about miracle cure that cures all diseases overnight! The deep state is "
                "covering this up!! Share before this gets deleted! You won't believe what doctors are hiding "
                "from you. Wake up sheeple, this is 100% PROVEN and they lied to us all along!!!"
            )
            st.rerun()

    # Load example if selected
    if "example_text" in st.session_state:
        news_input = st.session_state.pop("example_text")
        st.text_area("Loaded Example:", value=news_input, height=150, key="loaded_example")

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
        st.warning("⚠️ Please enter some text before analyzing.")


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
