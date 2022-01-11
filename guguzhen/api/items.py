import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional, Sequence, Literal

from lxml import etree

from .base import ReadType, FYGClient, ClickType, LimitReachedError, FygAPIError

_lvp = re.compile(r">(\d+)</span> (.+)")

_id_with_label = re.compile(r"(\d+)','Lv.\d+ ([^']+)")

_color_class = re.compile(r"fyg_colpz0(\d)bg")

_amulet_content = re.compile(r"\+(\d+)\s([点%])")

_fc_re = re.compile(r"获得(\d+)水果核")

_onclick_id = re.compile(r"\('?(\d+)'?[,)]")

EquipType = Literal[
	"探险者短仗",
	"光辉法杖",
	"探险者之剑",
	"陨铁重剑",
	"狂信者的荣誉之刃",
	"幽梦匕首",
	"荆棘剑盾",
	"探险者手套",
	"秃鹫手套",
	"命师的传承手环",
	"旅法师的灵光袍",
	"探险者头巾",
	"占星师的发饰",
	"天使缎带",
	"战线支撑者的荆棘重甲",
	"探险者短弓",
	"反叛者的刺杀弓",
	"探险者布甲",
	"探险者皮甲",
	"探险者铁甲",
]

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
	"""装备的一条属性"""

	type: str   				# 属性名
	ratio: float  				# 倍率
	value: int | float 			# 属性值，若是百分比则为 float

	def __str__(self):
		if isinstance(self.value, int):
			return f"[{self.ratio:.0%} {self.type} {self.value}]"
		else:
			return f"[{self.ratio:.0%} {self.type} {self.value:.0%}]"


@dataclass(frozen=True, slots=True)
class AmuletAttr:
	"""护身符的一条属性"""

	type: str					# 属性名
	value: int | float			# 增加量，若是百分比则为 float

	def __str__(self):
		if isinstance(self.value, int):
			return f"[{self.type} +{self.value}点]"
		else:
			return f"[{self.type} +{self.value:.0%}]"


@dataclass(frozen=True, slots=True)
class Amulet:
	"""护身符物品"""

	grade: Grade					# 品质
	name: str		 				# 名字
	enhancement: int				# 强化次数
	attrs: Sequence[AmuletAttr]		# 属性列表


@dataclass(frozen=True, slots=True)
class Equipment:
	"""装备物品，如果是 PK 记录则后两个属性为 None"""

	grade: Grade							# 装备品质
	name: EquipType							# 物品名
	level: int								# 装备等级

	attrs: Optional[Sequence[EquipAttr]]	# 属性列表
	mystery: Optional[str]					# 神秘属性文本


# 背包和仓库里的物品，可以是护身符或装备
Item = Amulet | Equipment


@dataclass(eq=False)
class ItemsInfo:
	size: int					 		# 当前背包容量（可能超出限制）
	backpacks: Dict[int, Item]	 		# 背包物品
	repository: Dict[int, Item]  		# 仓库物品


def _parse_item_list(buttons):
	id_and_item = {}

	for button in buttons:
		if not button.get("onclick"):
			continue
		item = parse_item_button(button)
		id_ = _get_id(button)
		id_and_item[id_] = item

	return id_and_item


def grade_from_class(button: etree.ElementBase):
	match = _color_class.search(button.get("class"))
	return Grade(int(match.group(1)))


def parse_item_button(button: etree.ElementBase):
	title = button.get("title")

	# 随机卡片标题为空
	if not title:
		return RandomCard

	grade = grade_from_class(button)
	entries = etree.HTML(button.get("data-content")).findall("body/p")

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

	value = int(v)
	if u == "%":
		value /= 100

	return AmuletAttr(paragraph.text, value)


def _parse_equip_attr(paragraph: etree.ElementBase):
	label, text = paragraph.iterchildren()

	ratio = int(label.text[:-1]) / 100
	type_, value = text.text.split(" ")

	if value[-1] == "%":
		value = int(value[:-1]) / 100
	else:
		value = int(value)

	return EquipAttr(type_, ratio, value)


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

		buttons = html.findall("body/div[1]/div/button")
		size = len(buttons)
		backpacks = _parse_item_list(buttons)

		buttons = html.findall("body/div[2]/div/button")
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
