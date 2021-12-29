import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple

from lxml import etree

from .base import FYGClient, ReadType, VS, ClickType, LimitReachedError, Role

_exp = re.compile(r"获得了 (\d+) ([^<]+)")
_base = re.compile(r"基准值:(\d+)，随机范围([0-9.]+)-([0-9.]+)倍")


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
	rank: PKRank	 	# 当前所在段位
	progress: int	 	# 段位进度
	power: int		 	# 今日体力
	strengthen: int		# 野怪附加强度


@dataclass(eq=False, slots=True)
class Trophy:
	value: int					# 数值
	type: str					# 资源类型
	base: int					# 基准值
	range: Tuple[float, float]  # 范围


@dataclass(eq=False, slots=True)
class Fighter:
	name: str		 # 名字
	role: Role		 # 职业（卡片）
	leval: int		 # 等级
	strengthen: int  # 强度（仅野怪）


@dataclass(eq=False, slots=True)
class Fighting:
	player: Fighter
	enemy: Fighter
	# 懒得解析对战记录了


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


	def pillage(self):
		"""搜刮资源"""
		html = self.api.fyg_click(ClickType.Pillage)
		match1 = _exp.search(html)

		if match1 is None:
			raise LimitReachedError()

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
			raise Exception("星沙不够")
