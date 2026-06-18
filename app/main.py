import os
import re
import pickle
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to sys.path to resolve any absolute imports correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="Bilingual Misinformation Detection API",
    description="Backend API for detecting fake news in English and Bahasa Malaysia.",
    version="1.0.0"
)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths to model files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(MODELS_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "vectorizer.pkl")
LABEL_ENCODER_PATH = os.path.join(MODELS_DIR, "label_encoder.pkl")

# Load model assets
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


# Bilingual Stopwords (matches training notebook)
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
    
    return {
        "text": news_input.text,
        "clean_text": cleaned,
        "language": lang,
        "prediction": label,
        "confidence": confidence,
        "word_count": len(news_input.text.split()),
        "keywords_detected": active_features[:15]
    }


# Serve static frontend folder (app/static)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
