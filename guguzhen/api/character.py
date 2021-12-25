import re
from dataclasses import dataclass
from enum import Enum

from lxml import etree

from .base import ReadType, FYGClient, Role, ClickType

_lvp = re.compile(r">(\d+)</span> (.+)")
_id_pkg = re.compile(r"(\d+)','Lv.(\d+) ([^']+)")
_xp = re.compile(r"fyg_colpz0(\d)bg")

_card_attrs_re = re.compile(r"(\d+) 最大等级<br/>(\d+) 技能位<br/>(\d+)% 品质")


class Halo(Enum):
	启程之誓 = "101"
	启程之心 = "102"
	启程之风 = "103"

	破壁之心 = "201"
	破魔之心 = "202"
	复合护盾 = "203"
	鲜血渴望 = "204"
	削骨之痛 = "205"

	伤口恶化 = "301"
	精神创伤 = "302"
	铁甲尖刺 = "303"
	忍无可忍 = "304"
	热血战魂 = "305"
	点到为止 = "306"

	沸血之志 = "401"
	波澜不惊 = "402"
	飓风之力 = "403"
	红蓝双刺 = "404"
	荧光护盾 = "405"
	后发制人 = "406"


@dataclass(eq=False, slots=True)
class ItemsInfo:
	size: int			# 背包格子数
	backpacks: list		# 背包物品
	repository: list	# 仓库物品


@dataclass(eq=False, slots=True)
class Item:
	id: int		 # 物品的 ID
	grade: int	 # 装备品质
	level: int	 # 装备等级
	name: str	 # 物品名


@dataclass(eq=False, slots=True)
class Equipment:
	weapon: Item	 # 武器
	bracelet: Item	 # 手部
	armor: Item		 # 衣服
	accessory: Item	 # 发饰


@dataclass(eq=False, slots=True)
class Card:
	id: int			# 卡片 ID
	level: int		# 等级
	role: Role		# 类型
	lv_max: int		# 最大等级
	skills: int		# 技能位
	quality: int    # 品质


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

		return ItemsInfo(size, backpacks, repository)

	def switch_card(self, card):
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.SwitchCard, id=card)
		if text != "ok":
			raise Exception("换卡失败：" + text)

	def set_halo(self, values):
		arr = ",".join(map(lambda x: x.value, values))
		text = self.api.fyg_click(ClickType.SetHalo, arr=arr)
		if text != "ok":
			raise Exception("换卡失败：" + text)

	def get_cards(self):
		"""角色卡片列表"""
		html = self.api.fyg_read(ReadType.CardList)
		html = etree.HTML(html)

		cards = []
		for div in html.xpath("/html/body/div"):
			id_ = int(div.get("onclick")[7:-1])
			level = int(div.xpath("div[1]/div[1]/span")[0].text)
			role = div.xpath("div[1]/div[3]")[0].text.strip()

			attrs = etree.tostring(div.xpath("div[2]")[0], encoding="unicode")
			match = _card_attrs_re.search(attrs)
			lv_max = int(match.group(1))
			skills = int(match.group(2))
			quality = int(match.group(3))

			cards.append(Card(id_, level, role, lv_max, skills, quality))

		return cards
