import logging
from copy import copy
from dataclasses import dataclass
from typing import Sequence

from .core import AbstractStrategy
from ..api import GuGuZhen

logger = logging.getLogger("GetGift")


@dataclass(eq=False, slots=True)
class GiftSandRule:
	"""额外翻卡规则，当奖池中剩余的奖励大于指定值时使用星沙追加翻卡"""

	type: str		# 奖励类型
	value: float    # 奖池剩余大于该值时尝试翻卡
	limit: int		# 如果需要的星沙大于该值则不翻


class GetGift(AbstractStrategy):

	def __init__(self, sand_usage: Sequence[GiftSandRule] = ()):
		self.sand_usage = sand_usage

	def run(self, api: GuGuZhen):
		pool = _GiftContext(api)

		lt = tuple(pool.total.values())
		lb = tuple(pool.base.values())
		logger.info(f"今日奖池 - 总共：{lt}，基本：{lb}")

		prev = count = len(pool.opened)
		if count == 0:
			pool.open(1, False)

		for index in range(1, 13):
			if index in pool.opened:
				continue

			self._handle_rules(pool, index)

			if len(pool.opened) == count:
				break

			count = len(pool.opened)

	def _handle_rules(self, pool, index):
		for rule in self.sand_usage:
			if pool.cost > rule.limit:
				continue
			if pool[rule.type] < rule.value:
				continue
			pool.open(index, True)


class _GiftContext:

	def __init__(self, api: GuGuZhen):
		self.api = api
		self.remaining = None
		self.opened = None

		self.total, self.base = api.gift.get_pool()
		self._refresh()

	def __getitem__(self, item):
		return self.remaining[item]

	@property
	def cost(self):
		"""打开下一个礼物需要的星沙数量"""
		n = len(self.opened)
		return 0 if n == 0 else 2 + (2 ** n)

	def open(self, index, use_sand):
		self.api.rest()
		self.api.gift.open(index, use_sand)
		self._refresh()

	def _refresh(self):
		self.opened = self.api.gift.get_opened()
		self.remaining = copy(self.total)

		for gift in self.opened.values():
			self.remaining[gift.type] -= gift.value
