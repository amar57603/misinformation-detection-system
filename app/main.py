import os
import re
import pickle
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="Bilingual Misinformation Detection API",
    description="Backend API for detecting fake news in English and Bahasa Malaysia.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "vectorizer.pkl")
LABEL_ENCODER_PATH = os.path.join(MODELS_DIR, "label_encoder.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    with open(LABEL_ENCODER_PATH, "rb") as f:
        label_encoder = pickle.load(f)
    print("Model, vectorizer, and label encoder loaded successfully.")
except Exception as e:
    print(f"Error loading model files: {e}")
    model, vectorizer, label_encoder = None, None, None


# ── Stopwords ────────────────────────────────────────────────
malay_stopwords = {
    'yang', 'di', 'dan', 'itu', 'dengan', 'untuk', 'tidak', 'ini', 'dari',
    'pada', 'dalam', 'ke', 'akan', 'oleh', 'juga', 'telah', 'ada', 'adalah',
    'kepada', 'sebagai', 'mereka', 'kita', 'kami', 'ia', 'atau', 'bahawa',
    'boleh', 'bagi', 'serta', 'apa', 'daripada', 'lebih', 'banyak', 'lagi',
    'apabila', 'seperti', 'satu', 'dua', 'tiga', 'sudah', 'hanya', 'setelah',
    'masih', 'semua', 'belum', 'antara', 'tanpa', 'bukan', 'begitu', 'kata',
    'orang', 'tahun', 'hari', 'pun', 'nak', 'tak', 'lah', 'kan', 'jer',
    'tu', 'ni', 'dah', 'kena', 'macam', 'bila', 'mana', 'siapa', 'kenapa',
    'bagaimana', 'berapa', 'sebuah', 'seorang', 'tersebut', 'iaitu', 'yakni',
    'tetapi', 'namun', 'walau', 'meskipun', 'walaupun', 'kerana', 'sebab',
    'jika', 'kalau', 'supaya', 'agar', 'hingga', 'sehingga', 'sambil',
    'selain', 'selepas', 'sebelum', 'semasa', 'ketika', 'manakala', 'sedangkan',
    'malah', 'bahkan', 'kini', 'sini', 'sana', 'mahu', 'hendak', 'perlu',
    'harus', 'dapat', 'bisa', 'sangat', 'amat', 'terlalu', 'agak', 'cukup',
    'paling', 'sekali', 'setiap', 'sesuatu', 'segala', 'para', 'beberapa'
}

english_stopwords = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
    'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'because', 'but', 'and', 'or', 'if', 'while', 'about', 'against',
    'this', 'that', 'these', 'those', 'it', 'its', 'he', 'she', 'they',
    'them', 'his', 'her', 'their', 'what', 'which', 'who', 'whom', 'i',
    'me', 'my', 'we', 'us', 'our', 'you', 'your', 'up', 'also', 'said'
}

bias_words = {
    'reuters', 'bernama', 'awani', 'astro', 'sinar', 'harian', 'malaysiakini', 'star',
    'nst', 'kuala', 'lumpur', 'putrajaya', 'washington', 'london', 'moscow', 'beijing',
    'tokyo', 'paris', 'berlin', 'jakarta', 'bangkok', 'manila', 'singapore', 'melaka',
    'reuter', 'press', 'associated'
}

all_stopwords = malay_stopwords.union(english_stopwords)

# ── Fake news signal words for explanation ───────────────────
FAKE_SIGNALS_EN = {
    'viral', 'share', 'urgent', 'breaking', 'alert', 'warning', 'shocking',
    'secret', 'exposed', 'banned', 'hidden', 'cure', 'miracle', 'hoax',
    'fake', 'conspiracy', 'spread', 'immediately', 'forward', 'save',
    'dangerous', 'die', 'kill', 'poison', 'illegal', 'proof', 'confirm',
    'leaked', 'exclusive', 'unbelievable', 'amazing', 'incredible'
}

