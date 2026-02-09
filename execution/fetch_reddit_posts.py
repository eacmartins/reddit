#!/usr/bin/env python3
"""
Fetch recent posts from Reddit subreddits and extract top engagement posts.
"""

import requests
import json
import os
import time
from datetime import datetime

import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/execution.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fetch_reddit_posts")

SUBREDDITS = ["n8n", "automation"]
LIMIT = 100
TOP_N = 5
OUTPUT_FILE = ".tmp/reddit_top_posts.json"
DASHBOARD_FILE = "dashboard/data.json"
CREDENTIALS_FILE = "credentials.json"

def initialize_firebase():
    try:
        # Check for environment variable first (CI/CD)
        firebase_creds_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if firebase_creds_json:
            logger.info("Using Firebase credentials from environment variable")
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()

        # Fallback to local file
        if not os.path.exists(CREDENTIALS_FILE):
             logger.warning(f"Credentials file {CREDENTIALS_FILE} not found and env var missing. Skipping Firestore upload.")
             return None
        
        logger.info(f"Using Firebase credentials from file: {CREDENTIALS_FILE}")
        cred = credentials.Certificate(CREDENTIALS_FILE)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return None

def upload_to_firestore(db, data):
    if not db:
        return
    
    try:
        logger.info("Uploading data to Firestore...")
        # We will store the latest results in a single document for easy retrieval
        # or separate documents. For dashboard simplicity, let's use a "dashboard_data" collection
        # and a single document "latest" that matches the JSON structure.
        
        doc_ref = db.collection("dashboard_data").document("latest")
        doc_ref.set(data)
        logger.info("Successfully uploaded data to Firestore (dashboard_data/latest)")
    except Exception as e:
        logger.error(f"Failed to upload to Firestore: {e}")

def fetch_subreddit_posts(subreddit, limit=100):
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Error fetching r/{subreddit}: {response.status_code}")
            return []
            
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
            
        return posts
    except Exception as e:
        logger.error(f"Exception fetching r/{subreddit}: {e}")
        return []

def main():
    logger.info("Starting Reddit post fetch")
    
    # Initialize Firebase
    db = initialize_firebase()
    
    all_top_posts = {}
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(DASHBOARD_FILE), exist_ok=True)
    
    for subreddit in SUBREDDITS:
        logger.info(f"Fetching posts from r/{subreddit}...")
        posts = fetch_subreddit_posts(subreddit, LIMIT)
        
        # Sort by engagement (score + comments)
        posts.sort(key=lambda x: x["engagement"], reverse=True)
        
        # Take top N
        top_posts = posts[:TOP_N]
        all_top_posts[subreddit] = top_posts
        
        logger.info(f"Found {len(posts)} posts. Top {TOP_N}:")
        for i, post in enumerate(top_posts, 1):
            logger.info(f"{i}. [{post['engagement']}] {post['title']} ({post['permalink']})")
        
        # Sleep briefly to be nice to the API
        time.sleep(1)

    # Save to temp file (legacy)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_top_posts, f, indent=2)
    logger.info(f"Saved results to {OUTPUT_FILE}")

    # Save to dashboard data file
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(all_top_posts, f, indent=2)
    logger.info(f"Saved dashboard data to {DASHBOARD_FILE}")
    
    # Upload to Firestore
    upload_to_firestore(db, all_top_posts)
    
    logger.info("Reddit post fetch completed")

if __name__ == "__main__":
    main()
