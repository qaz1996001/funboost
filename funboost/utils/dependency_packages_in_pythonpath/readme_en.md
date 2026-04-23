## This Folder is Added to sys.path

The funboost `__init__.py` file adds this to sys.path on the first line, which is equivalent to exporting PYTHONPATH:

```python
from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath # This adds dependency_packages_in_pythonpath to PYTHONPATH.
```

This folder stores third-party packages or modified versions of third-party packages.

When importing funboost, this folder is automatically added to sys.path (PYTHONPATH).

## For Developers to Avoid PyCharm Wavy Line Warnings and Improve Auto-completion

Right-click on the `funboost/utils/dependency_packages_in_pythonpath` folder in PyCharm -> Mark Directory as -> Mark as Source Root.

This way, when importing, you can get automatic completion suggestions and be able to jump to the packages in this directory.

## 3 The Contents Here Have Been Deprecated

Funboost no longer uses the contents of this folder.
