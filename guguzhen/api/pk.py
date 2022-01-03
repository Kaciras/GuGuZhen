import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple, Sequence, Literal

from lxml import etree

from . import parse_item_button, EquipConfig
from .base import FYGClient, ReadType, VS, ClickType, LimitReachedError, Role

_exp = re.compile(r"获得了 (\d+) ([^<]+)")
_base = re.compile(r"基准值:(\d+)，随机范围([0-9.]+)-([0-9.]+)倍")

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
class Fighter:
	name: str				# 名字
	role: Role				# 职业（卡片）
	leval: int				# 等级
	equipment: EquipConfig	# 装备


@dataclass(eq=False, slots=True)
class Creep:
	type: CreepType			# 名字
	strengthen: float		# 强度


States = tuple[str, int]


@dataclass(eq=False, slots=True)
class Action:
	is_attack: bool				# 是攻击方？
	state: Sequence[States]		# 技能和状态

	HP: int						# 血量
	ES: int						# 护盾

	AD: int						# 物伤
	AP: int						# 法伤
	TD: int						# 真伤

	HP_lose: int				# 掉血
	ES_lose: int				# 掉盾

	HP_health: int				# 回血
	ES_health: int				# 回盾


ActionPair = tuple[Action, Action]


@dataclass(eq=False, slots=True)
class Fighting:
	player: Fighter					# 自己
	enemy: Fighter					# 敌人
	actions: Sequence[ActionPair]	# 过程记录


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

	def fight_creep(self):
		html = self.api.fyg_v_intel(VS.Creeps)
		html = etree.HTML(html)
		rows = html.xpath("/html/body/div/div")

		fs = rows[0].xpath("div/div[1]/div[1]")
		r,t = fs[0].getchildren()

		# 看不到具体属性
		e = []
		for button in r:
			e.append(parse_item_button(button))

		for i in range(1, len(rows) - 2, 2):
			state, attrs = rows[i], rows[i+1]



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
