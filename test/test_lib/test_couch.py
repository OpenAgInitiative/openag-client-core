import os
import json
import shutil
import tempfile
import httpretty
from base64 import b64decode

from openag_lib.db_bootstrap.bootstrap_couch import BootstrapServer

@httpretty.activate
def test_get_or_create_db():
    server = BootstrapServer("http://test.test:5984")
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/test", status=404, body=""
    )
    def create_test_db(request, uri, headers):
        httpretty.reset()
        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/test", status=200
        )
        httpretty.register_uri(
            httpretty.PUT, "http://test.test:5984/test", status=500
        )
        return 201, headers, ""
    httpretty.register_uri(
        httpretty.PUT, "http://test.test:5984/test", body=create_test_db
    )
    assert "test" not in server
    test_db = server.get_or_create("test")
    assert "test" in server

@httpretty.activate
def test_replicate():
    # Start a replication
    server = BootstrapServer("http://test.test:5984")
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_replicator"
    )
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_replicator/test",
        status=404
    )
    def replicate_test_src(request, uri, headers):
        httpretty.reset()
        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/_replicator"
        )
        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/_replicator/test",
            status=200, etag="a"
        )
        return 201, headers, json.dumps({
            "id": "test_src", "rev": "a", "ok": True
        })
    httpretty.register_uri(
        httpretty.PUT, "http://test.test:5984/_replicator/test",
        status=201, content_type="application/json", body=replicate_test_src
    )
    server.replicate("test", "test_src", "test_dest", continuous=True)
    assert "test" in server["_replicator"]

    # Make sure replicate is idempotent
    httpretty.register_uri(
        httpretty.PUT, "http://test.test:5984/_replicator/test_src",
        status=500
    )
    server.replicate("test", "test_src", "test_dest", continuous=True)
    assert "test" in server["_replicator"]

    # Cancel the replication
    def cancel_test_replication(request, uri, headers):
        httpretty.reset()
        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/_replicator"
        )
        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/_replicator/test",
            status=404
        )
        return 200, headers, ""
    httpretty.register_uri(
        httpretty.DELETE, "http://test.test:5984/_replicator/test",
        status=200, body=cancel_test_replication
    )
    server.cancel_replication("test")
    assert "test" not in server["_replicator"]

@httpretty.activate
def test_cancel_replication():
    server = BootstrapServer("http://test.test:5984")
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_replicator",
        status=200
    )
    global doc_exists
    doc_exists = True
    def head_test_src(request, uri, headers):
        if doc_exists:
            return 200, headers, ""
        else:
            return 404, headers, ""
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_replicator/test_src",
        etag="a", body=head_test_src
    )
    def delete_test_src(request, uri, headers):
        global doc_exists
        doc_exists = False
        return 200, headers, ""
    httpretty.register_uri(
        httpretty.DELETE, "http://test.test:5984/_replicator/test_src",
        etag="a", body=delete_test_src
    )
    assert "test_src" in server["_replicator"]
    server.cancel_replication("test_src")
    assert "test_src" not in server["_replicator"]

@httpretty.activate
def test_create_user():
    server = BootstrapServer("http://test.test:5984")
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_users"
    )
    httpretty.register_uri(
        httpretty.PUT, "http://test.test:5984/_users/org.couchdb.user%3Atest",
        status=201
    )
    server.create_user("test", "test")

@httpretty.activate
def test_get_user_info():
    server = BootstrapServer("http://test.test:5984")

    # Try to get user info -- Should fail
    try:
        server.get_user_info()
        assert False, "BootstrapServer.get_user_info should fail when not logged in"
    except RuntimeError as e:
        pass

    def on_get_session(request, uri, headers):
        credentials = request.headers.getheader("Authorization")
        if credentials.startswith("Basic "):
            username, password = b64decode(credentials[6:]).split(":")
            if username == "test" and password == "test":
                return 200, headers, '{"test": "test"}'
        return 401, headers, '{"test": "test"}'
    httpretty.register_uri(
        httpretty.GET, "http://test.test:5984/_session", body=on_get_session,
        content_type="application/json"
    )
    server.log_in("test", "test")
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_users"
    )
    httpretty.register_uri(
        httpretty.GET, "http://test.test:5984/_users/org.couchdb.user%3Atest",
        body='{"test": "test"}', content_type="application/json"
    )
    res = server.get_user_info()
    assert server.get_user_info() == {"test": "test"}
    server.log_out()
    try:
        server.get_user_info()
        assert False, "Shouldn't be able to access the user's info when not logged in"
    except RuntimeError:
        pass

@httpretty.activate
def test_push_design_documents():
    server = BootstrapServer("http://test.test:5984")

    tempdir = tempfile.mkdtemp()
    try:
        test_db_path = os.path.join(tempdir, "test")
        os.mkdir(test_db_path)
        hidden_db_path = os.path.join(tempdir, ".test")
        os.mkdir(hidden_db_path)
        views_path = os.path.join(test_db_path, "views")
        os.mkdir(views_path)
        test_view_path = os.path.join(views_path, "test")
        os.mkdir(test_view_path)
        map_path = os.path.join(test_view_path, "map.js")
        with open(map_path, "w+") as f:
            f.write("test")
        hidden_map_path = os.path.join(test_view_path, ".test.js")
        with open(hidden_map_path, "w+") as f:
            f.write("test")

        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/test"
        )
        def create_design_doc(request, uri, headers):
            obj = {
                "_id": "_design/openag",
                "views": {
                    "test": {
                        "map": "test"
                    }
                }
            }
            if json.loads(request.body) == obj:
                return 200, headers, json.dumps({
                    "id": "_design/openag",
                    "rev": "a"
                })
            else:
                return 500, headers, ""
        httpretty.register_uri(
            httpretty.HEAD, "http://test.test:5984/test/_design/openag",
            status=404
        )
        httpretty.register_uri(
            httpretty.PUT, "http://test.test:5984/test/_design/openag",
            body=create_design_doc, content_type="application/json"
        )
        server.push_design_documents(tempdir)
    finally:
        shutil.rmtree(tempdir)
