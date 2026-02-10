const { onSchedule } = require("firebase-functions/v2/scheduler");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");
const axios = require("axios");

initializeApp();
const db = getFirestore();

const SUBREDDITS = ["n8n", "automation"];
const LIMIT = 100;
const TOP_N = 5;

exports.update_reddit_data = onSchedule("every 6 hours", async (event) => {
    console.log("Starting scheduled function");

    const allTopPosts = {};

    for (const subreddit of SUBREDDITS) {
        console.log(`Fetching r/${subreddit}...`);
        try {
            const url = `https://www.reddit.com/r/${subreddit}/new.json?limit=${LIMIT}`;
            const response = await axios.get(url, {
                headers: {
                    "User-Agent": "Mozilla/5.0 (Google Cloud Functions; Reddit Insights Bot) AppleWebKit/537.36 (KHTML, like Gecko)"
                }
            });

            if (response.status !== 200) {
                console.error(`Error fetching r/${subreddit}: ${response.status}`);
                continue;
            }

            const data = response.data;
            const posts = [];

            const children = data.data?.children || [];
            for (const child of children) {
                const postData = child.data;
                posts.push({
                    subreddit: subreddit,
                    title: postData.title,
                    url: postData.url,
                    score: postData.score || 0,
                    num_comments: postData.num_comments || 0,
                    created_utc: postData.created_utc,
                    engagement: (postData.score || 0) + (postData.num_comments || 0),
                    permalink: `https://reddit.com${postData.permalink}`
                });
            }

            // Sort by engagement
            posts.sort((a, b) => b.engagement - a.engagement);

            // Take top N
            allTopPosts[subreddit] = posts.slice(0, TOP_N);

        } catch (error) {
            console.error(`Exception fetching r/${subreddit}:`, error.message);
        }
    }

    // Upload to Firestore
    if (Object.keys(allTopPosts).length > 0) {
        console.log("Uploading data to Firestore...");
        await db.collection("dashboard_data").doc("latest").set(allTopPosts);
        console.log("Data upload complete.");
    } else {
        console.log("No data fetched.");
    }
});
