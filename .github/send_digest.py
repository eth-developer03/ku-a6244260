"""Sends the digest the Mac prepared in mail/. Runs on GitHub Actions; standard library only."""
import json, os, smtplib, ssl, sys
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

meta = json.loads(Path("mail/meta.json").read_text())
sent = Path("mail/sent.json")
if sent.exists() and json.loads(sent.read_text()).get("generated_at") == meta["generated_at"]:
    print(f"Already sent the digest from {meta['generated_at']}; nothing new (did the Mac run last night?)")
    sys.exit(0)
age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(meta["generated_at"])).total_seconds() / 3600
if age_h > 72:
    print(f"Newest digest is {age_h:.0f}h old; not sending stale news."); sys.exit(0)

user, password = os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"].replace(" ", "")
to = [a.strip() for a in os.environ["EMAIL_TO"].split(",") if a.strip()]
msg = EmailMessage()
msg["Subject"], msg["From"], msg["To"] = meta["subject"], user, ", ".join(to)
msg["Date"], msg["Message-ID"] = formatdate(localtime=True), make_msgid(domain="knowledge-updater.local")
msg.set_content(Path("mail/body.txt").read_text())
msg.add_alternative(Path("mail/body.html").read_text(), subtype="html")
with smtplib.SMTP(os.environ.get("SMTP_HOST") or "smtp.gmail.com", 587, timeout=30) as s:
    s.starttls(context=ssl.create_default_context())
    s.login(user, password)
    s.send_message(msg)
sent.write_text(json.dumps({"generated_at": meta["generated_at"],
                            "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}))
print(f"Sent the digest from {meta['generated_at']} to {len(to)} recipient(s)")
