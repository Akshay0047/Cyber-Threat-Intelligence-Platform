import os
import sys
from pathlib import Path


def setup_django():
    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cti_project.settings")
    import django

    django.setup()
