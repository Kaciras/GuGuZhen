import logging
import math
from typing import Sequence, AbstractSet

from .core import AbstractStrategy
from ..api import GuGuZhen, Card, RandomCard, Role
from ..helper import UniversalSet


class _NOPCleaner:

	def clean(self, api, cards, count): pass


class CardCleaner:
	"""清理卡片,正在使用的卡片不会被删除"""

	def __init__(self, rules, protect=frozenset()):
		self.rules = rules
		self.protect = protect

	def run(self, api: GuGuZhen):
		self.clean(api, api.character.get_cards(), 2 ** 31)

	def clean(self, api: GuGuZhen, cards: Sequence[Card], count: int):
		removable = []

		for card in cards:
			if card.id in self.protect:
				continue
			if card.in_use:
				continue
			removable.append(card)

		for rule in self.rules:
			if count <= 0:
				return
			es = rule(api, removable.copy(), count)
			for eliminated in es:
				removable.remove(eliminated)
				count -= 1
				api.character.delete_card(eliminated)

	@staticmethod
	def fifo():
		"""简单删除最旧的卡片"""
		return lambda _, cards, count: cards[-count:]

	@staticmethod
	def level(
			roles: AbstractSet[Role] = UniversalSet(),
			skills: int = 0,
			offset: int = math.inf,
	):
		"""
		优先选用技能点多的卡片，也能简单地根据角色和技能位过滤。

		:param roles: 保留哪些角色
		:param skills: 技能位至少几个
		:param offset: 等级差限制
		:return:
		"""

		def filter_weak_cards(api, cards, count):
			threshold = api.get_user().level + 200
			threshold = (threshold * 1.08) - offset

			for card in cards:
				lvs = card.lv_max * (1 + card.quality)

				if count == 0:
					return

				if (card.skills < skills) \
						or (card.role not in roles) \
						or (lvs < threshold):
					count -= 1
					yield card

		return filter_weak_cards


class EC:

	def __init__(self, types, count):
		self.types = types
		self.count = count

	def run(self, api: GuGuZhen):
		all = api.items.get_info()


class PickBeach(AbstractStrategy):

	def __init__(self, card_cleaner: CardCleaner = _NOPCleaner()):
		self.card_cleaner = card_cleaner

	def run(self, api: GuGuZhen):
		card_ids = []

		for id_, item in api.beach.get_items():
			if item == RandomCard:
				card_ids.append(id_)

		if card_ids:
			ex = api.character.get_cards()
			count = 8 + len(card_ids) - len(ex)
			if count > 0:
				self.card_cleaner.clean(api, ex, count)

			for id_ in card_ids:
				api.beach.pick(id_)

		api.beach.clear()
		logging.info(f"在海滩捡了{len(card_ids)}张卡")
