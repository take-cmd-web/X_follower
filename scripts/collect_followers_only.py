import os, csv, datetime
import tweepy

USERNAME = "nshima_finance"

client = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])
user = client.get_user(username=USERNAME, user_fields=["public_metrics"])
m = user.data.public_metrics

JST = datetime.timezone(datetime.timedelta(hours=9))
now_jst = datetime.datetime.now(JST)
today = now_jst.date().isoformat()
now_str = now_jst.strftime("%Y-%m-%d %H:%M")  # JST日時文字列
os.makedirs("data", exist_ok=True)

# ── フォロワー記録（今日の行は上書き・1日1データ） ────────
path = "data/followers.csv"
fieldnames = ["date", "followers", "following", "tweets", "updated_at"]

# 既存データを読み込む
existing = {}
if os.path.exists(path):
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            existing[row["date"]] = row

# 今日の行を上書き（2時間おきの最新値で更新）
existing[today] = {
    "date":       today,
    "followers":  m["followers_count"],
    "following":  m["following_count"],
    "tweets":     m["tweet_count"],
    "updated_at": now_str,
}

# 日付順に書き直し
with open(path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for row in sorted(existing.values(), key=lambda r: r["date"]):
        w.writerow(row)

print(f"Recorded: {today} followers={m['followers_count']} ({now_str})")
