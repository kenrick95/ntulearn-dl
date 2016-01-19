#!/usr/bin/env
# -*- coding: utf-8 -*-

import config
import os
import time
import math
import sys
import re
import requests
from requests import Request
from bs4 import BeautifulSoup
import urllib
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(__file__)
if os.path.isdir(config.folder_path):
    BASE_DIR = os.path.relpath(config.folder_path)

NTULEARN_BASE_URL = 'https://ntulearn.ntu.edu.sg'

def format_bytes(bytes):
    """
    Get human readable version of given bytes.
    Ripped from https://github.com/rg3/youtube-dl
    """
    if bytes is None:
        return 'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return '{0:.2f}{1}'.format(converted, suffix)

class DownloadProgress(object):
    """
    Report download progress.
    Inspired by https://github.com/rg3/youtube-dl
    """

    def __init__(self, total):
        if total in [0, '0', None]:
            self._total = None
        else:
            self._total = int(total)

        self._current = 0
        self._start = 0
        self._now = 0

        self._finished = False

    def start(self):
        self._now = time.time()
        self._start = self._now

    def stop(self):
        self._now = time.time()
        self._finished = True
        self._total = self._current
        self.report_progress()

    def read(self, bytes):
        self._now = time.time()
        self._current += bytes
        self.report_progress()

    def calc_percent(self):
        if self._total is None:
            return '--%'
        percentage = int(float(self._current) / float(self._total) * 100.0)
        done = int(percentage/2)
        return '[{0: <50}] {1}%'.format(done * '#', percentage)

    def calc_speed(self):
        dif = self._now - self._start
        if self._current == 0 or dif < 0.001:  # One millisecond
            return '---b/s'
        return '{0}/s'.format(format_bytes(float(self._current) / dif))

    def report_progress(self):
        """Report download progress."""
        percent = self.calc_percent()
        total = format_bytes(self._total)

        speed = self.calc_speed()
        total_speed_report = '{0} at {1}'.format(total, speed)

        report = '\r{0: <56} {1: >30}'.format(percent, total_speed_report)

        if self._finished:
            print report
        else:
            print report
            print
        sys.stdout.flush()


def download(session, url, path):
    """
        download single file from url
    """

    try:
        r = session.get(url, stream=True)
    except requests.exceptions.ConnectionError:
        print 'connection timeout, skippping...'
        return

    # types of file to skip
    if r.headers.get('content-type') in ['text/html']:
    	return

    filename = urllib.unquote(r.url.split('/')[-1])
    filesize = (int)(r.headers.get('content-length'))

    # only show progess if file size exceeds 3M
    show_progess = filesize > 1024 ** 2 * 3

    if show_progess:
    	progress = DownloadProgress(filesize)

    chunk_size = 1048576

    if r.ok:
    	if filesize > 1024 ** 2:
        	print '%s found (%.3f MB)' % (filename, filesize/1024.0/1024.0)
        else:
        	print '%s found (%.3f KB)' % (filename, filesize/1024.0)

    else:
        print 'Could not find the file'
        return

    valid_chars = "-_.() "
    path = "".join([x for x in path if (x.isalnum() or x in valid_chars or x == os.path.sep)])

    if not os.path.exists(path):
        os.makedirs(path)

    uri = os.path.join(path, filename)

    if os.path.isfile(uri):
        if os.path.getsize(uri) != filesize:
            print 'file seems corrupted, download again'
        elif config.replace_files:
            print 'downloading again'
        else:
            print 'already downloaded, skipping...'
            print
            return

    with open(uri, 'wb') as handle:
        print 'Start downloading...'
        if show_progess:
        	progress.start()
        for chunk in r.iter_content(chunk_size):
            if not chunk:
                if show_progess:
                	progress.stop()
                break
            if show_progess:
            	progress.read(chunk_size)

            handle.write(chunk)

        print '%s downloaded' % filename
        print

