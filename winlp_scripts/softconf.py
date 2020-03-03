"""
This module provides an interface for programmatically
interfacing with softconf
"""

import re
import requests
import xlrd
from bs4 import BeautifulSoup, Tag
from typing import Union, List
import pandas



class ConfigException(Exception): pass
class FailedLogin(Exception): pass
class HTTP404(Exception): pass

class SoftconfConnection(object):

    def __init__(self, username: str, password: str, base_url: str):
        self.base_url = base_url
        self.session = self._login(username, password)

    @classmethod
    def from_conf(cls, conf: dict):
        sc = conf.get('softconf', {})
        user = sc.get('user')
        pw = sc.get('pass')
        url_base = sc.get('url_base')

        if (sc is None) or (user is None) or (pw is None):
            raise ConfigException('"user", "pass", and "url_base" must be specified for the "softconf" section \
            in the config file.')


        return cls(user, pw, url_base)

    def _login(self, username: str, password: str) -> requests.Session:
        """
        Log into the softconf system using the provided username
        and password, and return a session that can be stored to
        use the saved login cookies.
        """
        login_url = self.base_url + 'login/scmd.cgi'
        s = requests.Session()
        response = s.post(url=login_url,
                          params={"scmd": "login"},
                          data={"username": username,
                                "password": password})

        # Check for 404 errors
        if response.status_code == 404:
            raise HTTP404

        data = BeautifulSoup(response.text, features="lxml")

        title = data.find('title').text # type: str

        # Check to see if login was successful
        if title.endswith('Login'):
            raise FailedLogin('Invalid Login Credentials')
        return s

    def author_information(self,
                           bytes=False) -> Union[pandas.DataFrame, bytes]:
        """
        Retrieve the spreadsheet of author information
        :param session:
        :return:
        """
        response = self.session.post(url=self.base_url + "manager/scmd.cgi",
                                     params={"scmd": "makeSpreadsheet"},
                                     data={"Type": "submissions",
                                           "Field{0}": "paperID",
                                           "Field{1}": "passcode",
                                           "Field{2}": "title",
                                           "Field{3}": "authors",
                                           "Field{4}": "acceptStatus",
                                           "Field{5}": "conditions",
                                           "Field{6}": "abstract",
                                           "Field{7}": "dateReceived",
                                           "Field{8}": "authorInfo",
                                           "Field{9}": "contactUsername",
                                           "Field{10}": "contactTitle",
                                           "Field{11}": "contactFirstname",
                                           "Field{12}": "contactLastname",
                                           "Field{13}": "contactAffiliation",
                                           "Field{14}": "contactAffiliationDpt",
                                           "Field{15}": "contactJobFunction",
                                           "Field{16}": "contactPhone",
                                           "Field{17}": "contactMobile",
                                           "Field{18}": "contactFax",
                                           "Field{19}": "email",
                                           "Field{20}": "contactAddress",
                                           "Field{21}": "contactCity",
                                           "Field{22}": "contactState",
                                           "Field{23}": "contactZip",
                                           "Field{24}": "contactCountry",
                                           "Field{25}": "contactBiography",
                                           "Field{26}": "authorsWithAffiliations",
                                           "Field{27}": "allAuthorEmails",
                                           "Field{28}": "field_GenderInfo",
                                           "Field{29}": "field_RaceInfo",
                                           "Field{30}": "field_RegionInfo",
                                           "Field{31}": "field_CitizenshipInfo",
                                           "Field{32}": "field_race_specification",
                                           "Field{33}": "field_copyrightSig",
                                           "Field{34}": "field_jobTitle",
                                           "Field{35}": "field_orgNameAddress",
                                           "Field{36}": "field_ACL_Length",
                                           "Field{37}": "field_ACL_Format",
                                           "Field{38}": "field_ACL_Author_Guidelines",
                                           "Field{39}": "final_attachments_ok",
                                           "Field{40}": "final_tags",
                                           "Field{41}": "final_notes",
                                           "SubmitButton": "Spreadsheet",
                                           "spreadsheet_type": "xlsx"})
        xlsx_data = response.content
        if bytes:
            return xlsx_data
        else:
            book = xlrd.open_workbook(file_contents=xlsx_data)
            return pandas.read_excel(book)

    def check_plagiarism(self):
        return self._get_spreadsheet(type="dude", keys=[])

    def _get_spreadsheet(self, type: str,
                         keys: List[str],
                         bytes: bool = False,
                         other_data: dict = None) -> Union[pandas.DataFrame, bytes]:
        data = {"Type": type,
                "SubmitButton": "Spreadsheet",
                "spreadsheet_type": "xlsx"
                }
        if other_data is not None:
            data.update(other_data)

        # The softconf interface allows up to 41 fields
        # in the spreadsheet.
        for i in range(42):
            val = keys[i] if i < len(keys) else ''
            data['Field{{{}}}'.format(i)] = val

        response = self.session.post(
            url=self.base_url+'manager/scmd.cgi',
            params={'scmd': 'makeSpreadsheet'},
            data=data)

        # Either return as raw bytes (if we want to download the spreadsheet)
        # or as a pandas dataframe.
        if bytes:
            return response.content
        else:
            book = xlrd.open_workbook(file_contents=response.content)
            df = pandas.read_excel(book) # type: pandas.DataFrame
            # Rename the columns to be the same as the provided keys
            df.rename(columns={old_key:new_key for old_key, new_key in zip(df.keys(), keys)}, inplace=True)
            return df

    def submission_information(self, bytes = False, keys: List[str] = None) -> Union[pandas.DataFrame, bytes]:
        """
        Retrieve the spreadsheet about submission information.

        If the "keys" var is specified, use that instead of the default keys.
        """
        keys = keys if keys is not None else [PAPER_ID, PASSCODE, MC_USERNAME, MC_EMAIL, PAPER_TITLE, ALL_EMAILS]
        return self._get_spreadsheet(
            'submissions', keys, bytes=bytes
        )

    def reviews(self, bytes=False, keys: List[str] = None) -> Union[pandas.DataFrame, bytes]:
        """
        Retrieve reviews
        """
        if keys is None:
            keys = [PAPER_ID, SCORE_CLARITY, SCORE_ORIGINALITY, SCORE_CORRECTNESS, SCORE_COMPARISON, SCORE_THOROUGHNESS, SCORE_IMPACT, REVIEWER_CONFIDENCE, SCORE_RECOMMENDATION, REVIEW_DETAILED_COMMENTS, REVIEW_AUTHOR_QUESTIONS]
        return self._get_spreadsheet(
            'customreviews',
            keys=keys,
            bytes=bytes,
            other_data={'spreadsheetReviewsView': 'byReview'}
        )

    def retrieve_pdf(self, submission_id: int) -> bytes:
        """
        Retrieve the PDF for the given submission ID.

        :param submission_id: The int of the submission ID
        """
        response = self.session.get(url=self.base_url+'pub/scmd.cgi',
                               params={'scmd':'getPaper',
                                       'paperID':submission_id,
                                       'filename':'{}.pdf'.format(submission_id)})
        return response.content

    def download_submission_page(self):
        response = self.session.get(self.base_url + 'manager/scmd.cgi?scmd=submitPaperCustom_editor&page_theid=1')
        return response.text

