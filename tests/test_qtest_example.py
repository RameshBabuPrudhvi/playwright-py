import pytest


@pytest.mark.tags(["smoke", "regression"])
@pytest.mark.qtest(["TC-9984", "TC-9985"])
def test_example_one(qtest_ids):
    print(f"\nTest mapped to qTest IDs: {qtest_ids}")
    assert True


@pytest.mark.tags(["regression"])
@pytest.mark.qtest(["TC-9986"])
def test_example_two(qtest_ids):
    print(f"\nTest mapped to qTest IDs: {qtest_ids}")
    assert False
