import re
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, Optional

from lxml import etree

from .base import ReadType, FYGClient, Role, ClickType

_lvp = re.compile(r">(\d+)</span> (.+)")
_id_with_label = re.compile(r"(\d+)','Lv.\d+ ([^']+)")
_color_class = re.compile(r"fyg_colpz0(\d)bg")
_amulet_content = re.compile(r"\+(\d+) ([点%])")

_card_attrs_re = re.compile(r"(\d+) 最大等级<br/>(\d+) 技能位<br/>(\d+)% 品质")
_fc_re = re.compile(r"获得(\d+)水果核")


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


# 随机卡片没属性，直接用个对象来标识
RandomCard = object()


class Grade(IntEnum):
	"""物品的品质（背景颜色）"""

	black = 1
	cyan = 2
	green = 3
	orange = 4
	red = 5


@dataclass(frozen=True, slots=True)
class EquipAttr:
	type: str   	# 属性名
	ratio: int  	# 倍率
	value: int  	# 属性值

	def __str__(self):
		return f"[{self.ratio}%] {self.type} {self.value}"


@dataclass(frozen=True, slots=True)
class AmuletAttr:
	type: str		# 增加的属性
	value: int		# 增加量
	unit: str		# 单位，点或%

	def __str__(self):
		return f"[{self.type} +{self.value}{self.unit}]"


@dataclass(frozen=True, slots=True)
class Amulet:
	grade: Grade			  # 品质
	name: str		 		  # 名字
	enhancement: int		  # 强化次数
	attrs: tuple[AmuletAttr]  # 属性列表


@dataclass(frozen=True, slots=True)
class Equipment:
	grade: Grade			 # 装备品质
	name: str				 # 物品名
	level: int				 # 装备等级
	attrs: tuple[EquipAttr]  # 属性列表
	mystery: Optional[str]   # 神秘属性文本


Item = Amulet | Equipment


@dataclass(eq=False)
class ItemsInfo:
	size: int					 # 背包格子数
	backpacks: Dict[int, Item]	 # 背包物品
	repository: Dict[int, Item]  # 仓库物品


@dataclass(eq=False)
class EquipConfig:
	weapon: Item	 # 武器
	bracelet: Item	 # 手部
	armor: Item		 # 衣服
	accessory: Item	 # 发饰


@dataclass(frozen=True, slots=True)
class Card:
	id: int			# 卡片 ID
	level: int		# 等级
	role: Role		# 类型
	lv_max: int		# 最大等级
	skills: int		# 技能位
	quality: int    # 品质
	in_use: bool    # 使用中？


def _parse_equipments_slots(buttons):
	buttons = filter(lambda x: x.get("onclick"), buttons)
	return dict(map(parse_item_button, buttons))


def parse_item_button(button):
	onclick, title = button.get("onclick"), button.get("title")

	# 随机卡片标题为空
	if not title:
		return _get_id(onclick), RandomCard

	match = _color_class.search(button.get("class"))
	grade = Grade(int(match.group(1)))
	entries = etree.HTML(button.get("data-content")).xpath("/html/body/p")

	# 护身符的 onclick 是两个参数。
	match = _id_with_label.search(onclick)
	if match:
		enhance = int(button.getchildren()[0].tail)
		attrs = tuple(map(_parse_amulet_attr, entries))
		id_, name = match.groups()

		return int(id_), Amulet(grade, name, enhance, attrs)

	# 剩下的情况就是装备。
	attrs = tuple(map(_parse_equip_attr, entries[:4]))
	mystery = entries[4].text if len(entries) > 4 else None

	id_ = _get_id(onclick)
	level, name = _lvp.search(title).groups()

	return id_, Equipment(grade, name, int(level), attrs, mystery)


def _parse_amulet_attr(paragraph: etree.ElementBase):
	span = paragraph.getchildren()[0]
	v, u = _amulet_content.match(span.text).groups()
	return AmuletAttr(paragraph.text, int(v), u)


def _parse_equip_attr(paragraph: etree.ElementBase):
	label, text = paragraph.iterchildren()

	ratio = int(label.text[:-1])
	type_, value = text.text.split(" ")

	return EquipAttr(type_, ratio, int(value[:-1]), )


# zbtip(id)、stpick(id) 或者 puto(id)
def _get_id(onclick):
	i = onclick.index("(") + 1
	return int(onclick[i:-1])


class CharacterApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""我的战斗信息"""
		html = self.api.fyg_read(ReadType.Character)

	def get_repository(self):
		"""获取所有的武器装备"""
		html = self.api.fyg_read(ReadType.Repository)
		html = etree.HTML(html)

		buttons = html.xpath("/html/body/div[1]/div/button")
		size = len(buttons)
		backpacks = _parse_equipments_slots(buttons)

		buttons = html.xpath("/html/body/div[2]/div/button")
		repository = _parse_equipments_slots(buttons)

		return ItemsInfo(size, backpacks, repository)

	def move_to_backpack(self, rp_id):
		"""将仓库中的物品放入背包"""
		text = self.api.fyg_click(ClickType.PutOut, id=rp_id)
		if text != "ok":
			raise Exception("失败：" + text)

	def move_to_repo(self, bp_id):
		"""将背包中的物品放入仓库"""
		text = self.api.fyg_click(ClickType.PutIn, id=bp_id)
		if text != "ok":
			raise Exception("失败：" + text)

	def put_on(self, bp_id):
		"""穿上装备"""
		text = self.api.fyg_click(ClickType.PutOn, id=bp_id)
		if text != "ok":
			raise Exception("失败：" + text)

	def destroy(self, bp_id):
		"""
		熔炼或销毁物品，如果物品是装备则熔炼为护身符；是护身符则销毁。

		:param bp_id: 物品在背包中的 ID
		:return:
		"""
		text = self.api.fyg_click(ClickType.Destroy, id=bp_id, yz="124")
		try:
			nid = int(text)
			self.api.fyg_read(ReadType.ZbTip, id=nid)
		# TODO
		except ValueError:
			match = _fc_re.search(text)
			if match is None:
				raise Exception("失败：" + text)
			return int(match.group(1))

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
