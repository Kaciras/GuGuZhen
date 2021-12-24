from guguzhen.api import GuGuZhen, PKRank


def test_pillage(httpx_mock):
	with open("fixtures/ClickPillage.html", encoding="utf8") as fp:
		httpx_mock.add_response(html=fp.read())

	api = GuGuZhen({})
	api.safe_id = ""
	trophy = api.pk.pillage()

	assert trophy.value == 23713
	assert trophy.base == 18500
	assert trophy.range == (0.8, 1.2)


def test_get_pk_info(httpx_mock):
	with open("fixtures/ReadPK.html", encoding="utf8") as fp:
		httpx_mock.add_response(html=fp.read())

	api = GuGuZhen({})
	info = api.pk.get_info()

	assert info.rank == PKRank.AA
	assert info.power == 100
	assert info.progress == 98
	assert info.creepsEnhance == 2


def test_get_repository(httpx_mock):
	with open("fixtures/repository.html", encoding="utf8") as fp:
		httpx_mock.add_response(html=fp.read())

	api = GuGuZhen({})
	get_equipments(api)


def test_get_safeid(httpx_mock):
	with open("fixtures/index.html", encoding="utf8") as fp:
		httpx_mock.add_response(html=fp.read())

	api = GuGuZhen({})
	api.fetch_safeid()

	assert api.safe_id == "aaaaaa"


def test_get_gift_pool(httpx_mock):
	with open("fixtures/gift.html", encoding="utf8") as fp:
		httpx_mock.add_response(html=fp.read())

	api = GuGuZhen({})
	pool = api.get_gift_pool()

	assert pool.conch == 114514
	assert pool.sand == 24
	assert pool.equipment == 48
	assert pool.cards == 1
	assert pool.halo == 5.28


def test_get_gift_cards(httpx_mock):
	with open("fixtures/giftop.html", encoding="utf8") as fp:
		httpx_mock.add_response(html=fp.read())

	api = GuGuZhen({})
	opened = api.get_gift_cards()

	assert len(opened) == 1
	assert opened[0].type == "贝壳"
	assert opened[0].base == 32600
	assert opened[0].ratio == 250
