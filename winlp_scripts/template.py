from docx.api import Document as CreateDocument
from docx.document import Document
from xml.etree.ElementTree import Element
import re

def get_key(s):
    key_m = re.match('^{(.*)}$', s)
    return key_m.group(1) if key_m else None

def process_docx_template(docx_path: str, keys: dict) -> Document:
    """
    Given a docx with {key}s, return a document with those
    keys filled with the variables from `keys`
    """
    d = CreateDocument(docx=docx_path) # type: Document

    # Iterate over all the paragraphs in the document.
    for para in d.paragraphs: # type: Paragraph
        key_text = ''
        in_key_run = False

        # print(para.paragraph_format.space_after)
        for run in para._p.r_lst: # type: Element

            # Get the run text
            key_m = re.match('^([^{}]*?)({\S*}?|{?\S*})([^{}]*)$', run.text)
            before_key, key, after_key = key_m.groups() if key_m else (None,)*3

            key_val = ''
            if key or in_key_run:
                if key == '}':
                    in_key_run = False
                    key_val = get_key(key_text+'}')
                    key_text = ''
                elif key == '{':
                    key_text += run.text
                    in_key_run = True
                elif key:
                    key_val = get_key(key)
                else:
                    key_text += run.text

                run.text = ''.join([s for s in [before_key, keys.get(key_val), after_key] if s])

    return d
