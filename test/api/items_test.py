import pytest

from guguzhen.api import FygAPIError


def test_get_info(api, fyg_server):
	fyg_server.mock_res("ReadEquipments.html")

	repo = api.items.get_info()

	assert repo.size == 11

	fyg_server.verify_read(f="7")


def test_put_out(api, fyg_server):
	fyg_server.mock_res(content="ok")
	api.items.put_out(1234567)
	fyg_server.verify_click(c="22", id="1234567")


def test_destroy(api, fyg_server):
	fyg_server.mock_res(content="至少需要“稀有”级别的装备才可以熔炼。")

	with pytest.raises(FygAPIError):
		api.items.destroy(4444888)

	fyg_server.verify_click(c="9", id="4444888", yz="124")
