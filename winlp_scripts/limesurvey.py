"""
This module is for handling interactions with the LimeSurvey software.

Unfortunately, while some of LimeSurvey's features are available
through an xml-rpc API, some
"""

import base64
import os
from typing import List

import requests
from bs4 import BeautifulSoup as bs
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from xlrd.book import Book
from xlrd.sheet import Sheet
from xlrd import open_workbook
from pandas import read_excel

from xmlrpc.client import ServerProxy

# -------------------------------------------
# URLS
# -------------------------------------------
def _get_csrf(response: requests.Response):
    """
    Obtain the CSRF token from a given LimeSurvey page.

    :param response:
    :return:
    """
    data = bs(response.content.decode('utf-8'), features='lxml')
    csrf = data.find('input', attrs={'name': 'YII_CSRF_TOKEN'})['value']
    return csrf

class LimeSurveyConnection(object):
    """
    Class to log into the LimeSurvey website, and maintain
    a connection.
    """
    def __init__(self, url_base, username, password):
        # the `ServerProxy` is the xml-rpc client.
        self.sp = ServerProxy(os.path.join(url_base, 'admin/remotecontrol'))
        self.url_base = url_base
        self._username = username
        self._password = password
        self._key = self.get_session_key()
        self._session = self._http_login()

    def list_surveys(self) -> List[dict]:
        return self.sp.list_surveys(self._key)

    def get_session_key(self) -> str:
        return self.sp.get_session_key(self._username, self._password)

    def list_questions(self, survey_id):
        return self.sp.list_questions(self._key, survey_id)

    def export_responses(self, survey_id):
        encoded = self.sp.export_responses(self._key, survey_id, 'xls',
                                           '', 'complete')
        decoded = base64.b64decode(encoded)
        book = open_workbook(file_contents=decoded)
        return read_excel(book)

    # -------------------------------------------
    # HTTP Methods
    # -------------------------------------------
    # Unfortunately, the XML-RPC infrastructure in limesurvey
    # doesn't support downloading files properly, but makes downloading
    # spreadsheets a pain. So, these methods are provided
    # in order to download attached files.

    def _http_login(self) -> requests.Session:
        """
        Initialize a session over http(s), and store the session and its
        relevant cookies for later access.
        """
        s = requests.Session()
        login_url = os.path.join(self.url_base, 'admin/authentication/sa/login')
        r = s.get(url=login_url)
        csrf = _get_csrf(r)
        r = s.post(login_url,
                   headers={
                   },
                   data={
                       'user': self._username,
                       'password': self._password,
                       'YII_CSRF_TOKEN': csrf,
                       "loginlang": "default",
                       "login_submit": "login",
                       "authMethod": "Authdb",
                   })
        return s

    def _http_logout(self):
        """
        Logout of the session. Used on __exit__.
        """
        url = os.path.join(self.url_base, 'admin/authentication/sa/logout')
        self._session.get(url)

    def _get_zip(self, url: str, bytes=False):
        resp = self._session.get(url)
        try:
            if bytes:
                return resp.content
            else:
                buffer = BytesIO(resp.content)
                return ZipFile(buffer)
        except BadZipFile as bze:
            return None

    def get_download_for_response(self, survey_id: int, response_id: int, bytes=False):
        """
        Given survey and response IDs, retrieve the zipfile associated with that
        response.
        """
        url = os.path.join(self.url_base,
                           'admin/responses/sa/actionDownloadfiles/surveyid/{}/sResponseId/{}'.format(survey_id, response_id))
        return self._get_zip(url, bytes=bytes)

    def get_download_for_response_list(self, survey_id: int, responses: List[int], bytes=False):
        url = os.path.join(self.url_base, 'admin/responses/sa/actionDownloadfiles/iSurveyId/{}/sResponseId/{}'.format(
            survey_id,
            ','.join([str(i) for i in responses])))
        return self._get_zip(url, bytes=bytes)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sp.release_session_key(self._key)
        self._http_logout()
