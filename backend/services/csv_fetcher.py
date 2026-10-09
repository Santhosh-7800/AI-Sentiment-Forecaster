import pandas as pd
import glob
import os
import re
import logging

logger = logging.getLogger(__name__)

def _fetch_local_csv_data(query: str):
    """Fetch real review data from local CSVs, matching product names and returning full review text."""
    articles = []
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output')
    csv_files = glob.glob(os.path.join(base_dir, '*.csv'))
    
    logger.info(f" CSV Fetch: Searching for '{query}' in {len(csv_files)} CSV files")
    
    q_words = set(w.lower().strip() for w in query.split() if len(w) > 2)  # Skip short words
    logger.info(f" Keywords: {q_words}")
    
    for f in csv_files:
        try:
            logger.info(f" Reading: {os.path.basename(f)}")
            df = pd.read_csv(f, engine='python', on_bad_lines='skip', dtype=str)
            
            # Identify columns: product name, review/text content, date, sentiment
            product_col = next((c for c in df.columns if 'product' in c.lower() or 'name' in c.lower()), None)
            text_cols = [c for c in df.columns if any(x in c.lower() for x in ['review', 'text', 'original', 'clean'])]
            date_col = next((c for c in df.columns if 'date' in c.lower()), None)
            sentiment_col = next((c for c in df.columns if 'sentiment' in c.lower()), None)
            
            if not text_cols:
                logger.debug(f"  Skipping {os.path.basename(f)}: No text columns found")
                continue
            
            logger.info(f"[OK] Columns found - Product: {product_col}, Text: {text_cols}, Date: {date_col}, Sentiment: {sentiment_col}")
            
            # Combine all text columns to get full review
            df['_full_text'] = ''
            for tc in text_cols:
                if tc in df.columns:
                    df['_full_text'] = df['_full_text'] + ' ' + df[tc].fillna('')
            
            # Filter by query: match product name AND/OR text content
            mask = df.apply(
                lambda row: any(
                    w in str(row.get(product_col, '')).lower() or 
                    w in str(row['_full_text']).lower() 
                    for w in q_words
                ),
                axis=1
            )
            
            filtered = df[mask].head(100)
            logger.info(f"[OK] Found {len(filtered)} matching rows in {os.path.basename(f)}")
            
            for _, row in filtered.iterrows():
                full_text = str(row.get('_full_text', '')).strip()
                if not full_text or len(full_text) < 10:
                    continue
                    
                d_val = str(row[date_col]) if date_col and pd.notna(row[date_col]) else ''
                sent_val = str(row[sentiment_col]).lower() if sentiment_col and pd.notna(row[sentiment_col]) else 'neutral'
                
                articles.append({
                    'platform': 'local_csv',
                    'keyword': query,
                    'title': full_text[:80],
                    'description': full_text,
                    'link': '',
                    'published_date': d_val,
                    'csv_sentiment': sent_val  # Pass pre-labeled sentiment from CSV
                })
        except Exception as e:
            logger.error(f"[FAIL] Error reading {os.path.basename(f)}: {str(e)}")
            continue
    
    logger.info(f"[OK] CSV Fetch Complete: {len(articles)} articles extracted")
    return articles
