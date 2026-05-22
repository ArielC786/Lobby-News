import feedparser
from bs4 import BeautifulSoup
import re
import random
import os
import json
from urllib.parse import urljoin

FEED_URLS = [
    "https://hospitalitydesign.com/feed/",
    "https://www.sleepermagazine.com/feed/",
    "https://www.hospitality-interiors.net/feed",
    "https://boutiquehotelnews.com/feed/",
    "https://www.dezeen.com/feed/",
    "https://feeds.feedburner.com/Archdaily",
    "https://www.hospitalitynet.org/rss.xml"
]

HISTORY_FILE = "seen_articles.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_to_history(new_urls):
    history = load_history()
    history.update(new_urls)
    # Keep history size manageable (e.g., last 500 articles)
    history_list = list(history)[-500:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history_list, f)

def clean_html_summary(raw_html):
    soup = BeautifulSoup(raw_html, "lxml")
    text = soup.get_text(separator=" ").strip()
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Extract the first complete sentence to avoid awkward cutoffs
    sentences = text.split('. ')
    if len(sentences) > 0 and len(sentences[0]) > 10:
        cleaned = sentences[0].strip()
        if not cleaned.endswith('.'):
            cleaned += '.'
        return cleaned
    
    # Fallback if split fails
    if len(text) > 120:
        idx = text.rfind(' ', 0, 117)
        if idx == -1: idx = 117
        return text[:idx] + "..."
    return text

def extract_image(entry):
    url = None
    
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media:
                url = media['url']
                break
                
    if not url and 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[0].get('url')
        
    if not url and 'enclosures' in entry:
        for enclosure in entry.enclosures:
            if 'type' in enclosure and enclosure.type.startswith('image/'):
                url = enclosure.href
                break
    
    if not url:
        content_to_check = ""
        if 'content' in entry:
            content_to_check += entry.content[0].value
        if 'summary' in entry:
            content_to_check += entry.summary
            
        soup = BeautifulSoup(content_to_check, "lxml")
        img = soup.find('img')
        if img and img.get('src'):
            url = img['src']
            
    if url:
        if entry.get('link'):
            url = urljoin(entry.link, url)
        return url
        
    return None

def is_design_related(title, summary, tag):
    text = f"{title} {summary} {tag}".lower()
    
    # Exclude non-design things and strictly exclude non-hospitality projects
    exclude_keywords = [
        "sponsor", "promot", "deal", "acqui", "financ", "invest", "shareholder", 
        "appoint", "personnel", "sale", "revenue", "quarterly", "profit",
        "buyout", "merger", "exec", "ceo", "cfo", "marketing", "earnings",
        "consultancy", "school", "education", "residential", "house", "apartment", 
        "villa", "home ", "campus", "stadium", "office", "workplace", "clinic", "hospital"
    ]
    for ex_kw in exclude_keywords:
        if ex_kw in text:
            return False
            
    # Include explicitly design-related topics
    design_keywords = [
        "design", "designer", "architect", "architecture", "interior", "process",
        "innovat", "detail", "concept", "studio", "aesthetic", "material",
        "renovat", "layout", "decor", "art", "sculpt", "furniture", "light",
        "space", "blueprint", "render"
    ]
    for kw in design_keywords:
        if kw in text:
            return True
            
    return False

def fetch_latest_news(count=7):
    source_articles = {}
    seen_history = load_history()
    
    # Fetch all articles and group by source
    for url in FEED_URLS:
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.title if 'title' in feed.feed else "Hospitality News"
            if source_title not in source_articles:
                source_articles[source_title] = []
                
            for entry in feed.entries[:count*3]: # Grab more from each to account for filtering
                img_url = extract_image(entry)
                
                # List of problematic patterns that often fail in email clients or are tracking pixels
                problematic_patterns = [
                    "feedburner", "doubleclick", "adzerk", "quantserve", "pixel", 
                    "analytics", "statcounter", "facebook.com/tr", "google-analytics"
                ]
                
                is_valid_image = img_url and any(ext in img_url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"])
                is_problematic = img_url and any(pattern in img_url.lower() for pattern in problematic_patterns)

                if not is_valid_image or is_problematic:
                    continue
                
                clean_sum = clean_html_summary(entry.get('summary', ''))
                
                # Ensure the summary behaves like a real write-up (at least ~12 words)
                if len(clean_sum.split()) < 12:
                    continue
                
                tag = source_title.upper()
                if 'tags' in entry and len(entry.tags) > 0:
                    tag = tag + " / " + entry.tags[0].term.upper()
                if len(tag) > 35:
                    tag = tag[:32] + "..."
                
                article = {
                    "title": entry.title,
                    "summary": clean_sum,
                    "url": entry.link,
                    "image": img_url,
                    "source": source_title,
                    "tag": tag
                }
                
                if not is_design_related(entry.title, clean_sum, tag):
                    continue
                    
                # Prevent duplicates and seen articles
                if article['url'] not in seen_history and article['title'] not in [a['title'] for a in source_articles[source_title]]:
                    source_articles[source_title].append(article)
                
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            
    # Round-robin selection to mix sources
    final_list = []
    sources = list(source_articles.keys())
    
    used_images = set()
    
    while len(final_list) < count and len(sources) > 0:
        for src in list(sources):
            if len(source_articles[src]) > 0:
                article = source_articles[src].pop(0)
                
                # Enforce unique images among the real ones
                if article['image'] in used_images:
                    continue # Skip this article if its real image is already used
                
                used_images.add(article['image'])
                final_list.append(article)
                
                if len(final_list) >= count:
                    break
            else:
                sources.remove(src)
                
    random.shuffle(final_list) # Optional shuffle to scatter the sources
    
    # Ensure Hero article is in Asia
    asia_keywords = ["asia", "japan", "china", "tokyo", "singapore", "bangkok", "hong kong", "seoul", "bali", "thailand", "india", "vietnam", "malaysia", "indonesia", "taiwan", "philippines", "korea", "kyoto", "osaka", "beijing", "shanghai"]
    hero_idx = 0
    for i, item in enumerate(final_list):
        text = f"{item['title']} {item['summary']} {item['tag']}".lower()
        if any(kw in text for kw in asia_keywords):
            hero_idx = i
            break
            
    if hero_idx != 0:
        final_list[0], final_list[hero_idx] = final_list[hero_idx], final_list[0]
        
    return final_list
