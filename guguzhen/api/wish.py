from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime

from guguzhen.api import ReadType
from .base import FYGClient

_WishValues = namedtuple("WishValues", [
	"强化背包", "每日海滩出产装备", "对玩家战斗进度保护",
	"对野怪战斗进度保护", "强化搜刮奖励经验", "强化搜刮奖励贝壳",

	"战斗用生命药水", "战斗用护盾药水",

	"天赋启程之誓强化", "天赋启程之心强化", "天赋启程之风强化",

	"对手是野怪时伤害增强", "对手是野怪时生命增强"
])


@dataclass(eq=False, slots=True)
class WishInfo:
	expiration: datetime
	cost: int
	point: int
	buffers: _WishValues


class WishApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		text = self.api.fyg_read(ReadType.Wish)
		xy_arr = text.split("#")

		return WishInfo(
			datetime.strptime(xy_arr[2], ""),
			int(xy_arr[0]),
			int(xy_arr[1]),
			_WishValues(*map(int, xy_arr[3:]))
		)

