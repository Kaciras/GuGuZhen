from pathlib import Path
from urllib.parse import parse_qsl

from pytest import fixture
from pytest_httpx import HTTPXMock

from guguzhen.api import GuGuZhen, PKRank, Card, Talent

_safe_id = "abc123"


class FYGServerMock:
	"""
	简单的 Mock 请求封装，让请求相关的准备和断言一行就能搞定。
	"""

	def __init__(self, httpx_mock: HTTPXMock):
		self.httpx_mock = httpx_mock

	def mock_res(self, res_file):
		html = Path("fixtures", res_file).read_text("utf8")
		self.httpx_mock.add_response(html=html)

	def verify(self, path, method="GET", **kwargs):
		request = self.httpx_mock.get_request()
		form = request.content.decode()

		assert request.method == method
		assert request.url.path == path
		assert parse_qsl(form) == list(kwargs.items())

	def verify_read(self, **kwargs):
		self.verify("/fyg_read.php", "POST", **kwargs)

	def verify_click(self, **kwargs):
		kwargs["safeid"] = _safe_id
		self.verify("/fyg_click.php", "POST", **kwargs)


@fixture
def fyg_server(httpx_mock):
	return FYGServerMock(httpx_mock)


def test_get_character_info(fyg_server):
	fyg_server.mock_res("ReadCharacter.html")

	api = GuGuZhen({})
	info = api.character.get_info()

	assert info.weapon.level == 157

	fyg_server.verify_read(f="9")


def test_pillage(fyg_server):
	fyg_server.mock_res("ClickPillage.html")

	api = GuGuZhen({})
	api.safe_id = _safe_id
	trophy = api.pk.pillage()

	fyg_server.verify_click(c="16")

	assert trophy.value == 23713
	assert trophy.base == 18500
	assert trophy.range == (0.8, 1.2)


def test_get_beach(fyg_server):
	fyg_server.mock_res("ReadBeach.html")

	api = GuGuZhen({})
	items = api.beach.get_items()

	fyg_server.verify_read(f="1")

	assert len(items) == 11


def test_get_talent(fyg_server):
	fyg_server.mock_res("ReadTalent.html")

	api = GuGuZhen({})
	info = api.character.get_talent()

	assert info.halo == 167.89
	assert info.talent == (Talent.启程之风, Talent.点到为止, Talent.飓风之力)

	fyg_server.verify_read(f="5")


def test_get_cards(fyg_server):
	fyg_server.mock_res("ReadCards.html")

	api = GuGuZhen({})
	cards = api.character.get_cards()

	assert len(cards) == 5
	assert cards[0] == Card(1262789, 0, "艾", 350, 3, 3, False)

	fyg_server.verify_read(f="8")


def test_get_pk_info(fyg_server):
	fyg_server.mock_res("ReadPK.html")

	api = GuGuZhen({})
	info = api.pk.get_info()

	fyg_server.verify_read(f="12")

	assert info.rank == PKRank.AA
	assert info.power == 100
	assert info.progress == 98
	assert info.strengthen == 2


def test_get_repository(fyg_server):
	fyg_server.mock_res("ReadRepository.html")

	api = GuGuZhen({})
	repo = api.items.get_repository()

	assert repo.size == 11

	fyg_server.verify_read(f="7")


def test_get_safeid(fyg_server):
	fyg_server.mock_res("index.html")

	api = GuGuZhen({})
	api.fetch_safeid()

	assert api.safe_id == "aaaaaa"

	fyg_server.verify("/fyg_index.php")


def test_get_gift_pool(fyg_server):
	fyg_server.mock_res("fyg_gift.html")

	api = GuGuZhen({})
	pool = api.gift.get_pool()

	assert pool.conch == 114514
	assert pool.sand == 24
	assert pool.equipment == 48
	assert pool.cards == 1
	assert pool.halo == 5.28

	fyg_server.verify("/fyg_gift.html")


def test_get_gifts(fyg_server):
	fyg_server.mock_res("giftop.html")

	api = GuGuZhen({})
	opened = api.gift.get_gifts()

	assert len(opened) == 1
	assert opened[0].type == "贝壳"
	assert opened[0].base == 32600
	assert opened[0].ratio == 250

	fyg_server.verify_read(f="10")
