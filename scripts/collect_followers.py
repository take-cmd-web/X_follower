import os, csv, datetime
import tweepy

USERNAME = "nshima_finance"

client = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])
user = client.get_user(username=USERNAME, user_fields=["public_metrics"])
m = user.data.public_metrics

today = datetime.date.today().isoformat()
os.makedirs("data", exist_ok=True)

# --- 既存: フォロワー記録 ---
path = "data/followers.csv"
new_file = not os.path.exists(path)
with open(path, "a", newline="") as f:
    w = csv.writer(f)
    if new_file:
        w.writerow(["date", "followers", "following", "tweets"])
    w.writerow([today, m["followers_count"], m["following_count"], m["tweet_count"]])
print(f"Recorded: {today} followers={m['followers_count']}")

# --- 追加: ツイート毎メトリクス ---
tweets = client.get_users_tweets(
    id=user.data.id,
    max_results=10,                          # 直近10件
    tweet_fields=["public_metrics", "created_at"],
    exclude=["retweets", "replies"],
)

tweet_path = "data/tweets.csv"
tweet_new = not os.path.exists(tweet_path)
with open(tweet_path, "a", newline="") as f:
    w = csv.writer(f)
    if tweet_new:
        w.writerow(["snapshot_date", "tweet_id", "created_at",
                    "impressions", "likes", "retweets", "replies"])
    for t in tweets.data or []:
        pm = t.public_metrics
        print(f"  tweet {t.id}: {pm}")      # ← どのフィールドが返るか確認用
        w.writerow([
            today, t.id, t.created_at.isoformat(),
            pm.get("impression_count", "N/A"),
            pm.get("like_count"),
            pm.get("retweet_count"),
            pm.get("reply_count"),
        ])