def download_document(session, course_id, content_id, path):
    content_detail_url = 'https://ntulearn.ntu.edu.sg/webapps/Bb-mobile-BBLEARN/contentDetail'
    params = {
        'v' :  '1',
        'f' : 'xml',
        'ver' : '4.1.2',
        'registration_id' : "29409",
        'rich_content_level' : 'RICH',
        'course_id' : course_id,
        'content_id' : content_id
    }

    resp = session.get(content_detail_url, params=params)

    content_detail_xml = ET.fromstring(resp.content)
    for attachment in content_detail_xml.iter('attachment'):
        name = attachment.get('name')
        uri = attachment.get('uri')
        filesize = attachment.get('filesize')
        linkLabel = attachment.get('linkLabel')
        fromHtmlParsing = attachment.get('fromHtmlParsing')
        modified_date = attachment.get('modifiedDate')

        download(session, NTULEARN_BASE_URL + uri, path)



def iter(session, course_id, current_map_item, path):
    if current_map_item.find('children') is None:
        return

    for map_item in current_map_item.find('children').findall('map-item'):
        name = map_item.get('name')
        linktype = map_item.get('linktype')
        isfolder = map_item.get('isfolder')
        content_id = map_item.get('contentid')
        datemodified = map_item.get('datemodified')
        viewurl = map_item.get('viewurl')
        new = map_item.get('new')

        if linktype.lower() == 'resource/x-bb-folder':
            iter(session, course_id, map_item, os.path.join(path, name))
        elif linktype.lower() == 'resource/x-bb-document' or linktype.lower() == 'resource/x-bb-file':
            download_document(session, course_id, content_id, path)


def main():
    session = requests.Session()
    headers = {
        "User-Agent" : "Mobile%20Learn/3333 CFNetwork/711.1.16 Darwin/14.0.0",
        "Content-Type" : "application/x-www-form-urlencoded",
        "Accept" : "*/*"
    }

    session.headers.update(headers)

    params = {
        'v' :  '2',
        'f' : 'xml',
        'ver' : '4.1.2',
        'registration_id' : "29409"
	}

    data = {
        'username' : config.data['username'],
        'password' : config.data['password']
    }

    url = 'https://ntulearn.ntu.edu.sg/webapps/Bb-mobile-BBLEARN/sslUserLogin'

    req = Request(
        "POST",
        url,
        params=params,
        data=data
    )
    prepped = req.prepare()

    resp = session.send(prepped)
    if resp.status_code == 200:
        print 'login successful'
    else:
        print 'login failed'

    session.headers.update({'Cookie':'JSESSIONID={}; s_session_id={}; session_id={}; dtCookie={}'.format(session.cookies.get('JSESSIONID'), session.cookies.get('s_session_id'), session.cookies.get('session_id'), session.cookies.get('dtCookie'))})

    enrollments_url = 'https://ntulearn.ntu.edu.sg/webapps/Bb-mobile-BBLEARN/enrollments'
    params={
        'v' : '1',
        'f' : 'xml',
        'ver' : '4.1.2',
        'registration_id' : '29409',
        'course_type' : 'ALL',
        'include_grades'  : 'false'
    }

    resp = session.get(enrollments_url, params=params)

    courses_xml = ET.fromstring(resp.content)

    courses = courses_xml.iter("course")
    if courses == 0:
        print 'no currently registed courses'

    course_map_url = 'https://ntulearn.ntu.edu.sg/webapps/Bb-mobile-BBLEARN/courseMap'

    for idx, course in enumerate(courses):
        course_id = course.get('bbid')
        course_name = course.get('name')
        course_type = course.get('courseid')

        print '-' * 30
        print 'Course {} - {}: {}'.format(idx, course_type, course_name)

        ok = False
        for c in config.download_courses:
            if course_name.count(c) > 0:
                ok = True
                break
        if not ok:
            print "Course not downloaded."
            continue

        params={
            'v' : '1',
            'f' : 'xml',
            'ver' : '4.1.2',
            'registration_id' : '29409',
            'course_id' : course_id
        }

        resp = session.get(course_map_url, params=params)

        course_map_xml = ET.fromstring(resp.content)

        for item in course_map_xml.find('map').findall('map-item'):
            name = item.get('name')
            linktype = item.get('linktype')
            if 'recorded lectures' in name.lower(): continue
            if linktype.lower() != 'content': continue
            content_id = item.get('content_id')
            isfolder = item.get('isfolder')
            viewurl = item.get('viewurl')

            iter(session, course_id, item, os.path.join(BASE_DIR, course_name, name))


if __name__ == '__main__':
    main()
