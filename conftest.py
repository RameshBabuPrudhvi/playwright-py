# python
import json
import os
from typing import Generator

import pytest
from playwright.sync_api import sync_playwright, APIRequestContext, Playwright

from utils.qtest_reporter import QTestReporter

# Get the absolute path of the project root
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Gets current directory
REPORTS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "reports"))  # Store outside 'tests'

# Ensure necessary directories exist
os.makedirs(f"{REPORTS_DIR}/videos", exist_ok=True)
os.makedirs(f"{REPORTS_DIR}/screenshots", exist_ok=True)


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="qa", help="Choose environment: dev, qa, prod")


@pytest.fixture(scope="session")
def config(pytestconfig):
    env = pytestconfig.getoption("env")  # Get environment from CLI or default
    with open("../config/test_config.json", "r") as f:
        configs = json.load(f)

    if env not in configs:
        raise ValueError(f"Environment '{env}' not found in test_config.json")

    return configs[env]


@pytest.fixture(scope='session')
def browser():
    """Launches a Playwright browser instance for the session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope='function')
def api_context(
        playwright: Playwright,
) -> Generator[APIRequestContext, None, None]:
    """Provides a new API request context for each test function."""
    request_context = playwright.request.new_context()
    yield request_context
    request_context.dispose()


@pytest.fixture(scope='function')
def page(browser, request):
    """Creates a new page for each test to maintain isolation."""
    video_path = os.path.join(REPORTS_DIR, "videos")  # Store videos outside 'tests'
    os.makedirs(video_path, exist_ok=True)

    context = browser.new_context(
        record_video_dir=video_path,
        record_video_size={"width": 1280, "height": 720}
    )

    page = context.new_page()
    yield page

    screenshot_path = os.path.join(REPORTS_DIR, "screenshots", f"{page.title()}.png")
    page.screenshot(path=screenshot_path)

    page.close()
    context.close()


@pytest.fixture
def qtest_ids(request):
    """Extracts qTest IDs from markers."""
    marker = request.node.get_closest_marker("qtest")
    return marker.args[0] if marker else []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item):
    """Runs after each test to upload results to qTest."""
    yield  # Run the test first

    # Check if the test has the 'qtest' marker
    if "qtest_ids" not in item.funcargs or not item.funcargs["qtest_ids"]:
        return  # Skip teardown if no qTest marker

    qtest_ids = item.funcargs.get("qtest_ids", [])
    test_outcome = item.rep_call.outcome

    status_mapping = {
        "passed": "PASS",
        "failed": "FAIL",
        "skipped": "SKIP"
    }
    status = status_mapping.get(test_outcome, "SKIP")

    html_file_path = os.path.join(REPORTS_DIR, "TestReport.html")

    base_url = "https://apitryout.qtestnet.com/api/v3"
    project_id = "101762"
    module_id = "10116193"
    api_token = "9bbf04fd-aed2-4e05-8428-7fc5ecff7bb8"

    reporter = QTestReporter(base_url, project_id, module_id, api_token)
    reporter.upload_multi_test_results(qtest_ids, status, html_file_path)
