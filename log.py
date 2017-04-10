#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日记
"""

import json
import logging
from logging.handlers import RotatingFileHandler
import configs

# def logout(aLogString):
    # """记录日记到指定位置

    # :aLogString: TODO
    # :returns: TODO

    # """
    # instanceForFile().log(logging.INFO, aLogString);

# def logoutError(aLogString):
    # instanceForFile().log(logging.ERROR, aLogString);

# def _logFormat():
    # return logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s");

def instanceForFile(aFileName = "/tmp/JxLog.log", aMaxFileSize = 1024 * 1024 * 5, aMaxFileCount = 5):
    frm =logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s");
    fh = RotatingFileHandler(aFileName, "a", aMaxFileSize, aMaxFileCount);
    fh.setFormatter(frm);
    fh.setLevel(logging.INFO);
    ch = logging.StreamHandler();
    ch.setFormatter(frm);
    log = logging.getLogger("app");
    log.setLevel(logging.DEBUG);
    log.addHandler(fh);
    log.addHandler(ch);
    return log;

def logObject():
    "日记对象"
    return instanceForFile(configs.logFileName());


if __name__ == "__main__":
    logObject().log(logging.DEBUG, "this is Test");
