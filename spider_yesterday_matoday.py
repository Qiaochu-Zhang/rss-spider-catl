import feedparser
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
from dateutil import parser

# 读取RSS源列表
with open("feeds.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# 当前日期（UTC）
today = datetime.now(timezone.utc).date()
# 时间范围：昨天
yesterday = today - timedelta(days=1)

records = []

for url in urls:
    feed = feedparser.parse(url)
    source_title = feed.feed.get("title", url)

    for entry in feed.entries:
        pub_date = None

        # 1️⃣ 尝试解析 Available online
        text = entry.get("summary", "") or entry.get("description", "")
        m = re.search(r'Available online\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})', text)
        if m:
            try:
                pub_date = parser.parse(m.group(1))
            except Exception:
                pub_date = None

        # 2️⃣ 如果没有 Available online，回退到标准字段
        if not pub_date:
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif entry.get("updated_parsed"):
                pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

        # 3️⃣ 如果成功解析出时间，再过滤：判断是否是昨天
        if pub_date and pub_date.date() == yesterday:
            records.append({
                "title": entry.title,
                "link": entry.link,
                "published": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "source": source_title,
                "pub_date": pub_date  # 保留原始 datetime 方便排序
            })

# 将 records 转换为 DataFrame
df = pd.DataFrame(records)

if not df.empty:
    # 按照标题去重，保留每个标题日期最早的那篇
    df_sorted = df.sort_values(by="pub_date", ascending=True)  # 按时间升序排列
    df_dedup = df_sorted.drop_duplicates(subset="title", keep="first")  # 去重，保留最早的那篇

    # 创建文件名：带日期的文件名
    file_name = f"output/news_{yesterday.strftime('%Y-%m-%d')}.csv"

    # 保存结果到 CSV
    df_dedup.to_csv(file_name, index=False, encoding="utf-8-sig")

    print(f"✅ 抓取完成，共 {len(df_dedup)} 条，已保存到 {file_name}")
    print(f"时间范围：{yesterday} (UTC 日期)")
else:
    print(f"⚠️ 昨天 {yesterday} 没有抓到符合条件的文章。")
