import feedparser
from bs4 import BeautifulSoup
import re
import random
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

DEFAULT_IMAGES = [
    "https://images.unsplash.com/photo-1542314831-c6a4d14d8373?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1485686531765-a8052928e5c8?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=800&auto=format&fit=crop"
]

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
    
    # Exclude non-design things (finance, promo, general news focus)
    exclude_keywords = [
        "sponsor", "promot", "deal", "acqui", "financ", "invest", "shareholder", 
        "appoint", "personnel", "sale", "revenue", "quarterly", "profit",
        "buyout", "merger", "exec", "ceo", "cfo", "marketing", "earnings",
        "consultancy"
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
    
    # Fetch all articles and group by source
    for url in FEED_URLS:
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.title if 'title' in feed.feed else "Hospitality News"
            if source_title not in source_articles:
                source_articles[source_title] = []
                
            for entry in feed.entries[:count*3]: # Grab more from each to account for filtering
                img_url = extract_image(entry)
                if not img_url:
                    img_url = random.choice(DEFAULT_IMAGES)
                
                clean_sum = clean_html_summary(entry.get('summary', ''))
                
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
                    
                # Prevent duplicates
                if article['title'] not in [a['title'] for a in source_articles[source_title]]:
                    source_articles[source_title].append(article)
                
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            
    # Round-robin selection to mix sources
    final_list = []
    sources = list(source_articles.keys())
    
    while len(final_list) < count and len(sources) > 0:
        for src in list(sources):
            if len(source_articles[src]) > 0:
                final_list.append(source_articles[src].pop(0))
                if len(final_list) >= count:
                    break
            else:
                sources.remove(src)
                
    random.shuffle(final_list) # Optional shuffle to scatter the sources
    return final_list
