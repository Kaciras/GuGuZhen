import pytest

from guguzhen.api import LimitReachedError, Gift


def test_gift_to_str():
	assert str(Gift("贝壳", 36200, 3.36)) == "贝壳+36200*336%"


def test_get_pool(api, fyg_server):
	fyg_server.mock_res("fyg_gift.html")

	pool, base = api.gift.get_pool()

	assert pool["贝壳"] == 114514
	assert pool["星沙"] == 24
	assert pool["装备"] == 48
	assert pool["卡片"] == 1
	assert pool["光环"] == 5.28

	assert base["贝壳"] == 32800
	assert base["星沙"] == 4
	assert base["装备"] == 5
	assert base["卡片"] == 1
	assert base["光环"] == 1.2

	fyg_server.verify("/fyg_gift.php")


def test_get_gifts(api, fyg_server):
	fyg_server.mock_res("ReadGifts.html")

	opened = api.gift.get_opened()

	assert len(opened) == 1
	assert opened[0].type == "贝壳"
	assert opened[0].base == 32600
	assert opened[0].ratio == 2.5

	fyg_server.verify_read(f="10")


def test_open(api, fyg_server):
	fyg_server.mock_res(content="恭喜你！获得 87966贝壳！")

	api.gift.open(1, True)

	fyg_server.verify_click(c="8", id="1", gx="1")


def test_open_limited(api, fyg_server):
	fyg_server.mock_res("ClickOpenGift_1.html")

	with pytest.raises(LimitReachedError):
		api.gift.open(4)

	fyg_server.verify_click(c="8", id="4")
