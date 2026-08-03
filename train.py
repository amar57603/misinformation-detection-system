import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import numpy as np
import warnings
from tqdm.auto import tqdm
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
import pickle

warnings.filterwarnings('ignore')

# ── Minimum accuracy threshold ─────────────────────────────────
# If the retrained model scores below this, the existing model
# is preserved and a warning is logged instead of overwriting.
ACCURACY_FLOOR = 0.90

# ── Verdict keywords for Sebenarnya.my article classification ──
# Sebenarnya.my is a government fact-checking portal. Articles
# are NOT all fake — they include official announcements (Real),
# public warnings (Real), and debunked claims (Fake).
FAKE_KEYWORDS = ['tidak benar', 'palsu', 'penipuan', 'tipu', 'scam', 'tular semula']
REAL_KEYWORDS = ['makluman', 'waspada', 'penjelasan', 'peringatan', 'nasihat']


def classify_verdict(title):
    """
    Determines the label (Fake/Real) of a Sebenarnya.my article
    based on keywords in its title. Returns None for ambiguous titles
    that should be excluded from training.
    """
    title_lower = title.lower()
    for keyword in FAKE_KEYWORDS:
        if keyword in title_lower:
            return 'Fake'
    for keyword in REAL_KEYWORDS:
        if keyword in title_lower:
            return 'Real'
    return None  # Ambiguous — skip this article

def scrape_sebenarnya(max_pages_per_category=2):
    categories = [
        'nasional/bencana',
        'nasional/keselamatan',
        'sosial/jenayah',
        'sosial/kesihatan'
    ]
    
    base_url = 'https://sebenarnya.my/category/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    data = []
    
    for category in categories:
        print(f"Scraping category: {category}")
        for page in range(1, max_pages_per_category + 1):
            url = f"{base_url}{category}/page/{page}/" if page > 1 else f"{base_url}{category}/"
            print(f"  Fetching {url}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('h3', class_='entry-title')
                
                for a in articles:
                    link_tag = a.find('a')
                    if not link_tag:
                        continue
                    
                    article_url = link_tag.get('href')
                    title = link_tag.get('title') or link_tag.get_text(strip=True)
                    
                    try:
                        art_res = requests.get(article_url, headers=headers, timeout=10)
                        art_soup = BeautifulSoup(art_res.text, 'html.parser')
                        
                        content_div = art_soup.find('div', class_='td-post-content')
                        text = content_div.get_text(separator=' ', strip=True) if content_div else ''
                        
                        date_tag = art_soup.find('time', class_='entry-date')
                        date = date_tag.get('datetime') if date_tag else ''
                        
                        data.append({
                            'title': title,
                            'url': article_url,
                            'category': category.split('/')[1],
                            'date': date,
                            'text': text,
                            'label': classify_verdict(title)
                        })
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"    Failed to fetch article {article_url}: {e}")
                        
            except Exception as e:
                print(f"  Failed to fetch category page {url}: {e}")
    
    df = pd.DataFrame(data)
    # Drop articles with ambiguous verdicts (label=None)
    before_count = len(df)
    df = df.dropna(subset=['label'])
    skipped = before_count - len(df)
    if skipped > 0:
        print(f"  Skipped {skipped} ambiguous articles (no clear verdict in title)")
    
    csv_path = 'data/raw/data_sebenarnya_scraped.csv'
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Scraping complete. Saved {len(df)} records to {csv_path}")
    label_counts = df['label'].value_counts().to_dict()
    print(f"  Label distribution: {label_counts}")

