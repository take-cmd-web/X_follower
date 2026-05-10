"""
rebuild_followers.py
────────────────────
Xの「アカウント概要アナリティクス」CSVから過去フォロワー数を逆算し、
既存の followers.csv とマージして上書きする。

使い方:
  python rebuild_followers.py \
    --overview account_overview_analytics.csv \
    --followers data/followers.csv \
    --current 937

  --current : 実行時点の実際のフォロワー数（X プロフィールで確認）
"""

import csv, datetime, argparse, os

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--overview",  default="account_overview_analytics__1_.csv")
    p.add_argument("--followers", default="data/followers.csv")
    p.add_argument("--current",   type=int, default=937,
                   help="今日時点の実際のフォロワー数")
    return p.parse_args()

def main():
    args = parse_args()

    # ── overview CSV を読み込む ──────────────────────────
    rows = []
    with open(args.overview, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # 古い順に並べ直し（CSVは新しい順）
    rows_asc = list(reversed(rows))

    # ── フォロワー数を逆算 ───────────────────────────────
    # 全期間の純増 = Σ新フォロー - Σフォロー解除
    total_new = sum(int(r["新しいフォロー"].strip()) for r in rows)
    total_unf = sum(int(r["フォロー解除"].replace("\\", "").strip()) for r in rows)
    start_followers = args.current - (total_new - total_unf)

    print(f"期間純増: +{total_new} / 解除: -{total_unf} / 純増計: {total_new - total_unf}")
    print(f"期間開始時フォロワー推定: {start_followers}")

    # 古い順に日次フォロワー数を計算
    overview_data = {}   # date_str -> followers
    current = start_followers
    for row in rows_asc:
        date_str = datetime.datetime.strptime(
            row["Date"].strip(), "%a, %b %d, %Y"
        ).date().isoformat()

        new_f = int(row["新しいフォロー"].strip())
        unf   = int(row["フォロー解除"].replace("\\", "").strip())
        current += new_f - unf
        overview_data[date_str] = current

    print(f"逆算結果 最終値: {current}（指定値: {args.current}）")

    # ── 既存 followers.csv を読み込む ────────────────────
    existing = {}
    if os.path.exists(args.followers):
        with open(args.followers, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["date"]] = row

    # ── マージ：overview を base に、既存データで上書き ──
    merged = {}

    # overview のデータを追加（followers 列のみ）
    for date_str, followers in overview_data.items():
        merged[date_str] = {
            "date":      date_str,
            "followers": followers,
            "following": "",   # overview には含まれないため空欄
            "tweets":    "",
        }

    # 既存 followers.csv で上書き（following / tweets も保持）
    for date_str, row in existing.items():
        merged[date_str] = row

    # ── 日付順にソートして書き出し ───────────────────────
    os.makedirs(os.path.dirname(args.followers) if os.path.dirname(args.followers) else ".", exist_ok=True)
    sorted_rows = sorted(merged.values(), key=lambda r: r["date"])

    with open(args.followers, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "followers", "following", "tweets"])
        w.writeheader()
        w.writerows(sorted_rows)

    print(f"\nfollowers.csv を更新しました: {len(sorted_rows)} 件")
    print("  うち following/tweets あり:", sum(1 for r in sorted_rows if r["following"] != ""))

if __name__ == "__main__":
    main()
