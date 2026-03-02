from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

    # 使用 UTF-8 编码发送中文邮件
    msg.attach(MIMEText(content, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(mail_from, [mail_to], msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    articles, start, end = fetch_articles()
    body = build_email_body(articles, start, end)
    subject = f"上周文献推送 ({start.date()} - {(end - timedelta(seconds=1)).date()})"
    send_email(subject, body)

if __name__ == "__main__":
    main()
