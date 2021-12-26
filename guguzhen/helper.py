from colorama import Fore

from guguzhen.api import GuGuZhen

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
	print(f"{c}{item.id} - Lv.{item.level} {item.name}{Fore.RESET}")


def print_equipments(api: GuGuZhen):
	equip = api.character.get_info()
	items = api.character.get_repository()

	print("\n武器装备信息：")
	print(f"背包格子数 = {items.size}")

	print("\n[背包]")
	for item in items.backpacks:
		_do_print_item(item)

	print("\n[仓库]")
	for item in items.repository:
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
