import re
from dataclasses import dataclass

from lxml import etree

from guguzhen.api import ReadType

lvp = re.compile(r">(\d+)</span> (.+)")
id_pkg = re.compile(r"(\d+)','Lv.(\d+) ([^']+)")


@dataclass(eq=False, slots=True)
class Equipment:
	size: int  # 背包格子数
	backpacks: list  # 背包物品
	repository: list  # 仓库物品


@dataclass(eq=False, slots=True)
class Item:
	id: int
	level: int
	name: str


def get_equipments(api):
	html = api.fyg_read(ReadType.Repository)
	html = etree.HTML(html)

	buttons = html.xpath("/html/body/div[1]/div/button")
	size = len(buttons)
	backpacks = _parse_equipments_slots(buttons)

	buttons = html.xpath("/html/body/div[2]/div/button")
	repository = _parse_equipments_slots(buttons)

	return Equipment(size, backpacks, repository)


def _parse_equipments_slots(buttons):
	buttons = filter(lambda x: x.get("onclick"), buttons)
	return list(map(_parse_button, buttons))


def _parse_button(button):
	click = button.get("onclick")

	match = id_pkg.search(click)
	if match:
		id_, level, name = match.groups()
		return Item(int(id_), int(level), name)

	id_ = int(click[5:-1])
	match = lvp.search(button.get("title"))
	level, name = match.groups()
	return Item(id_, int(level), name)
