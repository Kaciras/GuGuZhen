import logging
from http.cookiejar import LWPCookieJar

import fire
import inquirer
from browser_cookie3 import *

from guguzhen.api import GuGuZhen
from guguzhen.api.base import ClientVersionError
from guguzhen.helper import print_cards, print_items
from play import actions


def choose(cookies_map):
	question = inquirer.List("name", "在以下浏览器中找到了咕咕镇的 Cookies，复制哪个？", cookies_map)
	answers = inquirer.prompt([question], raise_keyboard_interrupt=True)
	return cookies_map[answers["name"]]


class GuGuZhenCli:

	@staticmethod
	def clone():
		"""复制浏览器的 Cookies"""
		browsers = (Chrome, Chromium, Opera, Brave, Edge, Firefox)
		found = {}

		for browser in browsers:
			try:
				cookies = browser(domain_name="www.guguzhen.com").load()
				if len(cookies) > 0:
					found[browser.__name__] = cookies
			except BrowserCookieError:
				pass

		if len(found) == 0:
			print("在所有的浏览器中都未找到相关 Cookie")
			return
		elif len(found) > 1:
			jar = choose(found)
		else:
			jar = found.popitem()[1]

		dist = LWPCookieJar()
		for cookie in jar:
			dist.set_cookie(cookie)

		print(dist)

	@staticmethod
	def login(user, password):
		"""使用用户名和密码登录"""
		api = GuGuZhen()
		api.login(user, password)
		api.save_cookies()

	@staticmethod
	def items(short=False):
		"""查看卡片和装备"""
		api = GuGuZhen()
		api.connect()

		print_cards(api)
		print_items(api, short)
		api.save_cookies()

	@staticmethod
	def play():
		"""运行自动游戏脚本"""
		api = GuGuZhen()
		api.connect()

		try:
			for action in actions:
				api.rest()
				action.run(api)

			api.save_cookies()
			logging.info("Completed.")
		except ClientVersionError as e:
			logging.warning(str(e))


if __name__ == '__main__':
	fire.Fire(GuGuZhenCli)
