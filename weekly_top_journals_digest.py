from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import re
import smtplib
import feedparser
from dataclasses import dataclass
from datetime import datetime, timedelta
from dateutil import parser as dtparser
import pytz

# 时区设置：中国时间
TZ = pytz.timezone("Asia/Shanghai")

# 关键词（可自行调整）
KEYWORDS = [
    "cell", "molecular", "genome", "rna", "protein",
    "immun", "infection", "virus", "cancer", "tumor",
    "chemistry", "chemical", "synthesis", "drug",
    "clinical", "therapy", "disease", "vaccine"
]

# 四大主刊 RSS
FEEDS = [
    {
        "name": "Science",
        "url": "https://www.science.org/action/showFeed?feed=rss&jc=science&type=etoc",
    },
    {
        "name": "Nature",
        "url": "https://www.nature.com/nature.rss",
    },
    {
        "name": "Cell",
        "url": "https://www.cell.com/cell/current.rss",
    },
    {
        "name": "The Lancet",
        "url": "https://www.thelancet.com/rssfeed/lancet_online.xml",
    },
]

@dataclass
class Article:
    journal: str
    title: str
    link: str
    published: datetime
    summary: str


# 获取上周时间窗口
def get_last_week_window():
    now = datetime.now(TZ)
    this_monday = now - timedelta(days=now.weekday())
    this_monday = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    last_monday = this_monday - timedelta(days=7)
    return last_monday, this_monday


# 清理文本
def clean_text(text):
    return re.sub(r"\s+", " ", (text or "").strip())


# 匹配关键词
def match_keywords(text):
    text = text.lower()
    return any(k.lower() in text for k in KEYWORDS)


# 解析文章的日期
def parse_date(entry):
    try:
        if hasattr(entry, "published"):
            dt = dtparser.parse(entry.published)
        elif hasattr(entry, "updated"):
            dt = dtparser.parse(entry.updated)
        elif hasattr(entry, "published_parsed"):
            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        else:
            return None

        if dt.tzinfo is None:
            dt = TZ.localize(dt)

        return dt.astimezone(TZ)
    except Exception:
        return None


# 抓取文章
def fetch_articles():
    start, end = get_last_week_window()
    articles = []

    for feed in FEEDS:
        try:
            data = feedparser.parse(feed["url"])
            for entry in data.entries:
                published = parse_date(entry)
                if not published:
                    continue

                if not (start <= published < end):
                    continue

                title = clean_text(entry.title)
                summary = clean_text(getattr(entry, "summary", ""))
                link = clean_text(entry.link)

                if match_keywords(title + " " + summary):
                    articles.append(
                        Article(
                            journal=feed["name"],
                            title=title,
                            link=link,
                            published=published,
                            summary=summary[:300]
                        )
                    )
        except Exception as e:
            print(f"Error fetching {feed['name']}: {e}")

    return articles, start, end


# 生成邮件内容
def build_email_body(articles, start, end):
    body = []
    body.append("每周文献推送（上周）")
    body.append("")
    body.append(f"时间范围: {start.date()} - {(end - timedelta(seconds=1)).date()}")
    body.append(f"总共 {len(articles)} 篇文章")
    body.append("")

    for article in sorted(articles, key=lambda x: x.published, reverse=True):
        body.append(f"{article.journal} | {article.published.date()}")
        body.append(f"标题: {article.title}")
        body.append(f"链接: {article.link}")
        body.append(f"摘要: {article.summary}")
        body.append("-" * 60)

    return "\n".join(body)


# 发送邮件
def send_email(subject, content):
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    mail_from = os.environ["MAIL_FROM"]
    mail_to = os.environ["MAIL_TO"]

    msg = MIMEMultipart()
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Subject"] = subject

    msg.attach(MIMEText(content, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(mail_from, [mail_to], msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


# 主程序
def main():
    articles, start, end = fetch_articles()
    body = build_email_body(articles, start, end)
    subject = f"上周文献推送 ({start.date()} - {(end - timedelta(seconds=1)).date()})"
    send_email(subject, body)


if __name__ == "__main__":
    main()
