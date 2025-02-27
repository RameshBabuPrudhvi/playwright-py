# Playwright-Pytest

This project is an automated testing framework built using Python and Playwright. It is designed to run both **API** and **web** tests while integrating with **qTest** for test result reporting.
## Setup

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Features

- **Environment Configuration**  
  Easily switch between different environments (dev, qa, prod) using a configuration file.

- **Playwright Integration**  
  Utilize Playwright for browser automation, including launching browsers, creating new pages, and recording videos and screenshots.

- **qTest Integration**  
  Automatically upload test results to qTest, including creating test cycles, suites, and attaching HTML reports.

- **Logging**  
  Comprehensive logging using Python's built-in logging module to track test execution and result uploads.

- **Parameterized Tests**  
  Run tests with different parameters using pytest's `@pytest.mark.parametrize`.


## Project Structure

- **conftest.py**  
  Contains pytest configuration, fixtures, and hooks for setting up the test environment and reporting results.

- **utils/qtest_reporter.py**  
  Handles interactions with the qTest API for uploading test results.

- **tests/test_web.py**  
  Example test cases using Playwright to test web applications.

- **config/test_config.json**  
  Configuration file for different environments and qTest settings.

- **reports/**  
  Directory to store test reports, videos, and screenshots.

## Run Tests
Execute tests using pytest with the specified environment:

```bash 
pytest --env=dev
```
Execute tests using pytest with the specific tag:

```bash 
pytest --tags=smoke
```