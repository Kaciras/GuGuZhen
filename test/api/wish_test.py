from datetime import datetime


def test_get_info(api, fyg_server):
	fyg_server.mock_res("ReadWish.html")

	info = api.wishing.get_info()

	assert info.point == 10
	assert info.cost == 1968300
	assert info.expiration == datetime(2021, 12, 26, 11, 36, 13)
	assert info.buffers.强化背包 == 6
	assert info.buffers.战斗用生命药水 == 4

	fyg_server.verify_read(f="19")


def test_refresh(api, fyg_server):
	fyg_server.mock_res(content="许愿池已经重置排列。")
	api.wishing.shuffle()
	fyg_server.verify_click(c="19")
