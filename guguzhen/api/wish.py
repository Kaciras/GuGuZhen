from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime

from .base import FYGClient, ReadType, ClickType, FygAPIError

# 懒得翻译成英文了
WishBuffers = namedtuple("WishBuffers", [
	"强化背包", "每日海滩出产装备",
	"对玩家战斗进度保护", "对野怪战斗进度保护",
	"强化搜刮奖励经验", "强化搜刮奖励贝壳",

	"战斗用生命药水", "战斗用护盾药水",

	"天赋启程之誓强化", "天赋启程之心强化", "天赋启程之风强化",

	"对手是野怪时伤害增强", "对手是野怪时生命增强"
])


@dataclass(eq=False, slots=True)
class WishInfo:
	expiration: datetime	# 愿望有效期
	cost: int				# 下一次许愿需要的贝壳
	point: int				# 下一次的愿望的点数
	buffers: WishBuffers	# 当前增益


class WishApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		"""查询许愿池"""
		text = self.api.fyg_read(ReadType.Wish)
		xy_arr = text.split("#")

		return WishInfo(
			datetime.strptime(xy_arr[2], "%Y/%m/%d %H:%M:%S"),
			int(xy_arr[0]),
			int(xy_arr[1]),
			WishBuffers(*map(int, xy_arr[3:]))
		)

	def wish(self):
		"""许愿！"""
		self.api.fyg_click(ClickType.Wish)

	def shuffle(self):
		"""重随许愿点"""
		text = self.api.fyg_click(ClickType.ReWish)
		if text != "许愿池已经重置排列。":
			raise FygAPIError(text)
