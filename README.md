# Digital Crisis and Misinformation Detection System

A Data Science and Machine Learning project developed to detect misinformation and fake news in both **Bahasa Malaysia** and **English**. The system leverages 64,000+ bilingual articles from academic datasets and live-scraped sources, processes text using advanced NLP (N-grams), and selects the best-performing classifier via a multi-model tournament.

---

## 💻 Misinformation Detection Dashboard

The system features a web application that loads our trained machine learning models to perform real-time bilingual misinformation verification.

### Key Features:
- **Real-time Inference:** Directly runs clean tokenization, TF-IDF vectorization, and model predictions on the input text.
- **Bilingual & Language Detection:** Automatically identifies if the text is English or Bahasa Malaysia.
- **Interactive Preset Bank:** Single-click buttons to load official vs. rumored sample messages to test the model immediately.
- **Verification History Storage:** Automatically saves previous analysis runs (verdict, language, confidence, text snippet) to the browser's `localStorage`. You can reload a past verification or delete it from history, even after refreshing the page!
- **Fast and Secure Serverless Design:** Optimized for CPU-only serverless deployment (e.g., on Vercel) by separating predictions from training processes.

---

## 📊 Project Architecture

The project consists of three main modules:

1. **Jupyter Notebook (`/notebooks`)**
   - **Data Collection:** Combined 64,000+ articles from Academic Malay NLP Dataset (Bernama, Astro Awani, Sinar Harian, MalCov), Global English Fake News Dataset (Hugging Face), and live-scraped articles from `sebenarnya.my`.
   - **Preprocessing:** Bilingual NLP cleaning (Malay & English stopwords), regex normalization, and text vectorization using TF-IDF with Bi-grams.
   - **Model Training:** Multi-model tournament (XGBoost, SVM, Logistic Regression, Random Forest) with automatic champion selection.

2. **Web Application (`/app`)**
   - A FastAPI backend served with a glassmorphism frontend dashboard to verify input articles.

3. **Data Pipeline Notebook (`/notebooks`)**
   - The Jupyter Notebook contains the complete end-to-end data pipeline: web scraping of Sebenarnya.my, preprocessing/tokenization, model training tournament, model exports, and chart generation.

---

## 📁 Folder Structure

```text
DataScience/
├── app/                  # Web Application backend and frontend assets
│   ├── main.py           # FastAPI backend server
│   └── static/           # Dashboard static pages (HTML, CSS, JS)
├── data/                 
│   ├── clean/            # Cleaned datasets & Power BI dashboard sources
│   │   ├── data_clean.csv
│   │   ├── Misinformation_Analysis_Dashboard.csv
│   │   └── Fake_News_Keyword_Importance.csv
│   └── raw/              # Raw scraped & downloaded datasets
├── models/               # Exported ML champion models (.pkl)
│   ├── model.pkl
│   ├── vectorizer.pkl
│   └── label_encoder.pkl
├── notebooks/            # Jupyter Notebooks for experimentation
│   └── data_preprocessing_and_training.ipynb
├── static/               # Generated charts & visualizations
│   ├── model_results.png
│   └── feature_importance.png
├── .gitignore
├── requirements.txt
├── README.md
└── retrain.bat           # Windows helper to run the notebook and update models/charts
```

---

## 🚀 How to Run Locally

### 1. Setup Environment
```bash
python -m venv .venv
# Activate environment (Windows)
.\.venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Web Application
```bash
python app/main.py
```
Open your browser and navigate to `http://127.0.0.1:8000` to access the dashboard.

### 3. Update Datasets & Retrain Models
To fetch fresh fake news from *Sebenarnya.my* and retrain the model locally:
* **On Windows:** Double-click the `retrain.bat` helper in the root directory.
* **On macOS/Linux/CLI:** Run the helper script from your terminal:
  ```bash
  python run_retrain.py
  ```
This executes the self-contained pipeline directly in your console (displaying real-time progress bars), updates the model files under `/models`, updates Power BI sheets, and regenerates charts under `/static`.

---

## 📈 ML Tournament Results

| Model | Accuracy |
|-------|----------|
| Logistic Regression 🏆 | **93.99%** |
| Support Vector Machine | 93.32% |
| XGBoost | 92.76% |
| Random Forest | 92.64% |

---

## 👥 Stakeholders
Developed as a Final Project with context provided for **MBMB Melaka**.

---

## ☁️ Deployment on Vercel

The application is configured for one-click deployment on **Vercel** using `@vercel/python` serverless runtimes:
* **API Routing:** Route `/api/*` is handled by the serverless function `api/index.py` (which loads the FastAPI app from `app/main.py`).
* **Static Assets Routing:** All other paths route directly to the glassmorphism frontend files under `app/static/` served globally via Vercel's CDN.
* **Deploy Steps:**
  1. Push the repository to GitHub.
  2. Import the project on Vercel.
  3. Click **Deploy**. Vercel will automatically configure the Python environment and static routing according to `vercel.json`.
