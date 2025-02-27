import base64
import os
import logging
from datetime import datetime, timezone

import requests


class QTestReporter:
    """Handles interaction with the qTest API for test result uploads."""

    def __init__(self, base_url, project_id, module_id, api_token):
        self.base_url = base_url
        self.project_id = project_id
        self.module_id = module_id
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        today = datetime.now(timezone.utc).strftime("%b-%d-%Y %H:%M:%S")

        # Initialize cycle and suite only once
        self.cycle_id = self.create_test_cycle(f"Automated Test Cycle {today}")
        self.logger.info(f"Created Test Cycle ID: {self.cycle_id}")
        self.suite_id = self.create_test_suite(self.cycle_id, f"Automated Test Suite {today}")
        self.logger.info(f"Created Test Suite ID: {self.suite_id}")

    @staticmethod
    def encode_file_to_base64(file_path):
        """Encodes the content of an HTML file to a base64 string."""
        with open(file_path, "rb") as file:
            encoded_html = base64.b64encode(file.read()).decode("utf-8")
        return encoded_html

    def get_test_case_details(self, test_case_pid):
        """Fetches the test case name and numerical ID using qTest ID with pagination."""
        page = 1
        size = 50
        while True:
            url = (
                f"{self.base_url}/projects/{self.project_id}/test-cases?"
                f"parentId={self.module_id}&page={page}&size={size}&expandProps=true"
            )
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            test_cases = response.json()
            if not test_cases:
                break  # No more test cases

            for test_case in test_cases:
                if test_case.get("pid") == test_case_pid:
                    return {"id": test_case.get("id"), "name": test_case.get("name")}

            page += 1

        return None

    def create_test_cycle(self, cycle_name):
        """Creates a new test cycle in qTest."""
        url = f"{self.base_url}/projects/{self.project_id}/test-cycles"
        payload = {"name": cycle_name, "description": "Automated test cycle", "status": "In Progress"}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json().get("id")

    def create_test_suite(self, cycle_id, suite_name):
        """Creates a test suite inside a given test cycle."""
        url = f"{self.base_url}/projects/{self.project_id}/test-suites?parentId={cycle_id}&parentType=test-cycle"
        payload = {"name": suite_name, "description": "Automated test suite"}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json().get("id")

    def add_test_case_to_suite(self, suite_id, qtest_id, test_case_id, test_case_name):
        """Adds a test case to the test suite."""
        url = f"{self.base_url}/projects/{self.project_id}/test-runs?parentId={suite_id}&parentType=test-suite"

        payload = {
            "name": f"{qtest_id}-{test_case_name}",
            "test_case": {
                "id": test_case_id
            }
        }
        response = requests.request("POST", url, headers=self.headers, json=payload)

        response.raise_for_status()

        return response.json().get("id")

    def upload_multi_test_results(self, qtest_ids, status, report_path):
        """Uploads results for multiple qTest IDs."""
        for qtest_id in qtest_ids:
            self.logger.info(f"Uploading Results for qTest ID: {qtest_id}")
            self.upload_test_result(qtest_id, status, report_path)

    def upload_test_result(self, qtest_id, status, report_path):
        """Uploads test results to qTest by creating a test run and attaching the report."""
        test_case_details = self.get_test_case_details(qtest_id)

        if test_case_details:
            test_case_id = test_case_details["id"]
            test_case_name = test_case_details["name"]
        else:
            test_case_id = None
            test_case_name = None

        assert test_case_id, f"Test Case ID not found for {qtest_id}"

        test_run_id = self.add_test_case_to_suite(self.suite_id, qtest_id, test_case_id, test_case_name)
        self.logger.info(f"Added Test Case {qtest_id} to Suite ID: {self.suite_id}")
        self.logger.info(f"Created Test Run ID: {test_run_id}")

        self.update_test_run_results(qtest_id, test_run_id, status, report_path)

    def update_test_run_results(self, qtest_id, test_run_id, status, report_path):
        url = f"{self.base_url}/projects/{self.project_id}/test-runs/{test_run_id}/auto-test-logs"

        exe_start_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        exe_end_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        encoded_html = self.encode_file_to_base64(report_path)
        payload = {
            "name": f"Test Run {qtest_id}",
            "status": status,
            "exe_start_date": exe_start_date,
            "exe_end_date": exe_end_date,
            "attachments": [
                {
                    "name": os.path.basename(report_path),
                    "content_type": "text/html",
                    "data": encoded_html
                }
            ]
        }

        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            self.logger.info(f"Successfully uploaded results for qTest ID: {qtest_id}")
        else:
            self.logger.error(f"Failed to upload results for qTest ID: {qtest_id} - {response.text}")
