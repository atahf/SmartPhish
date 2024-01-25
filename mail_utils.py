import imaplib
import os
import re
import email
from email.header import decode_header
import sys
import json
from datetime import datetime
import base64
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def parse_msg(parts, file_name):
    company_name = None
    sender_email = None
    for part in parts:
        if "html" in part.get_content_type():
            decoded_content = str(part.get_payload(decode=True).decode('utf-8'))
            soup = BeautifulSoup(decoded_content, "html.parser")
            
            soup_text = soup.get_text()
            sIdx = soup_text.find("---------- Forwarded message ---------")
            if sIdx != -1:
                fwd = soup_text[sIdx:soup_text.find(">", sIdx)]
                company_raw = fwd[fwd.find("From:")+5:fwd.find("<")].strip()
                cList = [c for c in company_raw.split() if len(c) > 1]
                if len(cList) > 2:
                    company_name = " ".join(cList[:2])
                else:
                    company_name = " ".join(cList)

                sender_email = fwd[fwd.find("<")+1:].strip()

            sign = soup.find("div", class_="gmail_signature")
            if sign:
                sign.extract()
            if decoded_content.find("---------- Forwarded message ---------") != -1:
                fwd_msg = soup.find("div", class_="gmail_attr")
                if fwd_msg:
                    fwd_msg.extract()
            main_html1 = soup.find("blockquote")
            main_html2 = soup.find("div", class_="gmail_quote")
            if main_html1:
                soup = main_html1
            elif main_html2:
                soup = main_html2
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            break
    return company_name, sender_email

def get_emails(user, password, only_unread=False):
    res = []
    emailObj = imaplib.IMAP4_SSL("imap.gmail.com", 993)

    if emailObj.login(user, password):
        emailObj.select("Inbox")
    else:
        raise Exception("failed to login!")

    mail_category = "UNSEEN" if only_unread else "ALL"
    typ, data = emailObj.search(None, mail_category)
    if typ == 'OK':
        email_ids = data[0].split()
        if email_ids:
            print(f"{len(email_ids)} new emails received!")
            parent_folder = f"emails_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
            os.mkdir(parent_folder)
            for single_email in email_ids:
                try:
                    single_typ, single_data = emailObj.fetch(single_email, '(UID RFC822)')
                    raw = single_data[0][1]
                    try:
                        raw_str = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        pass
                                
                    msg = email.message_from_string(raw_str)

                    sender = msg['from']
                    sender = sender[sender.find('<')+1:sender.find('>')]
                    date = msg['date']
                    encoded_subject = msg['subject']
                    try:
                        decoded_subject = decode_header(encoded_subject)
                        subject = decoded_subject[0][0].decode(decoded_subject[0][1] or 'utf-8')
                    except Exception as e:
                        subject = encoded_subject
                    
                    subject = subject.replace("Fwd: ", "")
                    print(f"========\nFrom: {sender}\nDate: {date}\nSubject: {subject}\n========")

                    filename = re.sub(r'[^\w\s-]', '', subject).strip()
                    for ch in [' ', '\n', '\r', '\t', '\\']:
                        while ch in filename:
                            filename = filename.replace(ch, '_')
                    os.mkdir(f"./{parent_folder}/{filename}")

                    company, c_sender = parse_msg(msg.get_payload(), f"{parent_folder}/{filename}/index.html")
                    if c_sender != None:
                        sender = c_sender

                    with open(f"{parent_folder}/{filename}/info.json", 'w', encoding="utf-8") as f:
                        json.dump({
                            "sender": sender,
                            "date": date,
                            "subject": subject,
                            "company": company
                        }, f, ensure_ascii=False, indent=4)
                    res.append((f"{parent_folder}/{filename}/index.html", sender, company))
                except Exception as e:
                    print(f"While getting email error occured, unreading this mail!\n{e}")
                    emailObj.store(single_email, '-FLAGS', '\\Seen')
    emailObj.close()
    return res

def send_email(user, password, destination, subject, html_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    message = MIMEMultipart()
    message['From'] = user
    message['To'] = destination
    message['Subject'] = subject
    message.attach(MIMEText(html_content, 'html'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user, password)
    server.sendmail(user, destination, message.as_string())
    server.quit()
