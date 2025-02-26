from playwright.sync_api import APIRequestContext


def test_get_example(api_context: APIRequestContext) -> None:
    response = api_context.get("https://jsonplaceholder.typicode.com/posts/1")
    assert response.status == 200
    json_data = response.json()
    assert json_data["id"] == 1
    assert json_data["userId"] == 1
    assert "title" in json_data
    assert "body" in json_data


def test_post_example(api_context: APIRequestContext) -> None:
    headers = {"Content-type": "application/json"}
    data = {
        "title": "foo",
        "body": "bar",
        "userId": 1
    }
    post_todo = api_context.post(
        f"https://jsonplaceholder.typicode.com/posts", data=data, headers=headers
    )
    assert post_todo.json()["title"] == "foo"
