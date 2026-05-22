import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from news_fetcher import fetch_latest_news, save_to_history

def generate_draft():
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('magazine.html')
    
    print("Fetching live hospitality news...")
    real_news = fetch_latest_news(7)
    
    if not real_news or len(real_news) < 7:
        print("Could not fetch 7 live articles. Defaulting to placeholders.")
        # Fallback to simple list if fetching fails
        real_news = [{"title":"Placeholder", "summary":"Summary text", "url":"#", "image":"https://images.unsplash.com/photo-1542314831-c6a4d14d8373", "source":"Lobby News", "tag":"NEWS"} for _ in range(7)]

    # Record these articles as "seen" so they don't repeat in the next run
    used_urls = [article['url'] for article in real_news if article['url'] != "#"]
    if used_urls:
        save_to_history(used_urls)

    mock_data = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "year": datetime.now().year,
        "articles": real_news
    }

    html_output = template.render(**mock_data)

    output_filename = "draft_preview.html"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"Draft successfully generated with LIVE NEWS: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    generate_draft()
