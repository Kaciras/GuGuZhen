import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple, Sequence, Literal

from lxml import etree

from .base import FYGClient, ReadType, VS, ClickType, LimitReachedError
from .character import EquipConfig, Role
from .items import Equipment, grade_from_class

_exp = re.compile(r"获得了 (\d+) ([^<]+)")

_base = re.compile(r"基准值:(\d+)，随机范围([0-9.]+)-([0-9.]+)倍")

_lv_pattern = re.compile(r"Lv\.(\d+)(?:\((\d+)%\))?")

_spaces = re.compile(r"\s+")

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


@dataclass(slots=True)
class PKInfo:
	"""争夺战场里的段位、体力等等信息"""

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
	"""战斗中的玩家"""

	name: str					# 名字
	role: Role					# 职业（卡片）
	leval: int					# 等级
	equipment: EquipConfig		# 装备


@dataclass(slots=True)
class Creep:
	"""战斗中的野怪"""

	type: CreepType				# 名字
	leval: int					# 等级
	strengthen: float			# 强度


# 元组的两个元素是名字和数量，比如 星芒 15! = ("星芒", 15)，没有数量的为 0
_StateList = Sequence[tuple[str, int]]


@dataclass(eq=False, slots=True)
class Action:
	is_attack: bool				# 是攻击方？
	state: _StateList			# 技能和状态

	HP: int = 0					# 血量
	ES: int = 0					# 护盾

	AD: int = None				# 物理攻击(未计算护甲)
	AP: int = None				# 魔法攻击(未计算护甲)
	TD: int = None				# 绝对攻击

	HP_lose: int = None			# 生命值损失
	ES_lose: int = None			# 护盾损失

	HP_health: int = None		# 生命值回复
	ES_health: int = None		# 护盾回复


# 表示一次交手，左边是自己右边是对方。
Round = tuple[Action, Action]


@dataclass(eq=False, slots=True)
class Battle:
	player: Player				# 自己
	enemy: Player | Creep		# 敌人
	is_win: bool				# 己方胜利
	actions: Sequence[Round]	# 过程


def _parse_fighter(equips, info):
	h3 = info.getchildren()[0]
	lv, role = _spaces.split(h3.getchildren()[0].tail)

	if role.startswith("Lv"):
		lv, role = role, lv

	match = _lv_pattern.match(lv)
	if role == "野怪":
		level, strengthen = match.groups()
		return Creep(h3.text, int(level), int(strengthen) / 100)

	# TODO: 如果装备不齐？最近不能注册新号，没法测。
	e = []
	for button in equips.iterchildren():
		grade = grade_from_class(button)
		name = button.get("title")
		level = int(button.getchildren()[0].tail)
		e.append(Equipment(grade, name, level, None, None))

	ec = EquipConfig(*e)
	return Player(h3.text, role, int(match.group(1)), ec)


def _parse_values(action, icon_col, col2):
	for icon in icon_col.iterfind("p/i"):
		key = _icon_class_map[icon.get("class")]
		setattr(action, key, int(icon.text))

	es, hp = col2.xpath("span/text()")
	action.ES, action.HP = int(es), int(hp)


def _parse_state(values):
	for x in values:
		x = x.rstrip("!").split(" ")
		c = x[1] if len(x) > 1 else 0
		yield x[0], int(c)


class PKApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""获取段位、体力等基本信息"""
		html = self.api.fyg_read(ReadType.PK)
		html = etree.HTML(html)
		spans = html.findall(".//span")

		return PKInfo(
			PKRank[spans[0].text],
			int(spans[1].text[:-1]),
			int(spans[-2].text),
			int(spans[-1].text),
		)

	def battle(self, target: VS):
		"""
		战斗，攻击野怪或抢夺其他玩家的进度。

		:param target: 打谁
		:return: 战斗结果
		"""
		html = etree.HTML(self.api.fyg_v_intel(target))
		rows = html.findall("body/div/div")

		fs = rows[0].findall("div/div[1]/div[1]")
		player = _parse_fighter(*fs[0].getchildren())
		enemy = _parse_fighter(*reversed(fs[1].getchildren()))

		actions = []
		for i in range(1, len(rows) - 2, 3):
			p1 = rows[i].find("div[1]/p")
			attack = "bg-special" in p1.get("class")

			s1 = p1.xpath("i/b/text()")
			s2 = rows[i].xpath("div[2]/p/i/b/text()")

			act1 = Action(attack, tuple(_parse_state(s1)))
			act2 = Action(not attack, tuple(_parse_state(s2)))

			h = rows[i + 1].getchildren()
			la, ls, rs, ra = h
			_parse_values(act1, la, ls)
			_parse_values(act2, ra, rs)

			actions.append((act1, act2))

		win = "smile" in rows[-1].find("div[2]/div/i").get("class")

		return Battle(player, enemy, win, actions)

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
