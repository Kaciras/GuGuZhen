import pytest

from guguzhen.api import Talent, Card, FygAPIError


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
	assert cards[3] == Card(1462388, 0, "艾", 351, 3, 0.03, False)

	fyg_server.verify_read(f="8")
