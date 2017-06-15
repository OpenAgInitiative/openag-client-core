"""
Shared utilities for openag scripts.
"""
import os
import re
from urlparse import urlparse

def index_by_id(docs):
    """Index a list of docs using `_id` field.
    Returns a dictionary keyed by _id."""
    return {doc["_id"]: doc for doc in docs}

def dedupe_by(things, key=None):
    """
    Given an iterator of things and an optional key generation function, return
    a new iterator of deduped things. Things are compared and de-duped by the
    key function, which is hash() by default.
    """
    if not key:
        key = hash
    index = {key(thing): thing for thing in things}
    return index.values()

def parent_dirname(file_path):
    return os.path.basename(os.path.dirname(file_path))

def make_dir_name_from_url(url):
    """This function attempts to emulate something like Git's "humanish"
    directory naming for clone. It's probably not a perfect facimile,
    but it's close."""
    url_path = urlparse(url).path
    head, tail = os.path.split(url_path)
    # If tail happens to be empty as in case `/foo/`, use foo.
    # If we are looking at a valid but ugly path such as
    # `/foo/.git`, use the "foo" not the ".git".
    if len(tail) is 0 or tail[0] is ".":
        head, tail = os.path.split(head)
    dir_name, ext = os.path.splitext(tail)
    return dir_name

