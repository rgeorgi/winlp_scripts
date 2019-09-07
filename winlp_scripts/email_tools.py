from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import List
import time
from html2text import html2text

def gmail_send(gmail_user,
               gmail_pass,
               to_addrs,
               msg: MIMEMultipart):
    """
    Actually perform the sending of the email.
    """
    msg['To'] = ','.join(to_addrs)
    for i in range(3):
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, to_addrs, msg.as_string())
            server.close()
            return server
        except TimeoutError as te:
            print("Attempt #{}/{} timed out. ".format(i+1, 3))
    time.sleep(3)


def craft_text_email(text, subject) -> MIMEMultipart:
    part = MIMEText(text, "plain")
    return draft_msg(subject, [part])

def create_html_email(html, subject, ) -> MIMEMultipart:
    html_part = MIMEText(html, 'html')
    text_part = MIMEText(html2text(html), 'plain')
    return draft_msg(subject, [html_part, text_part])

def draft_msg(subject: str,
              parts = List[MIMEText]) -> MIMEMultipart:
    """
    Compose a MIME-Multipart message with the given address

    :param text:
    :param to_addrs:
    :return:
    """
    msg = MIMEMultipart('alternative')
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    for part in parts:
        msg.attach(part)
    return msg