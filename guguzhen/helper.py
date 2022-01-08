import math
from base64 import urlsafe_b64encode
from hashlib import sha256
from struct import pack
from typing import AbstractSet

import inquirer
from browser_cookie3 import *
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


class UniversalSet(AbstractSet):
	"""
	表示全集，包含所有，该类仅用于判断是否存在，不支持获取其中的元素。

	【与字面量集合的区别】
	以 Role 为例，字面量随着服务端版本更新可能会改变，比如出了新的角色，
	如果用 frozenset(get_args(Role)) 无法包含新出的，必须等待程序更新；
	而全集则没有这个问题，在使用上是有差别的。
	"""

	def __len__(self):
		return math.inf

	def __iter__(self):
		raise NotImplementedError()

	def __contains__(self, _):
		return True


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
		hs = (f"'{item_hash(e)}'" for e in items[i:i + 10])
		line = ", ".join(hs)
		print(line + "," if i + 10 < len(items) else line)


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

			if isinstance(attr.value, int):
				m.update(attr.value.to_bytes(2, "big"))
			else:
				m.update(pack(">f", attr.value))
	elif item.attrs is None:
		raise TypeError("装备对象不含属性，无法 Hash")
	else:
		m.update(item.level.to_bytes(2, "big"))

		for attr in item.attrs:
			m.update(attr.type.encode())
			m.update(pack(">f", attr.ratio))

			if isinstance(attr.value, int):
				m.update(attr.value.to_bytes(2, "big"))
			else:
				m.update(pack(">f", attr.value))

		if item.mystery:
			m.update(item.mystery.encode())

	digest = m.digest()[:6]
	return urlsafe_b64encode(digest).decode()


def print_items(api: GuGuZhen, short: bool):
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
	items = api.items.get_info()

	print(f"\n[正在使用的]")
	print_fn([equip.weapon, equip.bracelet,
			  equip.armor, equip.accessory])

	print(f"\n[背包 (容量={items.size})]")
	print_fn(items.backpacks.values())

	print("\n[仓库]")
	print_fn(items.repository.values())


def print_cards(api: GuGuZhen):
	"""在控制台中输出所有的卡片"""
	cards = api.character.get_cards()
	print("\n[角色卡片]")

	for card in cards:
		color = Fore.RESET
		if card.in_use:
			color = Fore.BLUE
		print(f"{color}{card}{Fore.RESET}")


def scan_browser(origin):
	"""
	扫描系统里安装的浏览器，从中找出指定主机的 Cookies。

	【browser_cookies3 库中的已知问题】
	1.未指定 ConfigParser 的编码，当 Firefox 配置目录路径有中文会报错。
	2.Firefox 的 sqlite 开了预写日志，该库忘了把临时文件也复制过去，
	  导致一些 Cookie 只有关闭浏览器后才能获取到。

	:param origin: 主机名
	:return: 对应站点的 CookieJar
	"""
	browsers = (Chrome, Chromium, Opera, Brave, Edge, Firefox)
	found = {}

	for browser in browsers:
		try:
			cookies = browser(None, origin).load()
			if len(cookies) > 0:
				found[browser.__name__] = cookies
		except BrowserCookieError:
			pass

	if len(found) == 1:
		return found.popitem()[1]
	elif len(found) > 1:
		msg = "在以下浏览器中找到了 Cookies，复制哪个？"
		question = inquirer.List("name", msg, found)
		answers = inquirer.prompt([question], raise_keyboard_interrupt=True)
		return found[answers["name"]]
	else:
		return print("在所有的浏览器中都未找到咕咕镇的 Cookie")
