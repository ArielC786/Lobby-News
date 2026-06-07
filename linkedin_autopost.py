import os
import json
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def post_to_linkedin():
    access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
    repo_owner = os.environ.get('GITHUB_REPOSITORY', 'yourusername/lobbynews')
    
    if not access_token:
        print("Missing LINKEDIN_ACCESS_TOKEN.")
        return
        
    # Determine the public URL where GitHub Pages hosts this
    try:
        owner, repo = repo_owner.split('/')
        public_url = f"https://{owner}.github.io/{repo}/"
    except Exception:
        public_url = "https://github.com" # Fallback if run locally

    # Parse the magazine to extract the main headline for the post
    try:
        with open('draft_preview.html', 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
            headline_el = soup.find(class_='hero-title')
            headline = headline_el.text.strip() if headline_el else "New Innovations in Architecture"
    except Exception:
        headline = "New Innovations in Architecture"

    # Draft the LinkedIn post payload
    post_content = (
        "Welcome to this week's edition of Lobby News! 🗞️✨\n\n"
        f"Top Story: {headline}\n\n"
        "We curate the best hospitality projects, hotel openings, and architecture innovations.\n"
        "Swipe through the PDF carousel below for this week's highlights, or read the full interactive magazine here:\n"
        f"{public_url}\n\n"
        "#HospitalityDesign #Architecture #InteriorDesign #LobbyNews #HotelDesign #HospitalityTech #ArchDaily"
    )

    print("Fetching LinkedIn User Authority...")
    try:
        # Step 1: Authenticate and get our exact LinkedIn Member ID (URN)
        req_me = urllib.request.Request(
            'https://api.linkedin.com/v2/me',
            headers={'Authorization': f'Bearer {access_token}', 'X-Restli-Protocol-Version': '2.0.0'}
        )
        with urllib.request.urlopen(req_me) as response:
            me_data = json.loads(response.read().decode('utf-8'))
            person_urn = f"urn:li:person:{me_data['id']}"
            
        print(f"Authorized as URN: {person_urn}. Executing post...")
        
        # Step 2: Push the text + Link metadata to the LinkedIn wall
        post_url = 'https://api.linkedin.com/v2/ugcPosts'
        post_data = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_content
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": public_url
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        req_post = urllib.request.Request(
            post_url,
            data=json.dumps(post_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json'
            }
        )
        with urllib.request.urlopen(req_post) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("Successfully blasted to LinkedIn! Post ID:", result.get('id'))
            
    except Exception as e:
        print(f"Failed to post to LinkedIn. API Error: {e}")

if __name__ == "__main__":
    post_to_linkedin()
