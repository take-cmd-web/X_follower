import os, csv, datetime, re
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

# 今日の行を上書き（朝10時→夕方18時で最新値に更新）
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
print(f"Recorded: {today} followers={m['followers_count']}")

# ── ツイート取得（拡張版） ────────────────────────────────
tweets = client.get_users_tweets(
    id=user.data.id,
    max_results=100,
    tweet_fields=["public_metrics", "created_at", "text", "entities", "attachments"],
    expansions=["attachments.media_keys"],
    exclude=["retweets", "replies"],
)

# メディアキー → タイプ の辞書を作る
media_map = {}
if tweets.includes and "media" in tweets.includes:
    for media in tweets.includes["media"]:
        media_map[media.media_key] = media.type  # photo / video / animated_gif

tweet_path = "data/tweets.csv"

# 既存データを読み込んでtweet_idをキーに最新値で上書き（A方式）
existing = {}
if os.path.exists(tweet_path):
    with open(tweet_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row["tweet_id"]] = row

# 新しいデータで上書き
for t in tweets.data or []:
    pm = t.public_metrics

    # ハッシュタグ抽出
    hashtags = ""
    if t.entities and "hashtags" in t.entities:
        hashtags = " ".join(f"#{h['tag']}" for h in t.entities["hashtags"])

    # URL有無
    has_url = "1" if (t.entities and "urls" in t.entities) else "0"

    # メディア有無・タイプ
    media_type = ""
    if t.attachments and "media_keys" in t.attachments:
        types = [media_map.get(k, "") for k in t.attachments["media_keys"]]
        media_type = types[0] if types else ""

    # テキスト（t.co URLを除去してクリーンに）
    text = re.sub(r"https://t\.co/\S+", "", t.text).strip()

    # エンゲージメント率（impressions > 0 のときのみ計算）
    imp = pm.get("impression_count", 0)
    eng_rate = round(pm.get("like_count", 0) / imp * 100, 2) if imp > 0 else 0

    existing[str(t.id)] = {
        "snapshot_date": today,
        "tweet_id":      str(t.id),
        "created_at":    t.created_at.isoformat(),
        "text":          text,
        "hashtags":      hashtags,
        "has_url":       has_url,
        "media_type":    media_type,
        "impressions":   imp,
        "likes":         pm.get("like_count", 0),
        "retweets":      pm.get("retweet_count", 0),
        "replies":       pm.get("reply_count", 0),
        "eng_rate":      eng_rate,
    }

# 全件を created_at 降順で書き直し
rows = sorted(existing.values(), key=lambda r: r["created_at"], reverse=True)
fieldnames = [
    "snapshot_date", "tweet_id", "created_at", "text",
    "hashtags", "has_url", "media_type",
    "impressions", "likes", "retweets", "replies", "eng_rate",
]
with open(tweet_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"tweets.csv updated: {len(rows)} records")
