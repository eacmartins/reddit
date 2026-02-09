# Directive: Reddit Research

**Goal:** Fetch recent posts from specified subreddits and identify high-engagement content.

**Inputs:**
- Subreddits: `r/n8n`, `r/automation`
- Limit: 100 most recent posts
- Top N: 5 posts per subreddit

**Tools:**
- `execution/fetch_reddit_posts.py`

**Outputs:**
- JSON file in `.tmp/reddit_top_posts.json` containing the top posts.
- Console output summarizing the top posts.

**Edge Cases:**
- API rate limits (handle gracefully or wait).
- Empty subreddits or fetch errors (logging).
