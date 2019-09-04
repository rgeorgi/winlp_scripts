from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import List
import time


def gmail_send(config: dict,
               from_addr,
               to_addrs,
               msg: MIMEMultipart):
    """
    Actually perform the sending of the email.
    """
    for i in range(3):
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(config['gmail_user'], config['gmail_pass'])
            server.sendmail(from_addr, to_addrs, msg.as_string())
            server.close()
            return server
        except TimeoutError as te:
            print("Attempt #{}/{} timed out. ".format(i+1, 3))
        else:
            break
    time.sleep(3)


def draft_msg(text, subject, to_addrs, from_addr):
    """
    Compose a MIME-Multipart message with the given address

    :param text:
    :param to_addrs:
    :return:
    """
    msg = MIMEMultipart()
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg['To'] = ','.join(to_addrs)
    # msg['From'] = from_addr
    msg.attach(MIMEText(text))
    return msg