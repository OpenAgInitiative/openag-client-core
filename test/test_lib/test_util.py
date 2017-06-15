#debugrob: remove tests that are not for code in _lib/util.py

from openag_lib.util import (
    index_by_id, dedupe_by, parent_dirname, make_dir_name_from_url
)

EXAMPLE_DOCS = [
    {
        "_id": "foo",
        "type": "a"
    },
    {
        "_id": "foo",
        "type": "b"
    },
    {
        "_id": "bar",
        "type": "c"
    }
]

def get_id(doc):
    return doc["_id"]

def test_index_by_id():
    index = index_by_id(EXAMPLE_DOCS)
    # Assert multiple items with same key are de-duped
    assert len(index.keys()) == 2
    # Assert last item wins
    assert index["foo"]["type"] == "b"

def test_dedupe_by():
    docs = dedupe_by(EXAMPLE_DOCS, get_id)
    assert len(docs) == 2

def test_parent_dirname():
    assert parent_dirname("foo/bar.git") == "foo"
    assert parent_dirname("foo/bar/baz") == "bar"
    assert parent_dirname("foo/bar/baz/") == "baz"

def test_make_dir_name_from_url():
    url_a = "http://github.com/OpenAgInitiative/openag_am2315.git"
    a = make_dir_name_from_url(url_a)
    assert a == "openag_am2315", a

    url_b = "http://foo.xyz:8000/openag_am2315/.git"
    b = make_dir_name_from_url(url_b)
    assert b == "openag_am2315", b

    url_c = "http://foo.xyz/bar/"
    c = make_dir_name_from_url(url_c)
    assert c == "bar", c
