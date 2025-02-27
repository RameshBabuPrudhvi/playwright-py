import json
import logging
import os
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Playwright, APIRequestContext, sync_playwright

from utils.qtest_reporter import QTestReporter

logger = logging.getLogger(__name__)

CONFIG = {}

RESULTS = {}
REPORTER = None
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
REPORTS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "reports"))
CONFIG_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "config"))
# Ensure necessary directories exist
os.makedirs(f"{REPORTS_DIR}/videos", exist_ok=True)
os.makedirs(f"{REPORTS_DIR}/screenshots", exist_ok=True)


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="qa", help="Choose environment: dev, qa, prod")


def pytest_configure(config):
    """Load configuration before any test runs."""
    global CONFIG
    config_path = Path(CONFIG_DIR, "test_config.json").resolve()
    logger.info(f"Resolved config path: {config_path}")

    if not config_path.exists():
        logger.error(f"Configuration file not found at: {config_path}")
        CONFIG = {}
    else:
        with open(config_path, "r") as file:
            CONFIG = json.load(file)

    config._metadata = CONFIG  # Store config in pytest metadata (optional)


def pytest_sessionstart(session):
    global REPORTER

    qtest_config = CONFIG.get("qtest", {})
    if not qtest_config:
        logger.error("QTest configuration not found.")
        return

    if qtest_config.get("upload", False):
        logger.info("Initializing QTestReporter...")
        REPORTER = QTestReporter(qtest_config.get("url"),
                                 qtest_config.get("project_id"),
                                 qtest_config.get("module_id"),
                                 qtest_config.get("api_token"))
        logger.info("QTestReporter initialized successfully.")
        session.config._qtest_reporter = REPORTER


def pytest_runtest_setup(item):
    logger.info(f"[HOOK] Before Test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Store test results in RESULTS dictionary."""
    if "qtest_ids" not in item.funcargs or not item.funcargs["qtest_ids"]:
        return  # Skip teardown if no qTest marker

    qtest_ids = item.funcargs.get("qtest_ids", [])
    test_outcome = getattr(item, "rep_call", None)

    if not test_outcome:
        logger.error(f"No test outcome recorded for: {item.name}")
        return

    status_mapping = {
        "passed": "PASS",
        "failed": "FAIL",
        "skipped": "SKIP"
    }
    status = status_mapping.get(test_outcome.outcome, "SKIP")

    for qtest_id in qtest_ids:
        RESULTS[qtest_id] = status

    logger.info(f"Updated RESULTS: {RESULTS}")


def pytest_sessionfinish(session, exitstatus):
    """Report final test statuses to qTest with the exact HTML report."""
    qtest_config = CONFIG.get("qtest", {})
    if not qtest_config.get("upload", False):  # Skip if upload is False
        logger.info("QTest upload is disabled. Skipping result upload.")
        return
    report_path = os.path.join(REPORTS_DIR, "TestReport.html")
    reporter = getattr(session.config, "_qtest_reporter", None)
    if not reporter:
        logger.error("QTestReporter is not initialized.")
        return
    try:
        for qtest_id, status in RESULTS.items():
            reporter.upload_test_result(qtest_id, status, report_path)
            logger.info(f"Reported {qtest_id}: {status} with report: {report_path}")
    except Exception as e:
        logger.error(f"Error uploading test results to qTest: {e}")


def test_pytest_terminal_summary(self, mocker, tr_mock):
    logger.info("Test terminal summary")


@pytest.fixture(scope="session")
def config():
    """Fixture to access the loaded config in tests."""
    return CONFIG


@pytest.fixture(scope="session")
def env_config(pytestconfig):
    """Fixture to access environment-specific config in tests."""
    env = pytestconfig.getoption("--env")
    return CONFIG.get("environment", {}).get(env, {})


@pytest.fixture
def qtest_ids(request):
    """Extracts qTest IDs from markers."""
    marker = request.node.get_closest_marker("qtest")
    return marker.args[0] if marker else []


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
