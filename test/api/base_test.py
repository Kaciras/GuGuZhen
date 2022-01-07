import pytest

from guguzhen.api import FygAPIError


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
