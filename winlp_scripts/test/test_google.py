"""
Test the functionality for Google spreadsheets
"""
from pytest_testconfig import config

from winlp_scripts.google_sheets import auth_google

def test_authentication():
    auth_google()