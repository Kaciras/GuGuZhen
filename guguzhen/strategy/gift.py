import logging
from copy import copy
from dataclasses import dataclass
from typing import List


@dataclass(eq=False, slots=True)
class GiftSandRule:
	"""额外翻卡规则，当奖池中剩余的奖励大于指定值时使用星沙追加翻卡"""

	type: str  # 奖励类型
	value: float  # 奖池剩余大于该值时尝试翻卡
	limit: int  # 如果需要的星沙大于该值则不翻


class GetGift:

	def __init__(self, sand_usage: List[GiftSandRule] = ()):
		self.sand_usage = sand_usage

	def run(self, api):
		pool = _GiftContext(api)

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

		logging.info(f"好运奖励 - 翻了{prev - count}张卡")

	def _handle_rules(self, pool, index):
		for rule in self.sand_usage:
			if pool.cost > rule.limit:
				continue
			if pool[rule.type] < rule.value:
				continue
			pool.open(index, True)


class _GiftContext:

	def __init__(self, api):
		self.api = api
		self.remaining = None
		self.opened = None

		self.total = api.get_gift_pool()
		self._refresh()

	def __getitem__(self, item):
		return self.remaining[item]

	@property
	def cost(self):
		return 2 + (2 ** len(self.opened))

	def open(self, index, use_sand):
		self.api.open_gift(index, use_sand)
		self._refresh()

	def _refresh(self):
		self.opened = self.api.get_gift_cards()
		self.remaining = copy(self.total)

		for gift in self.opened.values():
			self.remaining[gift.type] -= gift.value
