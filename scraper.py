import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

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
                    
                    # Fetch individual article
                    try:
                        art_res = requests.get(article_url, headers=headers, timeout=10)
                        art_soup = BeautifulSoup(art_res.text, 'html.parser')
                        
                        # Find content
                        content_div = art_soup.find('div', class_='td-post-content')
                        text = content_div.get_text(separator=' ', strip=True) if content_div else ''
                        
                        # Find date
                        date_tag = art_soup.find('time', class_='entry-date')
                        date = date_tag.get('datetime') if date_tag else ''
                        
                        # Append
                        data.append({
                            'title': title,
                            'url': article_url,
                            'category': category.split('/')[1],
                            'date': date,
                            'text': text
                        })
                        time.sleep(1) # Polite delay
                    except Exception as e:
                        print(f"    Failed to fetch article {article_url}: {e}")
                        
            except Exception as e:
                print(f"  Failed to fetch category page {url}: {e}")
    
    df = pd.DataFrame(data)
    csv_path = 'data_raw.csv'
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Scraping complete. Saved {len(df)} records to {csv_path}")

if __name__ == "__main__":
    scrape_sebenarnya(max_pages_per_category=3)
