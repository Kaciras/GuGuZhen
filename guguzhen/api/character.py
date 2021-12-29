import re
from dataclasses import dataclass
from enum import Enum

from lxml import etree

from .base import ReadType, FYGClient, Role, ClickType
from .items import Equipment

_card_attrs_re = re.compile(r"(\d+) 最大等级<br/>(\d+) 技能位<br/>(\d+)% 品质")


class Halo(Enum):
	"""
	所有的光环天赋，值是对应的 ID，名字懒得翻译成英文了。
	虽然值可以解析为整数，但对其做运算无意义，所以用 str 而不是 int。
	"""

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


@dataclass(eq=False)
class EquipConfig:
	weapon: Equipment	 	 # 武器
	bracelet: Equipment	 	 # 手部
	armor: Equipment		 # 衣服
	accessory: Equipment	 # 发饰


@dataclass(frozen=True, slots=True)
class Card:
	id: int			# 卡片 ID
	level: int		# 等级
	role: Role		# 类型
	lv_max: int		# 最大等级
	skills: int		# 技能位
	quality: int    # 品质
	in_use: bool    # 使用中？

	def __str__(self):
		parts = [
			str(self.id),
			f"Lv.{self.level}/{self.lv_max}",
			str(self.role),
			f"{self.skills}技能位",
			f"{self.quality}%品质"
		]

		if self.in_use:
			parts.append("[使用中]")

		return " ".join(parts)


class CharacterApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""我的战斗信息"""
		html = self.api.fyg_read(ReadType.Character)

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
			raise Exception("失败：" + text)

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
			in_use = attrs.find("当前使用中") > 0

			cards.append(Card(id_, level, role, lv_max, skills, quality, in_use))

		return cards
