from firebase_functions import scheduler_fn
from firebase_admin import initialize_app, firestore
import requests
import logging
from datetime import datetime

# Initialize Firebase Admin
initialize_app()
db = firestore.client()

SUBREDDITS = ["n8n", "automation"]
LIMIT = 100
TOP_N = 5

@scheduler_fn.on_schedule(schedule="every 6 hours")
def update_reddit_data(event: scheduler_fn.ScheduledEvent) -> None:
    print(f"Starting scheduled function: {event.schedule_time}")
    
    all_top_posts = {}
    
    for subreddit in SUBREDDITS:
        print(f"Fetching r/{subreddit}...")
        try:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={LIMIT}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Google Cloud Functions; Reddit Insights Bot) AppleWebKit/537.36 (KHTML, like Gecko)"
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Error fetching r/{subreddit}: {response.status_code}")
                continue
                
            data = response.json()
            posts = []
            
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                posts.append({
                    "subreddit": subreddit,
                    "title": post_data.get("title"),
                    "url": post_data.get("url"),
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc"),
                    "engagement": post_data.get("score", 0) + post_data.get("num_comments", 0),
                    "permalink": f"https://reddit.com{post_data.get('permalink')}"
                })
            
            # Sort and slice
            posts.sort(key=lambda x: x["engagement"], reverse=True)
            top_posts = posts[:TOP_N]
            all_top_posts[subreddit] = top_posts
            
        except Exception as e:
            print(f"Exception fetching r/{subreddit}: {e}")

    # Upload to Firestore
    if all_top_posts:
        print("Uploading data to Firestore...")
        doc_ref = db.collection("dashboard_data").document("latest")
        doc_ref.set(all_top_posts)
        print("Data upload complete.")
    else:
        print("No data fetched.")