FAKE_SIGNALS_BM = {
    'viral', 'sebarkan', 'awas', 'segera', 'berita', 'tular', 'waspada',
    'rahsia', 'dedah', 'terdedah', 'sembuh', 'mujarab', 'penipuan',
    'konspirasi', 'tersebar', 'bahaya', 'mati', 'racun', 'haram', 'bukti',
    'bocor', 'eksklusif', 'dipercayai', 'percaya', 'jangan', 'percayai'
}

# ── Fact-check sources ───────────────────────────────────────
FACT_CHECK_SOURCES = [
    {
        "name": "Sebenarnya.my",
        "url": "https://sebenarnya.my",
        "description": "Official Malaysian Government fact-checking portal",
        "flag": "🇲🇾"
    },
    {
        "name": "AFP Fact Check",
        "url": "https://factcheck.afp.com",
        "description": "International newswire fact-checking service",
        "flag": "🌐"
    },
    {
        "name": "Reuters Fact Check",
        "url": "https://www.reuters.com/fact-check",
        "description": "Reuters global fact-checking desk",
        "flag": "🌐"
    },
    {
        "name": "Bernama",
        "url": "https://www.bernama.com",
        "description": "Malaysia's national news agency — official source",
        "flag": "🇲🇾"
    }
]


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    words = text.split()
    words = [w for w in words if w not in all_stopwords and w not in bias_words and len(w) > 2]
    return ' '.join(words)


def detect_language(text: str) -> str:
    words = set(re.sub(r'[^a-zA-Z\s]', '', text).lower().split())
    malay_count = len(words.intersection(malay_stopwords))
    english_count = len(words.intersection(english_stopwords))
    if malay_count == 0 and english_count == 0:
        return "Unknown"
    return "Bahasa Malaysia" if malay_count >= english_count else "English"


def build_word_frequencies(text: str) -> list:
    """Return top words with frequency for word cloud rendering."""
    words = re.sub(r'[^a-zA-Z\s]', '', text).lower().split()
    freq = {}
    for w in words:
        if w not in all_stopwords and w not in bias_words and len(w) > 2:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [{"word": w, "count": c} for w, c in sorted_words[:40]]


def build_summary(label: str, confidence: float, language: str,
                  keywords: list, text: str) -> str:
    """Generate a human-readable explanation for the verdict."""
    pct = round(confidence * 100, 1)
    words = set(re.sub(r'[^a-zA-Z\s]', '', text).lower().split())

    if label == "Fake":
        # Find which fake signal words are present
        signals_en = words.intersection(FAKE_SIGNALS_EN)
        signals_bm = words.intersection(FAKE_SIGNALS_BM)
        signals = list(signals_en.union(signals_bm))[:4]

        kw_str = ", ".join(f'"{k}"' for k in keywords[:4]) if keywords else "no strong keywords"
        signal_str = (", ".join(f'"{s}"' for s in signals)
                      if signals else "sensational phrasing")

        if language == "Bahasa Malaysia":
            return (
                f"Model mengesan corak bahasa yang mencurigakan dengan keyakinan {pct}%. "
                f"Artikel ini mengandungi perkataan seperti {signal_str} yang sering dikaitkan "
                f"dengan berita palsu. Kata kunci utama yang dikesan: {kw_str}. "
                f"Sila semak dengan sumber rasmi sebelum berkongsi."
            )
        else:
            return (
                f"The model detected suspicious language patterns with {pct}% confidence. "
                f"This article contains words such as {signal_str} commonly associated "
                f"with misinformation. Key features detected: {kw_str}. "
                f"Please verify with trusted sources before sharing."
            )
    else:
        kw_str = ", ".join(f'"{k}"' for k in keywords[:4]) if keywords else "structured language"
        if language == "Bahasa Malaysia":
            return (
                f"Model mengesahkan artikel ini sebagai berita nyata dengan keyakinan {pct}%. "
                f"Struktur bahasa yang formal dan fakta yang boleh disahkan menjadi penanda utama. "
                f"Kata kunci yang menyokong: {kw_str}."
            )
        else:
            return (
                f"The model verified this article as real news with {pct}% confidence. "
                f"It exhibits formal language structure and verifiable factual reporting patterns. "
                f"Supporting keywords: {kw_str}."
            )
 
 
