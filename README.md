# SiasatAI — Bilingual Misinformation Detection System

> An end-to-end Data Science and Machine Learning project for real-time fake news detection in **Bahasa Malaysia** and **English**, developed for **MBMB Melaka** as a final year project.

---

## 🔍 Overview

SiasatAI is a bilingual misinformation detection platform that combines a rigorously trained machine learning pipeline with a production-ready web application. The system is trained on **64,000+ bilingual articles** sourced from academic datasets and live-scraped portals, and achieves **93.99% accuracy** using a regularized Logistic Regression classifier selected through a multi-model tournament.

The application is optimized for CPU-only serverless hosting — it runs entirely on Vercel without any GPU dependency.

---

## ✨ Dashboard Features

### Core Analysis
| Feature | Description |
|---|---|
| **Real-time Prediction** | TF-IDF vectorization + Logistic Regression inference in under 2ms |
| **Bilingual Support** | Automatic language detection (Bahasa Malaysia / English) |
| **AI Confidence Score** | Animated gauge showing model prediction probability |
| **Sensationalism & Tone Meter** | Scores writing style from Neutral to Highly Sensational based on ALLCAPS ratio, exclamation density, and bilingual trigger keywords |
| **Word Cloud** | Canvas-rendered frequency visualization of the analyzed article |
| **Keyword Badges** | Top TF-IDF features detected in the submitted text |
| **AI Summary** | Human-readable bilingual explanation of the model's verdict |
| **Fact-Check Sources** | Persistent links to Sebenarnya.my, AFP, Reuters, and Bernama |

### Usability
| Feature | Description |
|---|---|
| **Verification History** | Saves last 50 analyses to `localStorage` — persists across page refreshes |
| **Quick Presets** | One-click sample texts (real and fake) in both languages |
| **Clipboard Paste** | Direct paste from clipboard with a single button |
| **Share Result** | Copies a formatted verdict summary to clipboard |
| **Dark / Light Mode** | Full theme toggle with persistent preference |

### Insights Panel
| Feature | Description |
|---|---|
| **Model Specifications** | Algorithm diagnostics, regularization parameters, vocabulary size, and last update timestamp |
| **Global Word Signals Chart** | Animated bar charts showing the top 5 words that drive "Fake" vs. "Real" predictions, derived from actual Logistic Regression coefficients |
| **Q&A Accordion** | Interactive FAQ explaining how the model works, what the confidence score means, and its limitations |
| **Feedback Form** | Categorized submission form (false alarm, missed rumor, suggestion) that sends reports asynchronously to Web3Forms, including the analyzed article and model verdict as context |

---

## 📊 ML Tournament Results

| Model | Accuracy |
|---|---|
| **Logistic Regression** 🏆 | **93.99%** |
| Support Vector Machine | 93.32% |
| XGBoost | 92.76% |
| Random Forest | 92.64% |

> **Why Logistic Regression?** Despite its simplicity, it outperformed all tree-based and kernel-based models on this high-dimensional TF-IDF feature space. Its regularization (`L2, C=0.15`) prevents domain bias, and the exported model weighs only ~5MB — making it ideal for serverless CPU-only environments.

---

## 🏗️ Architecture

```
SiasatAI/
├── app/
│   ├── main.py              # FastAPI backend — prediction, sensationalism scoring, model info
│   └── static/
│       ├── index.html       # Single-page dashboard
│       ├── style.css        # Design system (dark/light mode, glassmorphism)
│       └── app.js           # Frontend logic, chart rendering, Web3Forms integration
│
├── api/
│   └── index.py             # Vercel serverless function handler
│
├── data/
│   ├── raw/                 # Raw scraped & downloaded datasets
│   └── clean/               # Cleaned CSVs & Power BI dashboard exports
│       ├── data_clean.csv
│       ├── Misinformation_Analysis_Dashboard.csv
│       └── Fake_News_Keyword_Importance.csv
│
├── models/                  # Trained model assets (~5MB total)
│   ├── model.pkl            # Logistic Regression champion
│   ├── vectorizer.pkl       # TF-IDF vectorizer (10k features, 1–3 n-grams)
│   └── label_encoder.pkl    # Label encoder
│
├── notebooks/
│   └── data_preprocessing_and_training.ipynb   # Self-contained end-to-end pipeline
│
├── static/                  # Generated charts & visualizations
│
├── vercel.json              # Vercel routing configuration
├── requirements.txt
├── run_retrain.py           # Console pipeline runner (real-time progress bars)
└── retrain.bat              # Windows double-click helper for retraining
```

---

## 🚀 Running Locally

### 1. Set Up Environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch the Web Application

```bash
python app/main.py
```

Visit `http://127.0.0.1:8000` to access the dashboard.

### 3. Retrain the Model

To scrape fresh articles from *Sebenarnya.my* and retrain the model with the latest data:

```bash
# Windows (double-click or terminal)
retrain.bat

# macOS / Linux / any terminal
python run_retrain.py
```

This executes the self-contained Jupyter Notebook pipeline in your console with real-time `tqdm` progress bars, and automatically:
- Scrapes and merges new fake news articles
- Re-runs bilingual NLP cleaning and TF-IDF vectorization
- Re-runs the multi-model tournament and selects the new champion
- Exports updated `model.pkl`, `vectorizer.pkl`, and `label_encoder.pkl`
- Regenerates Power BI CSVs and evaluation charts

---

## ☁️ Deployment on Vercel

The application is pre-configured for zero-setup deployment on **Vercel**:

- `vercel.json` routes `/api/*` to the Python serverless function at `api/index.py`
- All other routes serve static files from `app/static/` via Vercel's global CDN
- No environment variables required — the model files are committed directly

**Deploy steps:**
1. Push this repository to GitHub
2. Import the project at [vercel.com](https://vercel.com)
3. Click **Deploy** — Vercel handles the rest

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/predict` | Analyze text — returns prediction, confidence, sensationalism score, word cloud, keywords, summary, and fact-check sources |
| `GET` | `/api/model_info` | Returns top 5 "Fake" and "Real" word features with Logistic Regression coefficient weights |

---

## 🗃️ Data Sources

| Source | Language | Articles |
|---|---|---|
| Academic Malay NLP Dataset (Bernama, Awani, Sinar Harian, MalCov) | Bahasa Malaysia | ~22,000 |
| Global English Fake News Dataset (Hugging Face / Kaggle) | English | ~40,000 |
| Live-scraped articles from [Sebenarnya.my](https://sebenarnya.my) | Bahasa Malaysia | ~2,000+ |

---

## 👥 Stakeholders

Developed as a **Final Year Data Science Project** with use-case context provided for **Majlis Bandaraya Melaka Bersejarah (MBMB)**.
