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
				ctx.put_on(e)

		out_list, in_list = [], []
		for h in ctx.h_map:
			area, id_ = ctx.h_map[h]
			if h in self.backpack and area == ctx.items.repository:
				out_list.append(id_)
				self.backpack.remove(h)
			if h not in self.backpack and area == ctx.items.backpack:
				in_list.append(id_)

		for id_ in in_list:
			api.items.move_to_repo(id_)

		count = min(ctx.items.size, len(out_list))
		for i in range(0, count):
			api.items.move_to_backpack(out_list[i])


class ItemSwitchContext:
	"""
	换装的代码比较多，单独提出来。
	"""

	def __init__(self, api: GuGuZhen):
		self.api = api
		self.h_map = {}
		self.items = None

		self.config = api.character.get_info()
		self._refresh()

	def _refresh(self):
		items = self.items = self.api.items.get_repository()
		h_map = self.h_map = {}

		for id_, e in items.backpacks.items():
			h_map[item_hash(e)] = (items.backpacks, id_)
		for id_, e in items.repository.items():
			h_map[item_hash(e)] = (items.repository, id_)

	def put_on(self, hash_: str):
		area, id_ = self.h_map[hash_]
		bp = self.items.backpacks

		# 如果在背包则直接换上即可
		if area == bp:
			self.api.items.put_on(id_)
			return

		# 如果背包满了就随便交换一个
		if len(bp) >= self.items.size:
			self.api.items.move_to_repo(bp[0])
			self.api.items.move_to_backpack(id_)
			self._refresh()

		id_ = self.h_map[hash_][1]
		self.api.items.put_on(id_)
