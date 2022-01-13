from collections import defaultdict
from dataclasses import dataclass, fields
from itertools import chain

from guguzhen.api import GuGuZhen, Talent, ItemsInfo
from guguzhen.helper import item_hash

# 4个元素分别是武器、手部、衣服、发饰的 Hash，为 None 的元素表示不换（咕咕镇好像不能卸下装备）
EquipTuple = list[str, str, str, str]

_NE = (None,) * 4

@dataclass(eq=False)
class CharacterPreset:
	"""
	角色配置，定义了所使用的卡片、天赋、装备、背包护身符，运行该策略将切换它们。
	该策略可用于一键换装（和护身符、卡片等等）。

	装备和背包使用物品的 Hash，为 None 的属性表示不换。
	"""

	card_id: int = None  			# 卡片的 ID
	talent: list[Talent] = None		# 光环天赋
	equipment: EquipTuple = _NE		# 装备
	backpack: list[str] = None		# 背包（超出容量的部分将忽略）

	@staticmethod
	def snapshot(api: GuGuZhen):
		"""获取当前的配置"""
		zid = api.character.get_current_card().id

		talent = api.character.get_talent().talent

		bp = api.items.get_info().backpacks
		bp = [item_hash(x) for x in bp.values()]

		eq = api.character.get_info()
		eq_list = []
		for f in fields(eq):
			v = getattr(eq, f.name)
			if v:
				eq_list.append(item_hash(v))
			else:
				eq_list.append(None)

		return CharacterPreset(zid, talent, eq_list, bp)

	def has_change(self, other):
		""""""

	def run(self, api: GuGuZhen):
		if self.card_id:
			api.character.switch_card(self.card_id)

		if self.talent is not None:
			api.character.set_talent(self.talent)

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

		if self.backpack:

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
				print(f"{id_} [背包] -> [仓库]")

			ctx.refresh()

			free = ctx.items.size - reaming
			for h in out_list[:free]:
				api.rest()
				id_ = ctx.rp_map[h].pop()
				api.items.put_out(id_)
				ctx.refresh()
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
		self.refresh()

	def refresh(self):
		self._update_items_state(self.api.items.get_info())

	def _update_items_state(self, items: ItemsInfo):
		self.items = items
		self.bp_map.clear()
		self.rp_map.clear()

		for id_, e in items.backpacks.items():
			self.bp_map[item_hash(e)].append(id_)
		for id_, e in items.repository.items():
			self.rp_map[item_hash(e)].append(id_)

	def ensure_slot(self):
		"""
		在背包中腾一个位置，背包物品数可能大于实际容量
		"""
		i, api = self.items, self.api

		while len(i.backpacks) >= i.size:
			ids = i.backpacks.keys()
			api.rest()
			api.items.put_in(next(iter(ids)))
			i = api.items.get_info()

		self._update_items_state(i)

	def r2b(self, hash_):
		"""
		Repository to backpack

		:param hash_: 物品的 Hash
		:return: 物品在背包中的 ID
		"""
		self.ensure_slot()

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
		self.refresh()
