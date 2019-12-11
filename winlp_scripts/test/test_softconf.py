"""
Unit tests for the softconf interface.
"""


# -------------------------------------------
# Load the config file and softconf setup
# info.
# -------------------------------------------
from pytest_testconfig import config
from winlp_scripts.softconf import SoftconfConnection

def test_init():
    user = config['softconf']['user']
    pw = config['softconf']['pass']
    url_base = config['softconf']['url_base']
    scc = SoftconfConnection(user, pw, url_base)
    assert scc is not None
    return scc

scc = test_init()

def test_submission_page():
    print(scc.submission_information().keys())