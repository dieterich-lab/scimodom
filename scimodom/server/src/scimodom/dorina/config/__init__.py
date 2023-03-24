#!/usr/bin/env python
# -*- coding: utf-8
import logging
import sys
from io import open
from os import path

from six.moves import configparser

from scimodom.dorina.utils import validate_data_path

_basedir = path.dirname(path.abspath(__file__))
_default_name = 'default.cfg'


def load_configuration(config_path=path.join(_basedir, _default_name)):
    configuration = configparser.ConfigParser()
    with open(config_path, encoding="utf-8") as f:
        try:
            configuration.read_file(f)
        except AttributeError:  # py27 support
            configuration.readfp(f)
    return configuration


def validate_configuration(configuration):
    default_path = configuration.get('DEFAULT', 'data_path')
    if '~' in default_path:
        configuration.set(
            'DEFAULT', 'data_path', value=validate_data_path(default_path))

    return configuration


config = load_configuration()
config = validate_configuration(config)
