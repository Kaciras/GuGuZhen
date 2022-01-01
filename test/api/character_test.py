from guguzhen.api import GuGuZhen, Talent, Card


def test_get_info(fyg_server):
	fyg_server.mock_res("ReadCharacter.html")

	api = GuGuZhen({})
	info = api.character.get_info()

	assert info.weapon.level == 157

	fyg_server.verify_read(f="9")


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
	assert cards[0] == Card(1262789, 0, "艾", 350, 3, 0.03, False)

	fyg_server.verify_read(f="8")
