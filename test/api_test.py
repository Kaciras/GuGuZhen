from guguzhen.api import GuGuZhen


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
