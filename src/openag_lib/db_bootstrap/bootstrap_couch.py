"""
This module consists of code for configuring a CouchDB server instance.
"""
import os
import json
import requests
from urllib import quote
from couchdb import Server as _Server
from couchdb.http import ResourceNotFound
from urlparse import urljoin


class BootstrapServer(_Server):
    """
    Class that represents a single CouchDB server instance and provides
    functions for interfacing with that server
    """
    def get_or_create(self, db_name):
        """
        Creates the database named `db_name` if it doesn't already exist and
        return it
        """
        if not db_name in self:
            res = self.resource.put(db_name)
            if not res[0] == 201:
                raise RuntimeError(
                    'Failed to create database "{}"'.format(db_name)
                )
        return self[db_name]

    def replicate(self, doc_id, source, target, continuous=False):
        """
        Starts a replication from the `source` database to the `target`
        database by writing a document with the id `doc_id` to the "_relicator"
        database
        """
        if doc_id in self["_replicator"]:
            return
        data = {
            "_id": doc_id,
            "source": source,
            "target": target,
            "continuous": continuous
        }
        self["_replicator"][doc_id] = data

    def cancel_replication(self, doc_id):
        """
        Cancels the replication with the id `doc_id`
        """
        if doc_id not in self["_replicator"]:
            return
        del self["_replicator"][doc_id]

    def create_user(self, username, password):
        """
        Creates a user in the CouchDB instance with the username `username` and
        password `password`
        """
        user_id = "org.couchdb.user:" + username
        res = self["_users"].resource.put(
            user_id, body=json.dumps({
                "_id": user_id,
                "name": username,
                "roles": [],
                "type": "user",
                "password": password,
                "farms": []
            })
        )
        if res[0] == 409:
            raise RuntimeError(
                'The username "{}" is already taken'.format(username)
            )
        elif res[0] != 201:
            raise RuntimeError(
                "Failed to create user ({}): {}".format(
                    res.status_code, res.content
                )
            )

    def log_in(self, username, password):
        """
        Logs in to the CouchDB instance with the credentials `username` and
        `password`
        """
        self.resource.credentials = (username, password)
        return self.resource.get_json("_session")[2]

    def get_user_info(self):
        """
        Returns the document representing the currently logged in user on the
        server
        """
        try:
            user_id = "org.couchdb.user:"+self.resource.credentials[0]
        except TypeError:
            raise RuntimeError(
                "Please log in before trying to access your user's info"
            )
        status, _, body = self["_users"].resource.get_json(user_id)
        if status != 200:
            raise RuntimeError(
                "Failed to get user info"
            )
        return body

    def log_out(self):
        """ Logs out of the CouchDB instance """
        self.resource.credentials = None

    def push_design_documents(self, design_path):
        """
        Push the design documents stored in `design_path` to the server
        """
        for db_name in os.listdir(design_path):
            if db_name.startswith("__") or db_name.startswith("."):
                continue
            db_path = os.path.join(design_path, db_name)
            doc = self._folder_to_dict(db_path)
            doc_id = "_design/openag"
            doc["_id"] = doc_id
            db = self[db_name]
            if doc_id in db:
                old_doc = db[doc_id]
                doc["_rev"] = old_doc["_rev"]
                if doc == old_doc:
                    continue
            db[doc_id] = doc

    def _folder_to_dict(self, path):
        """
        Recursively reads the files from the directory given by `path` and
        writes their contents to a nested dictionary, which is then returned.
        """
        res = {}
        for key in os.listdir(path):
            if key.startswith('.'):
                continue
            key_path = os.path.join(path, key)
            if os.path.isfile(key_path):
                val = open(key_path).read()
                key = key.split('.')[0]
                res[key] = val
            else:
                res[key] = self._folder_to_dict(key_path)
        return res