def main():
    print("Scraping fresh articles from Sebenarnya.my...")
    scrape_sebenarnya(max_pages_per_category=2)

    print('Loading datasets...')
    progress = tqdm(total=3, desc='Loading Sources')

    df_malay = pd.read_pickle('data/raw/academic_malay_dataset.pkl')
    df_malay = df_malay[['news', 'label']].copy()
    df_malay.columns = ['text', 'label']
    df_malay['label'] = df_malay['label'].map({1: 'Real', 0: 'Fake'})
    df_malay['source'] = 'Academic Malay'
    progress.set_postfix_str(f'Academic Malay: {len(df_malay)} articles')
    progress.update(1)

    df_english = pd.read_csv('data/raw/data_english_global.csv')
    df_english = df_english[['text', 'label']].copy()
    df_english['label'] = df_english['label'].map({1: 'Real', 0: 'Fake'})
    df_english['source'] = 'Global English'
    progress.set_postfix_str(f'Global English: {len(df_english)} articles')
    progress.update(1)

    df_scraped = pd.read_csv('data/raw/data_sebenarnya_scraped.csv')
    df_scraped = df_scraped[['text', 'label']].copy()
    df_scraped['source'] = 'Sebenarnya.my'
    progress.set_postfix_str(f'Sebenarnya.my: {len(df_scraped)} articles')
    progress.update(1)
    progress.close()

    df_all = pd.concat([df_malay, df_english, df_scraped], ignore_index=True)
    df_all = df_all.dropna(subset=['text'])
    df_all = df_all[df_all['text'].str.len() > 50]
    print(f"\\nTOTAL COMBINED DATASET: {len(df_all)} articles")

    # Stopwords
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

    all_stopwords = malay_stopwords.union(english_stopwords)

    def clean_text(text):
        if not isinstance(text, str):
            return ''
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = text.lower()
        words = text.split()
        words = [w for w in words if w not in all_stopwords and len(w) > 2]
        return ' '.join(words)

    tqdm.pandas(desc='Cleaning Articles')
    df_all['clean_text'] = df_all['text'].progress_apply(clean_text)
    df_all['word_count'] = df_all['clean_text'].apply(lambda x: len(x.split()))

    df_clean = df_all[df_all['word_count'] > 5].copy()
    df_clean = df_clean.reset_index(drop=True)

    os.makedirs('data/clean', exist_ok=True)
    df_clean.to_csv('data/clean/data_clean.csv', index=False)
    print(f"\nAfter cleaning: {len(df_clean)} articles remain")

    X = df_clean['clean_text']
    y = df_clean['label']

    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.95,
        sublinear_tf=True
    )

    X_vec = vectorizer.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42, stratify=y
    )
    
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)
    y_test_enc = le.transform(y_test)

    models = {
        'XGBoost': XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss',
            use_label_encoder=False
        ),
        'Support Vector Machine': LinearSVC(random_state=42, max_iter=5000),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    }

    results = {}
    best_model = None
    best_acc = 0
    best_name = ''

    for name, model in tqdm(models.items(), total=len(models), desc='Training Models'):
        start = time.time()
        if name == 'XGBoost':
            model.fit(X_train, y_train_enc)
            y_pred = le.inverse_transform(model.predict(X_test))
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
        
        elapsed = time.time() - start
        acc = accuracy_score(y_test, y_pred)
        
        results[name] = {
            'accuracy': acc,
            'time': elapsed,
            'predictions': y_pred
        }
        print(f"  {name}: {acc*100:.2f}% ({elapsed:.1f}s)")
        
        if acc > best_acc:
            best_acc = acc
            best_model = model
            best_name = name

    print(f"\nCHAMPION MODEL: {best_name} ({best_acc*100:.2f}%)")

    # ── Accuracy Safety Guard ──────────────────────────────────
    # Reject the new model if it falls below the accuracy floor.
    if best_acc < ACCURACY_FLOOR:
        print(f"\n⚠ WARNING: Champion accuracy ({best_acc*100:.2f}%) is below the")
        print(f"  safety floor ({ACCURACY_FLOOR*100:.0f}%). Existing models will NOT be overwritten.")
        print(f"  This may indicate corrupted or imbalanced training data.")
        print(f"  Investigate the data sources before retrying.")
        return

    # Save models
    os.makedirs('models', exist_ok=True)
    with open('models/model.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    with open('models/label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)

    feature_names = vectorizer.get_feature_names_out()
    if best_name == 'XGBoost':
        importances = best_model.feature_importances_
        word_scores = pd.DataFrame({'Word': feature_names, 'Score': importances})
    elif hasattr(best_model, 'coef_'):
        coefs = best_model.coef_[0] if len(best_model.coef_.shape) > 1 else best_model.coef_
        word_scores = pd.DataFrame({'Word': feature_names, 'Score': np.abs(coefs)})
    else:
        word_scores = pd.DataFrame({'Word': feature_names, 'Score': np.asarray(X_vec.sum(axis=0)).ravel()})
    
    word_scores = word_scores.sort_values('Score', ascending=False)
    top100 = word_scores.head(100).copy()
    top100.to_csv('data/clean/Fake_News_Keyword_Importance.csv', index=False)

    print(f"\nTraining complete and models exported successfully!")
    print(f"  Accuracy: {best_acc*100:.2f}% (floor: {ACCURACY_FLOOR*100:.0f}%)")

if __name__ == '__main__':
    main()
