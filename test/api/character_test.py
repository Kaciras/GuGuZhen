from guguzhen.api import Talent, Card


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


def test_get_cards(api, fyg_server):
	fyg_server.mock_res("ReadCards.html")

	cards = api.character.get_cards()

	assert len(cards) == 7
	assert cards[3] == Card(1462388, 0, "艾", 351, 3, 0.03, False)

	fyg_server.verify_read(f="8")
