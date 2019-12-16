"""
Unit tests for the softconf interface.
"""


# -------------------------------------------
# Load the config file and softconf setup
# info.
# -------------------------------------------
from pytest_testconfig import config
import pytest
from winlp_scripts.softconf import SoftconfConnection, FailedLogin
from pandas import DataFrame

def test_login_succeeds():
    user = config['softconf']['user']
    pw = config['softconf']['pass']
    url_base = config['softconf']['url_base']
    scc = SoftconfConnection(user, pw, url_base)
    assert scc is not None
    return scc

scc = test_login_succeeds()

def test_submissions():
    submission_info = scc.submission_information()
    print(submission_info.keys())
    # assert isinstance(submission_info, DataFrame)

def test_failed_login():
    url_base = config['softconf']['url_base']
    with pytest.raises(FailedLogin):
        scc = SoftconfConnection('none', 'none', url_base)
