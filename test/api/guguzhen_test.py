import pytest

from guguzhen.api import FygAPIError


def test_rest(api, fyg_server):
	"""这个似啥好测的，但为了覆盖率还是写一个了"""
	api.rest()
	assert fyg_server.httpx_mock.get_requests() == []


def test_get_version(api, fyg_server):
	fyg_server.mock_res("fyg_ulog.html")

	version = api.get_version()

	assert version == "2021/10/28"
	fyg_server.verify("/fyg_ulog.php")


def test_get_user(api, fyg_server):
	fyg_server.mock_res("ReadUser.html")

	user = api.get_user()

	assert user.name == "test"
	assert user.level == 166
	assert user.couch == 4810940
	assert user.sand == 57
	assert user.crystal == 0

	fyg_server.verify_read(f="13")


def test_drop_quagmire(api, fyg_server):
	fyg_server.mock_res("kf_drop_0.html", "gbk")
	fyg_server.mock_res("kf_drop_1.html", "gbk")

	api.drop_quagmire(50)

	_, second = fyg_server.httpx_mock.get_requests()
	assert second.url.query == b"r=50&sf=654321"


def test_drop_quagmire_failed(api, fyg_server):
	fyg_server.mock_res("kf_drop_0.html", "gbk")
	fyg_server.mock_res("kf_drop_2.html", "gbk")

	with pytest.raises(FygAPIError):
		api.drop_quagmire(50)

	_, second = fyg_server.httpx_mock.get_requests()
	assert second.url.query == b"r=50&sf=654321"
