import pytest


@pytest.mark.tags(["smoke", "regression"])
@pytest.mark.qtest(["TC-9984", "TC-9985"])
def test_example(qtest_ids):
    print(f"\nTest mapped to qTest IDs: {qtest_ids}")
    assert True


def test_env_config(config):
    """Test configuration loading."""
    qtest_config = config.get("qtest", {})
    url = qtest_config.get("url")

    print(f"\nBase URL: {url}")

    assert url is not None, "qTest URL should not be None!"

