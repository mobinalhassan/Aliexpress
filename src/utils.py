import os


ROOT = __file__


def get_full_path(*paths):
    root_dir = os.path.dirname(ROOT)
    full_path = os.path.join(root_dir, *paths)
    return full_path








