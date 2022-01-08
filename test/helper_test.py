import pytest

from guguzhen.api import Amulet, Grade, AmuletAttr, Equipment, EquipAttr
from guguzhen.helper import item_hash


def test_hash_incomplete_equip():
	a = Equipment(Grade.cyan, "幽梦匕首", 138, None, None)

	with pytest.raises(TypeError) as info:
		item_hash(a)

	assert str(info.value) == "装备对象不含属性，无法 Hash"


def test_amulet_hash():
	p1 = AmuletAttr("智力", 1)
	p2 = AmuletAttr("速度", 0.01)

	a = Amulet(Grade.cyan, "稀有苹果护身符", 1, (p1, p2))
	b = Amulet(Grade.cyan, "稀有苹果护身符", 1, (p1, p2))
	c = Amulet(Grade.cyan, "稀有苹果护身符", 1, ())

	h1, h2, h3 = item_hash(a), item_hash(b), item_hash(c)

	assert h1 != h3 and a != c
	assert a == b
	assert h1 == h2 == "gQMEexkj"


def test_equip_hash():
	p1 = EquipAttr("物理攻击", 1.23, 0.45)
	p2 = EquipAttr("附加理伤", 0.97, 1235)

	a = Equipment(Grade.black, "幽梦匕首", 138, (p1, p2), None)
	b = Equipment(Grade.black, "幽梦匕首", 138, (p1, p2), None)
	c = Equipment(Grade.black, "幽梦匕首", 138, (p1, p2), "foobar")

	h1, h2, h3 = item_hash(a), item_hash(b), item_hash(c)

	assert h1 != h3 and a != c
	assert a == b
	assert h1 == h2 == "EOrGZ-wJ"
