#!/usr/bin/env
# -*- coding: utf-8 -*-
import os

data = {
    'username' : 'USERNAME',
    'password' : 'PASSWORD'
}
download_courses = [] # List of courses you **want** to download e.g. ['CZ1001', 'CZ1002', 'CZ1003']
replace_files = False # Force replace files?
folder_path = os.path.dirname(__file__) # Custom download path, e.g. os.path.join("D:\", "School", "NTU Learn")
