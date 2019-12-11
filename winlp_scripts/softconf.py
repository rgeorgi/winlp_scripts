"""
This module provides an interface for programmatically
interfacing with softconf
"""

import pickle
import re

import requests
import xlrd
from bs4 import BeautifulSoup, Tag
from typing import Union
import pandas



class FailedLogin(Exception): pass
class HTTP404(Exception): pass

class SoftconfConnection(object):

    def __init__(self, username: str, password: str, base_url: str):
        self.base_url = base_url
        self.session = self._login(username, password)

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


    def submission_information(self, bytes = False) -> Union[pandas.DataFrame, bytes]:
        response = self.session.post(
            url=self.base_url+'manager/scmd.cgi',
            params={'scmd':'makeSpreadsheet'},
            data={
                "Type": "submissions",
                "Field{0}": "paperID",
                "Field{1}": "",
                "Field{2}": "",
                "Field{3}": "",
                "Field{4}": "title",
                "Field{5}": "",
                "Field{6}": "",
                "Field{7}": "",
                "Field{8}": "authors",
                "Field{9}": "",
                "Field{10}": "",
                "Field{11}": "",
                "Field{12}": "acceptStatus",
                "Field{13}": "",
                "Field{14}": "",
                "Field{15}": "",
                "Field{16}": "dateReceived",
                "Field{17}": "",
                "Field{18}": "",
                "Field{19}": "",
                "Field{20}": "contactUsername",
                "Field{21}": "",
                "Field{22}": "",
                "Field{23}": "",
                "Field{24}": "contactFirstname",
                "Field{25}": "",
                "Field{26}": "",
                "Field{27}": "",
                "Field{28}": "contactLastname",
                "Field{29}": "",
                "Field{30}": "",
                "Field{31}": "",
                "Field{32}": "",
                "Field{33}": "",
                "Field{34}": "",
                "Field{35}": "",
                "Field{36}": "",
                "Field{37}": "",
                "Field{38}": "",
                "Field{39}": "",
                "Field{40}": "",
                "Field{41}": "",
                "SubmitButton": "Spreadsheet",
                "spreadsheet_type": "xlsx"})
        if bytes:
            return response.content
        else:
            book = xlrd.open_workbook(file_contents=response.content)
            return pandas.read_excel(book)

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


