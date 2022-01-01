from guguzhen.api import PKRank


def test_get_pk_info(api, fyg_server):
	fyg_server.mock_res("ReadPK.html")

	info = api.pk.get_info()

	fyg_server.verify_read(f="12")

	assert info.rank == PKRank.AA
	assert info.power == 100
	assert info.progress == 98
	assert info.strengthen == 2


def test_vs_creep(api, fyg_server):
	fyg_server.mock_res("VIntel.html")

	fighting = api.pk.fight_creep()


def test_pillage(api, fyg_server):
	fyg_server.mock_res("ClickPillage.html")

	trophy = api.pk.pillage()

	fyg_server.verify_click(c="16")

	assert trophy.value == 23713
	assert trophy.base == 18500
	assert trophy.range == (0.8, 1.2)

