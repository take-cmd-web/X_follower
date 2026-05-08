import os, csv, datetime
import tweepy

USERNAME = "nshima_finance"  # @は不要。例: "elonmusk"

client = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])
user = client.get_user(username=USERNAME, user_fields=["public_metrics"])
m = user.data.public_metrics

today = datetime.date.today().isoformat()
os.makedirs("data", exist_ok=True)
path = "data/followers.csv"
new_file = not os.path.exists(path)

with open(path, "a", newline="") as f:
    w = csv.writer(f)
    if new_file:
        w.writerow(["date", "followers", "following", "tweets"])
    w.writerow([today, m["followers_count"], m["following_count"], m["tweet_count"]])

print(f"Recorded: {today} followers={m['followers_count']}")
