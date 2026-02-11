# -*- coding: utf-8 -*-
import pytest
from karios.core.utils import sanitize_filename, get_filename

def test_sanitize_filename_standard():
    assert sanitize_filename("standard.tif") == "standard.tif"
    assert sanitize_filename("path/to/standard.tif") == "standard.tif"

def test_sanitize_filename_traversal():
    assert sanitize_filename("..") == "unnamed"
    assert sanitize_filename(".") == "unnamed"
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\etc\\passwd") == "passwd"

def test_sanitize_filename_dangerous_chars():
    assert sanitize_filename("file;name.tif") == "file_name.tif"
    assert sanitize_filename("file&name.tif") == "file_name.tif"
    assert sanitize_filename("file|name.tif") == "file_name.tif"
    assert sanitize_filename("file<name.tif") == "file_name.tif"
    assert sanitize_filename("file>name.tif") == "file_name.tif"
    assert sanitize_filename("file space.tif") == "file_space.tif"

def test_sanitize_filename_empty():
    assert sanitize_filename("") == "unnamed"
    assert sanitize_filename("/") == "unnamed"
    assert sanitize_filename("\\") == "unnamed"

def test_sanitize_filename_dots():
    assert sanitize_filename("...") == "..."
    assert sanitize_filename("....") == "...."

def test_sanitize_filename_reserved_names():
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename("nul.tif") == "nul.tif" # Extension makes it safe on most systems, but our sanitization keeps nul.tif as is.
    # If the base name matches reserved name exactly (ignoring case)
    assert sanitize_filename("NUL") == "_NUL"
    assert sanitize_filename("com1") == "_com1"

def test_sanitize_filename_mixed_separators():
    assert sanitize_filename("dir1/dir2\\file.txt") == "file.txt"

def test_get_filename_security():
    assert get_filename("../../etc/passwd") == "passwd"
    assert get_filename("..\\..\\etc\\passwd") == "passwd"
    assert get_filename("CON") == "_CON"
