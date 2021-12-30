from base64 import urlsafe_b64encode
from hashlib import sha256

from colorama import Fore

from guguzhen.api import GuGuZhen, Item, Amulet

_color_map = (
	None,
	Fore.LIGHTBLACK_EX,
	Fore.LIGHTBLUE_EX,
	Fore.LIGHTGREEN_EX,
	Fore.LIGHTYELLOW_EX,
	Fore.LIGHTRED_EX,
)


def _full_print(items):
	for item in items:
		c, h = _color_map[item.grade], item_hash(item)
		e = " ".join(map(str, item.attrs))

		if isinstance(item, Amulet):
			print(f"{h} {c}+{item.enhancement} {item.name}{Fore.RESET} {e}")
		else:
			m = Fore.RED + " [+神秘属性]" + Fore.RESET if item.mystery else ""
			print(f"{h} {c}Lv.{item.level} {item.name}{Fore.RESET} {e}{m}")


def _print_hash_list(items):
	"""打印物品的 hash 值，10 个一行跟游戏一致"""
	items = tuple(items)
	for i in range(0, len(items), 10):
		for e in items[i:i + 10]:
			h = item_hash(e)
			print(f"'{h}'", end="")

			if e != items[-1]:
				print(", ", end="")
		print()


def item_hash(item: Item):
	"""
	根据物品的属性生成 hash 值，可用于标识该物品。

	因为 Python 默认启用了 hash 随机化，因此 hash(obj) 的结果每次运行都不同，
	让用户添加 PYTHONHASHSEED 变量也不方便，于是就自己实现了。

	:param item: 装备或护身符
	:return: 8 位 base64 hash 值
	"""
	m = sha256()
	m.update(item.grade.to_bytes(1, "big"))
	m.update(item.name.encode())

	if isinstance(item, Amulet):
		m.update(item.enhancement.to_bytes(1, "big"))
		for attr in item.attrs:
			m.update(attr.type.encode())
			m.update(attr.value.to_bytes(2, "big"))
			m.update(attr.unit.encode())
	else:
		m.update(item.level.to_bytes(2, "big"))
		for attr in item.attrs:
			m.update(attr.type.encode())
			m.update(attr.value.to_bytes(2, "big"))
			m.update(attr.ratio.to_bytes(2, "big"))
		if item.mystery:
			m.update(item.mystery.encode())

	digest = m.digest()[:6]
	return urlsafe_b64encode(digest).decode()


def print_items(api: GuGuZhen, short=True):
	"""
	在控制台中输出所有拥有的物品。

	:param api: 不解释
	:param short: 是否使用短格式（仅输出 hash）
	"""
	if short:
		print_fn = _print_hash_list
	else:
		print_fn = _full_print

	equip = api.character.get_info()
	items = api.items.get_repository()

	print(f"\n[正在使用的]")
	print_fn([equip.weapon, equip.bracelet,
			  equip.armor, equip.accessory])

	print(f"\n[背包 (容量={items.size})]")
	print_fn(items.backpacks.values())

	print("\n[仓库]")
	print_fn(items.repository.values())


def print_cards(api: GuGuZhen):
	"""在控制台中输出所有的卡片"""
	print("\n[角色卡片]")

	for card in api.character.get_cards():
		color = Fore.RESET
		if card.in_use:
			color = Fore.BLUE
		print(f"{color}{card}{Fore.RESET}")
