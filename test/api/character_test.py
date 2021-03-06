import pytest

from guguzhen.api import Talent, Card, FygAPIError, Properties


class TestCard:

	def test_levelup_cost_0(self):
		card = Card(114514, 0, "命", 342, 3, 0.03, False)

		assert card.level_up_cost(1) == 9
		assert card.level_up_cost(10) == 999
		assert card.level_up_cost(342) == 1169639

	def test_levelup_cost_1(self):
		card = Card(114514, 12, "薇", 349, 4, 0.01, False)

		assert card.level_up_cost(13) == 250
		assert card.level_up_cost(22) == 3400
		assert card.level_up_cost(349) == 1216570

	def test_gp(self):
		card = Card(114514, 336, "梦", 336, 3, 0.06, True)
		assert card.gp == 1074
		assert card.gp_max == 1074

	def test_gp_free(self):
		props = Properties(1, 17, 1, 18, 1, 1)
		card = Card(114514, 12, "梦", 349, 4, 0.01, False, props)

		assert card.gp == 42
		assert card.gp_free == 3

	def test_str(self):
		card = Card(114514, 336, "梦", 336, 3, 0.06, True)
		assert str(card) == "114514 Lv.336/336 梦 3技能位 6%品质 [使用中]"


def test_talent_cost():
	assert Talent.飓风之力.cost == 100
	assert Talent.破魔之心.cost == 30
	assert Talent.启程之风.cost == 10
	assert Talent.点到为止.cost == 50


def test_get_current(api, fyg_server):
	fyg_server.mock_res("ReadCardDetail.html")

	card = api.character.get_current_card()
	assert card.id == 1436389
	assert card.in_use
	assert card.props == Properties(1, 350, 300, 1, 421, 1)

	fyg_server.verify_read(f="18", zid="mi")


def test_get_info(api, fyg_server):
	fyg_server.mock_res("ReadCharacter.html")

	info = api.character.get_info()

	assert info.weapon.level == 157

	fyg_server.verify_read(f="9")


def test_get_talent(api, fyg_server):
	fyg_server.mock_res("ReadTalent.html")

	info = api.character.get_talent()

	assert info.halo == 167.89
	assert info.talent == (Talent.启程之风, Talent.点到为止, Talent.飓风之力)

	fyg_server.verify_read(f="5")


def test_insufficient_slots(api, fyg_server):
	c = "你当前装备的卡片拥有 [ 3 ] 个天赋技能位<br>你只可以选择最多 [ 3 ] 个天赋技能"
	fyg_server.mock_res(content=c)

	with pytest.raises(FygAPIError):
		api.character.set_talent([Talent.飓风之力, Talent.破魔之心])

	fyg_server.verify_click(c="4", arr="403,202")


def test_insufficient_halo(api, fyg_server):
	c = "所选天赋技能需要 [ 300 ] 天赋点<br>你拥有 [ 168 ] 天赋点"
	fyg_server.mock_res(content=c)

	with pytest.raises(FygAPIError):
		api.character.set_talent([Talent.飓风之力, Talent.破魔之心])

	fyg_server.verify_click(c="4", arr="403,202")


def test_get_cards(api, fyg_server):
	fyg_server.mock_res("ReadCards.html")

	cards = api.character.get_cards()

	assert len(cards) == 7
	fyg_server.verify_read(f="8")

	assert cards[3].id == 1462388
	assert cards[3].level == 0
	assert cards[3].role == "艾"
	assert cards[3].lv_max == 351
	assert cards[3].skills == 3
	assert cards[3].quality == 0.03
	assert cards[3].in_use == False
	assert cards[3].props is None


def test_delete_card(api, fyg_server):
	fyg_server.mock_res(content="该卡片已删除，被删除卡片的50%经验(5000)已给予当前装备的卡片。")
	api.character.delete_card(1455897)
	fyg_server.verify_click(c="11", id="1455897")
