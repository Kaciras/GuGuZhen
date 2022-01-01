from guguzhen.api import GuGuZhen

def test_get_gift_pool(fyg_server):
	fyg_server.mock_res("fyg_gift.html")

	api = GuGuZhen({})
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


def test_get_gifts(fyg_server):
	fyg_server.mock_res("giftop.html")

	api = GuGuZhen({})
	opened = api.gift.get_gifts()

	assert len(opened) == 1
	assert opened[0].type == "贝壳"
	assert opened[0].base == 32600
	assert opened[0].ratio == 250

	fyg_server.verify_read(f="10")
