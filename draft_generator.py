import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from news_fetcher import fetch_latest_news

def generate_draft():
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('magazine.html')
    
    print("Fetching live hospitality news...")
    real_news = fetch_latest_news(7)
    
    if not real_news or len(real_news) < 7:
        print("Could not fetch 7 live articles. Defaulting to placeholders.")
        # Fallback to simple list if fetching fails
        real_news = [{"title":"Placeholder", "summary":"Summary text", "url":"#", "image":"https://images.unsplash.com/photo-1542314831-c6a4d14d8373", "source":"Lobby News", "tag":"NEWS"} for _ in range(7)]

    hero_article = real_news[0]
    grid_articles = real_news[1:4]
    bottom_articles = real_news[4:7]

    mock_data = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "year": datetime.now().year,
        "hero_article": hero_article,
        "grid_articles": grid_articles,
        "bottom_articles": bottom_articles
    }

    html_output = template.render(**mock_data)

    output_filename = "draft_preview.html"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"Draft successfully generated with LIVE NEWS: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    generate_draft()
