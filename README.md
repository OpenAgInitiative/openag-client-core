OpenAg Brain
============

This repository holds code that runs on the main computing board of an OpenAg
food computer. In builds on top of [CouchDB](http://couchdb.apache.org/) for
data storage. In particular, the "core" code in this respository reads a
configuration of software modules from a CouchDB instance and then runs those
modules. The modules themselves are responsible for interfacing with hardware,
running control loops, posting the grow data to CouchDB instance, running
recipes, and performing any other tasks required for operation of the food
computer.

Installation
------------

First, install an instance of CouchDB on your machine. There are installation
instructions [here](http://docs.couchdb.org/en/1.6.1/install/index.html) for
doing so. For newer versions of Ubuntu (13.10 and up), this can be done via
`sudo apt-get install couchdb`. Once CouchDB is installed, it should
automatically start itself on `localhost:5984`.

Next, clone the repository and install the contained Python package using
`pip`:

    git clone https://github.com/OpenAgInitiative/openag_brain.git
    cd openag_brain
    pip3 install .

Finally, initialize the CouchDB database by running the `init_db` command

    python3 -m openag.brain.core.init_db
