from guguzhen.api import PKRank, VS, Creep, Equipment, Grade


def test_get_info(api, fyg_server):
	fyg_server.mock_res("ReadPK.html")

	info = api.pk.get_info()

	fyg_server.verify_read(f="12")

	assert info.rank == PKRank.AA
	assert info.power == 100
	assert info.progress == 98
	assert info.strengthen == 2


def test_vs_creep(api, fyg_server):
	fyg_server.mock_res("VIntel_0.html")

	battle = api.pk.battle(VS.Creep)

	assert battle.enemy == Creep("憨憨的食铁兽", 285, 1.32)
	assert battle.is_win
	assert len(battle.actions) == 5

	fyg_server.verify("/fyg_v_intel.php", "POST", id="1", safeid=api.safe_id)


def test_vs_player(api, fyg_server):
	fyg_server.mock_res("VIntel_1.html")

	battle = api.pk.battle(VS.Player)

	assert battle.enemy.name == "兩儀式"
	assert battle.enemy.role == "梦"
	assert battle.enemy.leval == 326
	assert len(battle.actions) == 10

	equips = battle.enemy.equipment
	assert equips.armor == Equipment(Grade.orange, "旅法师的灵光袍", 97, None, None)
	assert equips.accessory == Equipment(Grade.cyan, "占星师的发饰", 146, None, None)

	left, _ = battle.actions[9]
	assert left.is_attack == True
	assert left.state == ["暴击", "飓风之力", "星芒 15", "点到为止"]
	assert left.HP == 1559
	assert left.ES == 64194
	assert left.AD == 108
	assert left.AP == 133212
	assert left.TD == 5021
	assert left.ES_health == 313

	assert left.ES_lose is None
	assert left.HP_lose is None
	assert left.HP_health is None

	fyg_server.verify("/fyg_v_intel.php", "POST", id="2", safeid=api.safe_id)


def test_pillage(api, fyg_server):
	fyg_server.mock_res("ClickPillage.html")

	trophy = api.pk.pillage()

	fyg_server.verify_click(c="16")

	assert trophy.value == 23713
	assert trophy.base == 18500
	assert trophy.range == (0.8, 1.2)
