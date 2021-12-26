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
	items = api.character.get_repository()
	print("武器装备信息：")
	print(f"背包格子数 = {items.size}")

	print("\n[背包]")
	for item in items.backpacks:
		_do_print_item(item)

	print("\n[仓库]")
	for item in items.repository:
		_do_print_item(item)

