import pytest

from guguzhen.api import RandomCard, Equipment, Grade, EquipAttr, LimitReachedError, FygAPIError


def test_next_time(api, fyg_server):
	fyg_server.mock_res("fyg_beach.html")

	duration = api.beach.get_next_time()

	assert str(duration) == "21:50:00"
	fyg_server.verify("/fyg_beach.php")


def test_pick_not_exists(api, fyg_server):
	"""
	服务端对于不存在的物品都认为是卡片……
	"""
	fyg_server.mock_res(content="卡片不存在。")

	with pytest.raises(FygAPIError):
		api.beach.pick(8964)


def test_pick_card(api, fyg_server):
	fyg_server.mock_res(content="新的卡片已放入你的卡片栏，请查看。ok")
	api.beach.pick(8964)
	fyg_server.verify_click(c="1", id="8964")


def test_pick_card_full(api, fyg_server):
	fyg_server.mock_res(content="卡片栏已满，请先清理无用卡片。")
	with pytest.raises(LimitReachedError):
		api.beach.pick(8964)


def test_pick_equip_full(api, fyg_server):
	fyg_server.mock_res(content="背包已满。无法放入新装备。")
	with pytest.raises(LimitReachedError):
		api.beach.pick(8964)


def test_get_beach(api, fyg_server):
	fyg_server.mock_res("ReadBeach.html")

	items = api.beach.get_items()

	assert len(items) == 11
	assert items[0] == (46945022, RandomCard)

	attrs = (
		EquipAttr("附加生命", 1.18, 678),
		EquipAttr("物理减伤", 1.05, 48),
		EquipAttr("魔法减伤", 1.0, 46),
		EquipAttr("附加回血", 0.96, 132),
	)
	v = Equipment(Grade.green, "探险者布甲", 23, attrs, None)
	assert items[2] == (46945012, v)

	fyg_server.verify_read(f="1")


def test_clear(api, fyg_server):
	fyg_server.mock_res("ClickClearBeach.html")
	api.beach.clear()
	fyg_server.verify_click(c="20")


def test_throw_not_exists(api, fyg_server):
	fyg_server.mock_res(content="只能丢弃背包里的装备")

	with pytest.raises(FygAPIError):
		api.beach.throw(666)

	fyg_server.verify_click(c="7", id="666")
