from collections import Counter
from xml.etree.ElementTree import Element
import re
from docx import Document as LoadDoc
from docx.document import Document
from docx.section import Section
from docx.text.paragraph import Paragraph
from docx.text.run import Run

KEY_PATTERN = '{([^}]+)}'

def get_key(s):
    key_m = re.match('^{(.*)}$', s)
    return key_m.group(1) if key_m else None

def replace_keys(text: str, keys: dict, key_pattern=KEY_PATTERN) -> str:
    """
    Given a dictionary of keys and a key replacement pattern,
    return text where all the instances of a key pattern have been replaced
    with their associated values.
    """
    new_text = ''
    cur_stop = 0

    key_matches = re.finditer(key_pattern, text)
    for key_match in key_matches:
        start, stop = key_match.span()
        new_text += text[cur_stop:start]
        new_text += keys[key_match.group(1).strip()]
        cur_stop = stop

    new_text += text[cur_stop:]
    return new_text



def docx_template(docx_path: str, keys: dict) -> Document:
    """
    Given a docx with {key}s, return a document with those
    keys filled with the variables from `keys`
    """
    d = LoadDoc(docx_path) # type: Document

    # Iterate over all the paragraphs in the document.
    for para in d.sou: # type: Section
        para._document_part

        new_runs = []

        cur_run = None
        cur_run_text = ''


        # print(para.paragraph_format.space_after)
        for run in para._p.r_lst: # type: Element

            # Look to see whether a key occurs in the run text.
            key_in_run_m = '{' in run.text or '}' in run.text

            # If there was no key seen in this run, and we're not waiting
            # to fill another key slot... just append it to the list of current runs.
            if not key_in_run_m and cur_run is None:
                new_runs.append(run)

            # If there was a key located in the text...
            else:
                # See if we have the same number of close brackets as open
                cur_run = cur_run if cur_run is not None else run
                cur_run_text += run.text

                if cur_run is not run:
                    run.text = ''

                char_counts = Counter(cur_run_text)



                if char_counts.get('{', 0) - char_counts.get('}', 0) == 0:
                    cur_run.text = replace_keys(cur_run_text, keys)
                    new_runs.append(cur_run)
                    cur_run = None
                    cur_run_text = ''



        # para.clear()
        # for run in new_runs: # type: Run
        #     para.add_run(run.text, run.style)



    return d
