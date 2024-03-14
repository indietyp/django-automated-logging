import os
import sys
from pathlib import Path

import django
from coverage import coverage

from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = Path(BASE_DIR)

    sys.path.append(BASE_DIR.as_posix())
    os.chdir(BASE_DIR.as_posix())

    Coverage = coverage(config_file=".coveragerc")
    Coverage.start()

    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()

    TestRunner = get_runner(settings)

    test_runner = TestRunner()
    failures = test_runner.run_tests(["automated_logging"])

    if failures:
        sys.exit(1)

    Coverage.stop()

    print("Coverage Summary:")
    Coverage.report()

    location = BASE_DIR / "tmp" / "coverage"
    Coverage.html_report(directory=location.as_posix())
    print(f"HTML version: file://{location}/index.html")
