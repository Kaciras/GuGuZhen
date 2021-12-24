import re
from dataclasses import dataclass

from lxml import etree

from .base import ReadType, FYGClient

_lvp = re.compile(r">(\d+)</span> (.+)")
_id_pkg = re.compile(r"(\d+)','Lv.(\d+) ([^']+)")
_xp = re.compile(r"fyg_colpz0(\d)bg")


@dataclass(eq=False, slots=True)
class Equipment:
	size: int  # 背包格子数
	backpacks: list  # 背包物品
	repository: list  # 仓库物品


@dataclass(eq=False, slots=True)
class Item:
	id: int
	grade: int
	level: int
	name: str


def _parse_equipments_slots(buttons):
	buttons = filter(lambda x: x.get("onclick"), buttons)
	return list(map(_parse_item_button, buttons))


def _parse_item_button(button):
	click = button.get("onclick")
	match = _xp.search(button.get("class"))
	grade = int(match.group(1))

	match = _id_pkg.search(click)
	if match:
		id_, level, name = match.groups()
		return Item(int(id_), grade, int(level), name)

	id_ = int(click[5:-1])
	match = _lvp.search(button.get("title"))
	level, name = match.groups()
	return Item(id_, grade, int(level), name)


class CharacterApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""我的战斗信息"""
		html = self.api.fyg_read(ReadType.Character)


	def get_repository(self):
		"""武器装备"""
		html = self.api.fyg_read(ReadType.Repository)
		html = etree.HTML(html)

		buttons = html.xpath("/html/body/div[1]/div/button")
		size = len(buttons)
		backpacks = _parse_equipments_slots(buttons)

		buttons = html.xpath("/html/body/div[2]/div/button")
		repository = _parse_equipments_slots(buttons)

		return Equipment(size, backpacks, repository)

	def get_cards(self):
		"""角色卡片列表"""

