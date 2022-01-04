import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple, Sequence, Literal

from lxml import etree

from .base import FYGClient, ReadType, VS, ClickType, LimitReachedError
from .character import EquipConfig, Role
from .items import Equipment, parse_item_icon

_exp = re.compile(r"获得了 (\d+) ([^<]+)")

_base = re.compile(r"基准值:(\d+)，随机范围([0-9.]+)-([0-9.]+)倍")

_lv_pattern = re.compile(r"Lv\.(\d+)(?:\((\d+)%\))?")

_spaces = re.compile("\s+")

_icon_class_map = {
	"icon icon-bolt text-danger fyg_f14": "AD",
	"icon icon-bolt text-primary fyg_f14": "AP",
	"icon icon-bolt text-warning fyg_f14": "TD",
	"icon icon-minus text-danger fyg_f14": "HP_lose",
	"icon icon-minus text-info fyg_f14": "ES_lose",
	"icon icon-plus text-danger fyg_f14": "HP_health",
	"icon icon-plus text-info fyg_f14": "ES_health",
}

CreepType = Literal["铁皮木人", "嗜血的迅捷蛛", "魔灯之灵", "憨憨的食铁兽"]


class PKRank(IntEnum):
	C = 1
	CC = 2
	CCC = 3
	B = 4
	BB = 5
	BBB = 6
	A = 7
	AA = 8
	AAA = 9
	S = 10
	SS = 11
	SSS = 12


@dataclass(eq=False, slots=True)
class PKInfo:
	rank: PKRank	 		# 当前所在段位
	progress: int	 		# 段位进度
	power: int		 		# 今日体力
	strengthen: int			# 野怪附加强度


@dataclass(eq=False, slots=True)
class Trophy:
	"""一次搜刮资源的结果"""

	value: int					# 数值
	type: str					# 资源类型
	base: int					# 基准值
	range: Tuple[float, float]  # 范围


@dataclass(eq=False, slots=True)
class Player:
	name: str					# 名字
	role: Role					# 职业（卡片）
	leval: int					# 等级
	equipment: EquipConfig		# 装备


@dataclass(eq=False, slots=True)
class Creep:
	type: CreepType				# 名字
	leval: int					# 等级
	strengthen: float			# 强度


@dataclass(init=False, eq=False, slots=True)
class Action:
	is_attack: bool				# 是攻击方？
	state: Sequence[str]		# 技能和状态

	HP: int						# 血量
	ES: int						# 护盾

	AD: int = None				# 物伤
	AP: int = None				# 法伤
	TD: int = None				# 真伤

	HP_lose: int = None			# 掉血
	ES_lose: int = None			# 掉盾

	HP_health: int = None		# 回血
	ES_health: int = None		# 回盾


ActionPair = tuple[Action, Action]


@dataclass(eq=False, slots=True)
class Battle:
	player: Player					# 自己
	enemy: Player					# 敌人
	actions: Sequence[ActionPair]	# 过程


def _parse_fighter(equips, info):
	h3 = info.getchildren()[0]
	lv, role = _spaces.split(h3.getchildren()[0].tail)

	if role.startswith("Lv"):
		lv, role = role, lv

	match = _lv_pattern.match(lv)
	if role == "野怪":
		level, strengthen = match.groups()
		return Creep(h3.text, int(level), int(strengthen) / 100)

	# TODO: 如果装备不齐？懒得新建小号测试，等遇到了再说
	e = []
	for button in equips.iterchildren():
		name = button.get("title")
		gradle, level = parse_item_icon(button)
		e.append(Equipment(gradle, name, level, None, None))

	ec = EquipConfig(*e)
	return Player(h3.text, role, int(match.group(1)), ec)


def _parse_values(action, icon_col, col2):
	for icon in icon_col.xpath("p/i"):
		key = _icon_class_map[icon.get("class")]
		setattr(action, key, int(icon.text))

	es, hp = col2.xpath("span/text()")
	action.ES, action.HP = int(es), int(hp)


class PKApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""获取段位、体力等基本信息"""
		html = self.api.fyg_read(ReadType.PK)
		html = etree.HTML(html)
		spans = html.xpath("//span")

		return PKInfo(
			PKRank[spans[0].text],
			int(spans[1].text[:-1]),
			int(spans[-2].text),
			int(spans[-1].text),
		)

	def battle(self, target: VS):
		html = self.api.fyg_v_intel(target)
		html = etree.HTML(html)
		rows = html.xpath("/html/body/div/div")

		fs = rows[0].xpath("div/div[1]/div[1]")
		player = _parse_fighter(*fs[0].getchildren())
		enemy = _parse_fighter(*reversed(fs[1].getchildren()))

		actions = []
		for i in range(1, len(rows) - 2, 3):
			act1, act2 = Action(), Action()

			p1 = rows[i].xpath("div[1]/p")[0]
			act1.is_attack = "bg-special" in p1.get("class")
			act2.is_attack = not act1.is_attack

			act1.state = p1.xpath("i/b/text()")
			act2.state = rows[i].xpath("div[2]/p/i/b/text()")

			h = rows[i + 1].getchildren()
			la, ls, rs, ra =  h
			_parse_values(act1, la, ls)
			_parse_values(act2, ra, rs)

			actions.append((act1, act2))

		return Battle(player, enemy, actions)

	def pillage(self):
		"""搜刮资源"""
		html = self.api.fyg_click(ClickType.Pillage)
		match1 = _exp.search(html)

		if match1 is None:
			raise LimitReachedError("没有体力了")

		match2 = _base.search(html)
		min_, max_ = match2.groups()[1:]

		return Trophy(
			int(match1.group(1)),
			match1.group(2),
			int(match2.group(1)),
			(float(min_), float(max_)),
		)

	def rejuvenate(self):
		"""恢复体力到 100，固定消耗 20 星沙"""
		text = self.api.fyg_click(ClickType.Rejuvenate)
		if text != "体力已刷新。":
			raise LimitReachedError("星沙不够")
