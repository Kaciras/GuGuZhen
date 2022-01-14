import pytest

from guguzhen.api import FygAPIError


def test_get_safeid(api, fyg_server):
	fyg_server.mock_res("index.html")

	api.connect()

	assert api.safe_id == "aaaaaa"
	fyg_server.verify("/fyg_index.php")


def test_login_user_not_exists(api, fyg_server):
	fyg_server.mock_res("login_1.html", enc="gbk")

	with pytest.raises(FygAPIError):
		api.login("alice", "foobar123")


def test_login(api, fyg_server):
	fyg_server.mock_res("login_0.html", enc="gbk")

	api.login("alice", "foobar123")

	request = fyg_server.httpx_mock.get_request()
	assert request.method == "POST"
	assert request.url == "https://bbs.9shenmi.com/login.php"
