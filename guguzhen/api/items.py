import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional

from lxml import etree

from .base import ReadType, FYGClient, ClickType, LimitReachedError, FygAPIError

_lvp = re.compile(r">(\d+)</span> (.+)")

_id_with_label = re.compile(r"(\d+)','Lv.\d+ ([^']+)")

_color_class = re.compile(r"fyg_colpz0(\d)bg")

_amulet_content = re.compile(r"\+(\d+) ([点%])")

_fc_re = re.compile(r"获得(\d+)水果核")

_onclick_id = re.compile(r"\('?(\d+)'?[,)]")


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
	ratio: float  	# 倍率
	value: int  	# 属性值

	def __str__(self):
		return f"[{self.ratio:.0%} {self.type} {self.value}]"


@dataclass(frozen=True, slots=True)
class AmuletAttr:
	type: str		# 增加的属性
	value: int		# 增加量（若是百分比需要除以 100）
	unit: str		# 单位，"点" 或 "%"

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


# 背包和仓库里的物品，可以是护身符或装备
Item = Amulet | Equipment


@dataclass(eq=False)
class ItemsInfo:
	size: int					 # 背包格子数
	backpacks: Dict[int, Item]	 # 背包物品
	repository: Dict[int, Item]  # 仓库物品


def _parse_item_list(buttons):
	id_and_item = {}

	for button in buttons:
		if not button.get("onclick"):
			continue
		item = parse_item_button(button)
		id_ = _get_id(button)
		id_and_item[id_] = item

	return id_and_item


def parse_item_button(button):
	title = button.get("title")

	# 随机卡片标题为空
	if not title:
		return RandomCard

	match = _color_class.search(button.get("class"))
	grade = Grade(int(match.group(1)))
	entries = etree.HTML(button.get("data-content")).xpath("/html/body/p")

	# 护身符的 onclick 是两个参数。
	match = _lvp.search(title)
	if not match:
		enhance = int(button.getchildren()[0].tail)
		attrs = tuple(map(_parse_amulet_attr, entries))

		return Amulet(grade, title, enhance, attrs)

	# 剩下的情况就是装备。
	attrs = tuple(map(_parse_equip_attr, entries[:4]))
	mystery = entries[4].text if len(entries) > 4 else None
	level, name = match.groups()

	return Equipment(grade, name, int(level), attrs, mystery)


def _parse_amulet_attr(paragraph: etree.ElementBase):
	span = paragraph.getchildren()[0]
	v, u = _amulet_content.match(span.text).groups()
	return AmuletAttr(paragraph.text, int(v), u)


def _parse_equip_attr(paragraph: etree.ElementBase):
	label, text = paragraph.iterchildren()

	ratio = int(label.text[:-1]) / 100
	type_, value = text.text.split(" ")

	return EquipAttr(type_, ratio, int(value[:-1]))


# xxx('<id>','Lv.1 稀有苹果护身符')、或者 xxx(<id>)
def _get_id(button):
	return int(_onclick_id.search(button.get("onclick")).group(1))


class ItemApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""获取 我的角色/武器装备 页面的信息"""
		html = self.api.fyg_read(ReadType.Equipments)
		html = etree.HTML(html)

		buttons = html.xpath("/html/body/div[1]/div/button")
		size = len(buttons)
		backpacks = _parse_item_list(buttons)

		buttons = html.xpath("/html/body/div[2]/div/button")
		repository = _parse_item_list(buttons)

		return ItemsInfo(size, backpacks, repository)

	def put_out(self, rp_id):
		"""
		将物品放入背包，该物品必须在仓库中。

		:param rp_id 物品在仓库中的 ID
		"""
		text = self.api.fyg_click(ClickType.PutOut, id=rp_id)
		if text == "背包已满。":
			raise LimitReachedError(text)
		if text != "ok":
			raise FygAPIError(f"{text}({rp_id=})")

	def put_in(self, bp_id):
		"""
		将物品放入仓库，该装备必须在背包中。

		:param bp_id 物品在背包中的 ID
		"""
		text = self.api.fyg_click(ClickType.PutIn, id=bp_id)
		if text != "ok":
			raise FygAPIError(f"{text}({bp_id=})")

	def put_on(self, bp_id):
		"""
		穿上装备，该装备必须在背包中。

		:param bp_id 物品在背包中的 ID
		"""
		text = self.api.fyg_click(ClickType.PutOn, id=bp_id)
		if text != "ok":
			raise FygAPIError(f"{text}({bp_id=})")

	def destroy(self, bp_id):
		"""
		熔炼或销毁物品，该物品必须在背包中。
		如果物品是装备则熔炼为护身符；是护身符则销毁。

		:param bp_id: 物品在背包中的 ID
		:return: 如果是熔炼则返回护身符 ID，否则 None
		"""
		text = self.api.fyg_click(ClickType.Destroy, id=bp_id, yz="124")
		try:
			return int(text)
		except ValueError:
			match = _fc_re.search(text)
			if match is None:
				raise FygAPIError("销毁失败：" + text)
			return int(match.group(1))
