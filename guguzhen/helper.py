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
	Fore.RED
)


def _do_print_item(item):
	c = _color_map[item.grade]
	h = item_hash(item)
	e = ", ".join(map(str, item.attrs))

	if isinstance(item, Amulet):
		print(f"{h} {c}+{item.enhancement} {item.name}{Fore.RESET} {e}")
	else:
		print(f"{h} {c}Lv.{item.level} {item.name}{Fore.RESET} ({e})")


def item_hash(item: Item):
	m = sha256()
	m.update(item.grade.to_bytes(1, "big"))
	m.update(item.name.encode())

	if isinstance(item, Amulet):
		m.update(item.enhancement.to_bytes(1, "big"))
		for attr in item.attrs:
			m.update(str(attr).encode())
	else:
		m.update(item.level.to_bytes(2, "big"))
		for attr in item.attrs:
			m.update(str(attr).encode())
		if item.mystery:
			m.update(item.mystery.encode())

	digest = m.digest()[:6]
	return urlsafe_b64encode(digest).decode()


def print_equipments(api: GuGuZhen):
	equip = api.character.get_info()
	items = api.character.get_repository()

	print(f"\n[背包 (容量 = {items.size})]")
	for item in items.backpacks.values():
		_do_print_item(item)

	print("\n[仓库]")
	for item in items.repository.values():
		_do_print_item(item)


def print_cards(api: GuGuZhen):
	print("\n[角色卡片]")

	for card in api.character.get_cards():
		parts = [
			str(card.id),
			f"Lv.{card.level}/{card.lv_max}",
			str(card.role),
			f"{card.skills}技能位",
			f"{card.quality}%品质"
		]

		color = Fore.RESET
		if card.in_use:
			color = Fore.BLUE
			parts.append("[使用中]")

		line = " ".join(parts)
		print(color + line + Fore.RESET)
