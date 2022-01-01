import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from lxml import etree

from .base import ReadType, FYGClient, Role, ClickType, FygAPIError
from .items import Equipment, parse_item_button

_card_attrs_re = re.compile(r"(\d+) 最大等级<br/>(\d+) 技能位<br/>(\d+)% 品质")

_highlight_code = re.compile(r'\$\("#tf(\d+)"\)\.attr\("class","btn btn-primary"\);')


class Talent(Enum):
	"""
	所有的光环天赋，值是对应的 ID，名字懒得翻译成英文了。
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
		"""技能需要的光环数量"""
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
	halo: float
	talent: tuple[Talent]


@dataclass
class EquipConfig:
	"""当前身上穿的 4 个装备"""

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


def _parse_card(div: etree.ElementBase):
	lv, _, name = div.xpath("div[1]/div")

	tl = div.xpath("div[2]")[0]
	attrs = etree.tostring(tl, encoding="unicode")
	match = _card_attrs_re.search(attrs)

	return Card(
		int(div.get("onclick")[7:-1]),
		int(lv.xpath("span")[0].text),
		name.text.strip(),
		int(match.group(1)),
		int(match.group(2)),
		float(match.group(3)) / 100,
		attrs.find("当前使用中") > 0
	)


class CharacterApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""我的战斗信息"""
		html = self.api.fyg_read(ReadType.Character)
		html = etree.HTML(html)

		buttons = html.xpath("//div[@class='fyg_tc']/button")
		return EquipConfig(*map(parse_item_button, buttons))

	def get_talent(self):
		html = self.api.fyg_read(ReadType.Talent)
		html = etree.HTML(html)

		h1 = html.xpath("/html/body/h1")[0]
		halo = float(h1.text[:-1])

		script = html.xpath("/html/body/script")[0].text
		ids = _highlight_code.findall(script)
		talent = map(lambda x: Talent(int(x)), ids)

		return TalentPanel(halo, tuple(talent))

	def set_talent(self, values: Iterable[Talent]):
		arr = ",".join(map(lambda x: x.value, values))
		text = self.api.fyg_click(ClickType.SetTalent, arr=arr)
		# 点数不足：start_with 你当前装备的卡片
		# 错误的天赋 ID 也返回 ok……
		if text != "ok":
			raise FygAPIError("光环天赋保存失败：" + text)

	def get_cards(self):
		"""角色卡片列表"""
		html = self.api.fyg_read(ReadType.CardList)
		html = etree.HTML(html)

		return tuple(map(_parse_card, html.xpath("/html/body/div")))

	def switch_card(self, card):
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.SwitchCard, id=card)
		if text != "ok":
			raise FygAPIError("换卡失败：" + text)

	def rebuild(self, card):
		"""重置卡片的加点"""
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.Rebuild, id=card)

	def delete_card(self, card):
		if isinstance(card, Card):
			card = card.id
		text = self.api.fyg_click(ClickType.SwitchCard, id=card)
		if text.startswith("你没有"):
			raise FygAPIError("你没有这张卡片或已经装备中")