# -------------------------------------------
# Page Parsing Methods
# -------------------------------------------

def textarea_text(textarea_tag: Tag):
    return ''.join([str(s) for s in textarea_tag.contents])

def field_if_exists(tag: Tag, search_text: str, type='textarea'):
    field_td = tag.find(text=re.compile(search_text, flags=re.I))  # type: Tag
    if field_td is not None:
        if type == 'textarea':
            field_value = textarea_text(field_td.find_next('textarea'))
            return field_value
        else:
            field_value = field_td.find_next('input', attrs={'type':'text'})['value']
            return field_value
    return ''

def convert_submission_page_to_text(sub_page_html: str):
    sub_page_data = BeautifulSoup(sub_page_html, features='lxml')
    title = sub_page_data.find('input', id='currentpage_newname')['value']
    items = sub_page_data.find('div', id='theitems').find_all(class_='portlet')

    for item in items:
        item_name = item.find(class_='portlet-header').find('td').text.strip()

        # Text handling
        if item_name.startswith('TextBox'):
            print(item_name)

        elif item_name.startswith('Text'):
            print(textarea_text(item.find('textarea')))

        # Dividing Lines
        elif item_name.startswith('Line'):
            print('-'*80)

        # Selectors
        elif item_name.startswith('Selector'):
            print(item.find(attrs={'type':'text'})['value'])
            options = item.find_all('textarea')[1].text
            for option in options.split('\n'):
                print(' - {}'.format(option))


        # Other fields
        else:
            print(item_name)
            print(field_if_exists(item, '.*title.*', type='text'), end=' ')
            print(field_if_exists(item, '.*description.*'), end='\n')

    # print(items)



# -------------------------------------------
# Define the keys used for generating the spreadsheets
# -------------------------------------------
ALL_EMAILS = 'allAuthorEmails'
ALL_NAMES = 'authors'
MC_LAST = 'contactLastname'
MC_FIRST = 'contactFirstname'
MC_EMAIL = 'email'
MC_USERNAME = 'contactUsername'
MC_TITLE = 'contactTitle'
MC_AFFILLIATION = 'contactAffiliation'
MC_DEPT = 'contactAffiliationDpt'
MC_JOB = 'contactJobFunction'
MC_PHONE = 'contactPhone'
MC_MOBILE = 'contactMobile'
MC_ADDRESS = 'contactAddress'
MC_CITY = 'contactCity'
MC_STATE = 'contactState'
MC_ZIP = 'contactZip'
MC_COUNTRY = 'contactCountry'
MC_BIO = 'contactBiography'
MC_GENDER = 'field_GenderInfo'
MC_RACE = 'field_RaceInfo'
MC_REGION = 'field_RegionInfo'
MC_CITIZENSHIP = 'field_CitizenshipInfo'
MC_RACE_SPEC = 'field_race_specification'
PAPER_ID = 'paperID'
PAPER_TITLE = 'title'
PAPER_ACCEPT = 'acceptStatus'
PAPER_ABSTRACT = 'abstract'
PAPER_RECEIVED = 'dateReceived'
PASSCODE = 'passcode'

# --------------------------------------------
# Review Keys
# --------------------------------------------
REVIEWER = 'reviewer'
REVIEWER_FIRST = 'reviewerFirstName'
REVIEWER_LAST = 'reviewerLastName'
REVIEWER_EMAIL = 'reviewerEmail'
SCORE_CLARITY = 'ScoreField{Clarity}'
SCORE_ORIGINALITY = 'ScoreField{Originality___Innovativeness}'
SCORE_CORRECTNESS = 'ScoreField{Soundness___Correctness}'
SCORE_COMPARISON = 'ScoreField{Meaningful_Comparison}'
SCORE_THOROUGHNESS = 'ScoreField{Thoroughness}'
SCORE_IMPACT = 'ScoreField{Impact_of_Ideas_or_Results}'
REVIEWER_CONFIDENCE = 'ScoreField{Reviewer_Confidence}'
SCORE_RECOMMENDATION='ScoreField{Recommendation}'
REVIEW_DETAILED_COMMENTS='field_raw_Detailed_Comments'
REVIEW_AUTHOR_QUESTIONS='field_raw_Questions_for_Authors'


