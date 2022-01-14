import re
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Literal

from lxml import etree

from .base import ReadType, FYGClient, ClickType, FygAPIError
from .items import Equipment, parse_item_button

_card_attrs_re = re.compile(r"(\d+) 最大等级<br/>(\d+) 技能位<br/>(\d+)% 品质")

_highlight_code = re.compile(r'\$\("#tf(\d+)"\)\.attr\("class","btn btn-primary"\);')

Role = Literal["梦", "默", "薇", "艾", "冥", "琳", "伊", "命"]


class Talent(Enum):
	"""
	所有的光环天赋，值是对应的 ID，名字懒得翻译。
	"""

	启程之誓 = 101
	启程之心 = 102
	启程之风 = 103

	破壁之心 = 201
	破魔之心 = 202
	复合护盾 = 203
	鲜血渴望 = 204
	削骨之痛 = 205

	伤口恶化 = 301
	精神创伤 = 302
	铁甲尖刺 = 303
	忍无可忍 = 304
	热血战魂 = 305
	点到为止 = 306

	沸血之志 = 401
	波澜不惊 = 402
	飓风之力 = 403
	红蓝双刺 = 404
	荧光护盾 = 405
	后发制人 = 406

	@property
	def cost(self):
		"""技能需要的光环点数"""
		rank = self.value // 100
		if rank == 1:
			return 10
		if rank == 2:
			return 30
		if rank == 3:
			return 50
		if rank == 4:
			return 100


@dataclass(eq=False)
class TalentPanel:
	"""
	我的角色 / 光环天赋页面。

	【注意：光环的值】
	光环的单位是点数，比如 123.45% 光环表示为 123.45 而不是 1.2345，
	因为光环并不与其它数据做运算，它的百分比无意义。
	"""

	halo: float				# 光环值
	talent: tuple[Talent]	# 已选择的天赋


@dataclass
class EquipConfig:
	"""当前身上穿的 4 个装备"""

	weapon: Equipment	 	 # 武器
	bracelet: Equipment	 	 # 手部
	armor: Equipment		 # 衣服
	accessory: Equipment	 # 发饰


Properties = namedtuple("Properties", [
	"str",		# 力量
	"agi",		# 敏捷
	"int",		# 智力
	"con",		# 体魄
	"men",		# 精神
	"vit",		# 意志
])

@dataclass(eq=False, slots=True)
class Card:
	"""卡片对象，部分属性仅在卡片详情中有效"""

	id: int				# 卡片 ID
	level: int			# 等级
	role: Role			# 职业
	lv_max: int			# 最大等级
	skills: int			# 技能位
	quality: float		# 品质
	in_use: bool 		# 使用中？

	props: Properties = None	# 加点

	def level_up_cost(self, to: int):
		"""升到指定等级所需的贝壳"""
		exp = 1 if self.level == 0 else 0
		return (to ** 2 - self.level ** 2) * 10 - exp

	@property
	def final_level(self):
		"""品质换算后的等级"""
		return self.level * (1 + self.quality)

	@property
	def final_lv_max(self):
		"""品质换算后的最大等级"""
		return self.lv_max * (1 + self.quality)

	@property
	def gp_max(self):
		"""该卡最大能有多少属性点"""
		return int(6 + self.final_lv_max * 3)

	@property
	def gp(self):
		"""总属性点"""
		return int(6 + self.final_level * 3)

	@property
	def gp_free(self):
		"""可分配点"""
		if self.props is None:
			raise ValueError("当前卡片未包含加点信息")
		return self.gp - sum(self.props)

	def __str__(self):
		parts = [
			str(self.id),
			f"Lv.{self.level}/{self.lv_max}",
			str(self.role),
			f"{self.skills}技能位",
			f"{self.quality:.0%}品质"
		]

		if self.in_use:
			parts.append("[使用中]")

		return " ".join(parts)


def _parse_card(div: etree.ElementBase):
	lv, _, name = div.iterfind("div[1]/div")

	tl = div.find("div[2]")
	attrs = etree.tostring(tl, encoding="unicode")
	match = _card_attrs_re.search(attrs)

	return Card(
		int(div.get("onclick")[7:-1]),
		int(lv.find("span").text),
		name.text.strip(),
		int(match.group(1)),
		int(match.group(2)),
		float(match.group(3)) / 100,
		attrs.find("当前使用中") > 0
	)


def _parse_card_detail(html: etree.ElementBase):
	card = _parse_card(html.find("body/div[1]/div/div"))
	card.in_use = html.find("body/div[1]/div[2]/button[2]/i").tail == " 本卡片装备中"

	props = html.findall("body/div[3]/div")
	props = [int(e.find("div/div").text) for e in props[1::2]]
	card.props = Properties(*props)

	return card


class CharacterApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""我的战斗信息"""
		html = self.api.fyg_read(ReadType.Character)
		html = etree.HTML(html)

		buttons = html.iterfind(".//div[@class='fyg_tc']/button")
		return EquipConfig(*map(parse_item_button, buttons))

	def get_talent(self):
		"""查询我的光环天赋"""
		html = self.api.fyg_read(ReadType.Talent)
		html = etree.HTML(html)

		halo = float(html.find("body/h1").text[:-1])

		script = html.find("body/script").text
		ids = _highlight_code.findall(script)
		talent = map(lambda x: Talent(int(x)), ids)

		return TalentPanel(halo, tuple(talent))

	def set_talent(self, values: Iterable[Talent]):
		"""保存光环技能"""
		arr = ",".join(map(lambda x: str(x.value), values))
		text = self.api.fyg_click(ClickType.SetTalent, arr=arr)

		# 错误的天赋 ID 也返回 ok
		# 列表有重复 ID 也返回 ok
		if text != "ok":
			raise FygAPIError("光环技能保存失败：" + text)

	def get_cards(self):
		"""角色卡片列表"""
		html = self.api.fyg_read(ReadType.CardList)
		html = etree.HTML(html)

		return tuple(map(_parse_card, html.iterfind("body/div")))

	def get_current_card(self, card:  Card | int | None = None):
		"""查看卡片的详细信息（加点等），参数如果为 None 则查看使用中的卡片"""
		if card is None:
			card = "mi"
		if isinstance(card, Card):
			card = card.id

		html = self.api.fyg_read(ReadType.CardDetail, zid=card)
		return _parse_card_detail(html = etree.HTML(html))

	def switch_card(self, card: Card | int):
		"""装备指定的卡片"""
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.SwitchCard, id=card)
		if text != "ok":
			raise FygAPIError("换卡失败：" + text)

	def level_up(self, card: Card | int, value: int):
		"""
		升级卡片，所需的贝壳可用 Card.level_up_cost() 计算。

		:param card: 卡片或其 ID
		:param value: 升多少级
		"""
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.LevelUp, num=card, up=value)
		if not text.startswith("卡片已升级"):
			raise FygAPIError(text)

	def rebuild(self, card: Card | int):
		"""重置卡片的加点"""
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.Rebuild, id=card)

	def delete_card(self, card: Card | int):
		"""删除指定的卡片"""
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.DeleteCard, id=card)
		if text.startswith("你没有"):
			raise FygAPIError("你没有这张卡片或已经装备中")

