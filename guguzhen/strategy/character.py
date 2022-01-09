from collections import defaultdict
from itertools import chain

from guguzhen.api import GuGuZhen, Talent
from guguzhen.helper import item_hash

EquipTuple = list[str, str, str, str]


class CharacterPreset:

	def __init__(self, card_id: int = None,
				 halo: list[Talent] = None,
				 equipment: EquipTuple = None,
				 backpack: list[str] = None):
		self.card_id = card_id
		self.halo = halo
		self.equipment = equipment
		self.backpack = backpack

	def run(self, api: GuGuZhen):
		if self.card_id:
			api.character.switch_card(self.card_id)

		if self.halo is not None:
			api.character.set_halo(self.halo)

		# 切换装备和背包，
		ctx = ItemSwitchContext(api)

		# 先换装备
		config = api.character.get_info()
		s = (config.weapon, config.bracelet, config.armor, config.accessory)
		for i, e in enumerate(self.equipment):
			if item_hash(s[i]) != e:
				api.rest()
				ctx.put_on(e)

		out_list, reaming = [], 0
		ctx.refresh()

		for h in self.backpack:
			ids = ctx.bp_map[h]
			if ids:
				reaming += 1
				ids.pop()
			else:
				out_list.append(h)

		for id_ in chain.from_iterable(ctx.bp_map.values()):
			api.rest()
			api.items.put_in(id_)
			print(f"{id_} [背包] -> [仓库]") # 4416100

		free = ctx.items.size - reaming
		for h in out_list[:free]:
			api.rest()
			id_ = ctx.rp_map[h].pop()
			api.items.put_out(id_)
			print(f"{id_} [仓库] -> [背包]")


class ItemSwitchContext:
	"""
	换装的代码比较多，单独提出来。
	"""

	def __init__(self, api: GuGuZhen):
		self.api = api
		self.bp_map = defaultdict(list)
		self.rp_map = defaultdict(list)
		self.items = None

		self.config = api.character.get_info()
		self.refresh()

	def refresh(self):
		items = self.items = self.api.items.get_info()
		self.bp_map.clear()
		self.rp_map.clear()

		for id_, e in items.backpacks.items():
			self.bp_map[item_hash(e)].append(id_)
		for id_, e in items.repository.items():
			self.rp_map[item_hash(e)].append(id_)

	def r2b(self, hash_):
		"""

		:param hash_:
		:return:
		"""
		bp = self.items.backpacks
		if len(bp) >= self.items.size:
			v = bp.popitem()[0]
			self.api.items.put_in(v)

		id_ = self.rp_map[hash_][0]
		self.api.rest()
		self.api.items.put_out(id_)
		self.refresh()

		return self.bp_map[hash_][0]

	def put_on(self, hash_):
		try:
			id_ = self.bp_map[hash_][0]
		except IndexError:
			id_ = self.r2b(hash_)

		self.api.items.put_on(id_)