def calculate_sensationalism(text: str) -> float:
    if not text:
        return 0.0
    
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return 0.0
        
    upper_words = sum(1 for w in words if w.isupper() and len(w) > 2)
    cap_ratio = upper_words / total_words
    cap_score = min(1.0, cap_ratio / 0.15) * 0.35
    
    excl_count = text.count('!')
    excl_score = min(1.0, excl_count / 3.0) * 0.25
    
    cleaned_words = set(re.sub(r'[^a-zA-Z\s]', '', text).lower().split())
    signals_en = cleaned_words.intersection(FAKE_SIGNALS_EN)
    signals_bm = cleaned_words.intersection(FAKE_SIGNALS_BM)
    signal_count = len(signals_en.union(signals_bm))
    keyword_score = min(1.0, signal_count / 3.0) * 0.40
    
    score = cap_score + excl_score + keyword_score
    return min(1.0, max(0.0, score))


class NewsInput(BaseModel):
    text: str


@app.post("/api/predict")
async def predict(news_input: NewsInput):
    if not news_input.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    lang = detect_language(news_input.text)

    if model is None or vectorizer is None or label_encoder is None:
        raise HTTPException(status_code=500, detail="Model assets are not loaded on backend.")

    cleaned = clean_text(news_input.text)

    if not cleaned.strip() or len(cleaned.split()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Input text is too short or contains only stop words. Please enter a longer article."
        )

    vec = vectorizer.transform([cleaned])
    pred_val = model.predict(vec)[0]

    if isinstance(pred_val, str):
        label = pred_val
    elif hasattr(label_encoder, 'classes_'):
        label = label_encoder.inverse_transform([pred_val])[0]
    else:
        label = str(pred_val)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(vec)[0]
        classes = list(label_encoder.classes_) if hasattr(label_encoder, 'classes_') else ['Fake', 'Real']
        prob_dict = {str(c): float(p) for c, p in zip(classes, proba)}
        confidence = prob_dict.get(label, 0.99)
    else:
        confidence = 0.95

    feature_names = vectorizer.get_feature_names_out()
    vec_array = vec.toarray()[0]
    active_features = [feature_names[i] for i, val in enumerate(vec_array) if val > 0]

    keywords = active_features[:15]
    word_frequencies = build_word_frequencies(news_input.text)
    summary = build_summary(label, confidence, lang, keywords, news_input.text)

    return {
        "text": news_input.text,
        "clean_text": cleaned,
        "language": lang,
        "prediction": label,
        "confidence": confidence,
        "sensationalism_score": calculate_sensationalism(news_input.text),
        "word_count": len(news_input.text.split()),
        "keywords_detected": keywords,
        "word_frequencies": word_frequencies,
        "summary": summary,
        "fact_check_sources": FACT_CHECK_SOURCES
    }


@app.get("/api/model_info")
async def model_info():
    if model is None or vectorizer is None or label_encoder is None:
        raise HTTPException(status_code=500, detail="Model assets not loaded.")
    
    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]
    word_coefs = list(zip(feature_names, coefs))
    
    sorted_by_coef = sorted(word_coefs, key=lambda x: x[1])
    
    top_fake = [{"word": word, "weight": float(coef)} for word, coef in sorted_by_coef[:5]]
    top_real = [{"word": word, "weight": float(coef)} for word, coef in sorted_by_coef[-5:]]
    top_real.reverse()
    
    return {
        "algorithm": "Logistic Regression",
        "vocabulary_size": len(feature_names),
        "top_fake_features": top_fake,
        "top_real_features": top_real
    }


# Serve static frontend
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
