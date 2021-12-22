import copy
import logging
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

		self._remaining = None
		self._pool = None
		self._opened = None

	def _refresh(self, client):
		self._opened = client.get_gift_cards()
		self._remaining = copy.copy(self._pool)

		for gift in self._opened.values():
			self._remaining[gift.type] -= gift.value

	def _open(self, client, index, use_sand):
		client.open_gift(index, use_sand)
		self._refresh(client)

	def run(self, client):
		self._pool = client.get_gift_pool()
		self._refresh(client)

		prev = count = len(self._opened)
		if count == 0:
			self._open(client, 1, False)

		for index in range(1, 13):
			if index in self._opened:
				continue
			require = 2 + (2 ** len(self._opened))
			self._handle_rules(client, index, require)

			if len(self._opened) == count:
				break

			count = len(self._opened)

		logging.info(f"好运奖励 - 翻了{prev - count}张卡")

	def _handle_rules(self, client, index, require):
		for rule in self.sand_usage:
			if self._pool[rule.type] < rule.value:
				continue
			if require > rule.limit:
				continue
			self._open(client, index, True)
