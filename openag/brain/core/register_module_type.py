from .models import ModuleTypeModel
from .db_names import DbName

from sys import argv
from uuid import uuid4
from couchdb import Server
from importlib import import_module

def register_module_type(cls, db):
    package_path = cls.__module__
    cls_name = cls.__name__
    cls_path = ':'.join([package_path, cls_name])
    doc = {}

    # Check if the document already exists
    if cls_path in db:
        doc = db[cls_path]
    else:
        doc = {"_id": cls_path}
    new_info = cls._info._asdict()

    # Only apply the update if changes have actually been made to the class
    if any(doc.get(k, None) != v for k,v in new_info.items()):
        doc.update(new_info)
        db.save(doc)

if __name__ == '__main__':
    server = Server()
    db = server[DbName.MODULE_TYPE.value]
    class_path = argv[1]
    package_path, class_name = class_path.split(":")
    package = import_module(package_path)
    class_to_register = getattr(package, class_name)
    register_module_type(class_to_register, db)

