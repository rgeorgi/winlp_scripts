"""
Unit tests for working with the LimeSurvey software.
"""
import os
import yaml

from pytest_testconfig import config

user = config['limesurvey']['user']
pw = config['limesurvey']['pass']
url_base = config['limesurvey']['url_base']

def test_init():
    from winlp_scripts.limesurvey import LimeSurveyConnection
    ls = LimeSurveyConnection(url_base, user, pw)
    assert ls is not None
    assert ls.get_session_key() is not None
    return ls

ls = test_init()

def test_list_surveys():
    ls.list_surveys()