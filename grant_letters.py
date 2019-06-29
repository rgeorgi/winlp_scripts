#!/usr/bin/env python3

"""
This script is used to generate the funding letters from a template, and email out

"""

import argparse
import os
import re

# Email imports
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formatdate


from io import BytesIO
from typing import Dict, Tuple, List
import smtplib
from email.mime.multipart import MIMEMultipart
import time
import num2words

# Work with docx and xlsx (Word Doc and Excel) documents
import yaml
from docx import Document
from docx.text.paragraph import Paragraph
import xlrd

import time



def gmail_send(to_addr, msg: MIMEMultipart):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_pass)
    server.sendmail('WiNLP Chairs', [to_addr, cc_user], msg.as_string())
    server.close()
    return server

def modify_docx(docx_path: str,
                recipient_name: str,
                award_amt: float,
                paper_title: str,
                sent: bool):
    """
    Generate the new docx file from the provided template.
    """
    amt_str = '{:.02f}'.format(award_amt)
    date = time.strftime('%d %b %Y')
    document = Document(docx_path)  # type: Document
    for para in document.paragraphs:  # type: Paragraph

        if '{paper_title}' in para.text and paper_title is None:
            para.text = 'We are excited for you to join us at the 2019 Widening NLP Workshop on the 28th of July.'
        else:
            para.text = para.text.format(name=recipient_name,
                                         paper_title=paper_title,
                                         date=date,
                                         amount=amt_str,
                                         text_amount=num2words.num2words(amt_str))
    return document

def generate_email(config: dict,
                   spreadsheet_path: str,
                   docx_path: str):
    """
    Generate the email to send to the attendees.
    """
    workbook = xlrd.open_workbook(spreadsheet_path)
    worksheet = workbook.sheet_by_index(1)

    # Get non-header rows
    for i, row in enumerate(worksheet.get_rows()):

        # Skip the first row (headers)
        if i == 0:
            continue

        # For the expected spreadsheet format,
        # refer to the readme.
        recipient_name = row[1].value
        award_amt = row[2].value
        recipient_email = row[15].value
        paper_title = row[18].value
        sent = row[19].value

        # Skip already sent messages, or those
        # where the award amount is zero.
        if sent or award_amt == 0:
            continue

        # Create the new document
        document = modify_docx(docx_path, recipient_name, award_amt, paper_title, sent)

        # Generate the directory to store the letters, and save
        # the modified document.
        filename = 'WiNLP Travel Grant Invitation Letter - {}.docx'.format(recipient_name)
        dir = os.path.join(os.getcwd(), 'letters')
        fullpath = os.path.join(dir, filename)
        os.makedirs(dir, exist_ok=True)
        document.save(fullpath)

        # Now, generate the email

        msg = draft_msg('''Dear {name},
        
    Please find attached an invitation letter for WiNLP 2019, that you may use for your records and the visa application process.
    
    If you believe there are any errors, or need additional documentation for your visa application, please let us know as sono as possible.
    
-- WiNLP Chairs'''.format(name=recipient_name), recipient_email)
        doc_attach = BytesIO()
        document.save(doc_attach)
        # Add the docx
        doc_attach.seek(0)
        msg.attach(MIMEApplication(doc_attach.read(), Name=filename))
        return msg



        # gmail_send(email, msg)


def draft_msg(text, to_addr):
    """
    Compose a MIME-Multipart message with the given address

    :param text:
    :param to_addr:
    :return:
    """
    msg = MIMEMultipart()
    msg['From'] = cc_user
    msg['To'] = to_addr
    msg['CC'] = cc_user
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = 'WiNLP Travel Grant - Invitation Letter'
    msg.attach(MIMEText(text))
    return msg

def load_yml(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.load(f)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-s', '--spreadsheet', help='Spreadsheet with submissions, authors, etc')
    p.add_argument('-t', '--template', help='Template for email')
    p.add_argument('-c', '--config', help='Path to the email config file.', default='config.yml', type=load_yml)
    p.add_argument('-w', '--worksheet', help='Worksheet number for the grant info', default=1)

    args = p.parse_args()

    # Generate the email
    msg = generate_email(args.config,
                         args.spreadsheet,
                         args.template)
