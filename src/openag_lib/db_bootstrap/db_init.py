import os
import json
import time
import subprocess
from os import path
from shutil import rmtree
from tempfile import mkdtemp
from couchdb.http import urljoin

from ..config import config
from .bootstrap_couch import BootstrapServer, ResourceNotFound
from .db_config import generate_config
from .db_names import all_dbs
from openag_lib.db_bootstrap import _design


def db_init(db_url, api_url):
    """
    Initialize the database server. Sets some configuration parameters on the
    server, creates the necessary databases for this project, pushes design
    documents into those databases.
    """
    db_config = generate_config(api_url)
    server = BootstrapServer(db_url)

    # Configure the CouchDB instance itself
    config_items = []
    for section, values in db_config.items():
        for param, value in values.items():
            config_items.append((section, param, value))

    print "Applying CouchDB configuration"
    for section, param, value in config_items:
        url = urljoin(server.resource.url, "_config", section, param)
        try:
            current_val = server.resource.session.request( "GET", url \
                )[2].read().strip()
        except ResourceNotFound:
            current_val = None
        desired_val = '"{}"'.format(value.replace('"', '\\"'))
        if current_val != desired_val:
            status = server.resource.session.request(
                "PUT", url, body=desired_val
            )[0]
            # Unless there is some delay between requests, CouchDB gets
            # sad for some reason
            if status != 200:
                raise Exception(
                    'Failed to set configuration parameter "{}": {}'.format(
                        param, res.content)
                )
            time.sleep(1)

    # Create all dbs on the server
    print "Creating databases"
    for db_name in all_dbs:
        server.get_or_create(db_name)

    # Push design documents
    print "Pushing design documents"
    design_path = os.path.dirname(_design.__file__)
    server.push_design_documents(design_path)

    # Save the local server
    config["local_server"]["url"] = db_url



