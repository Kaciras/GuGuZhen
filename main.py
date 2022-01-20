import logging
from http.cookiejar import LWPCookieJar
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

import fire

from guguzhen.api import *
from guguzhen.helper import print_cards, print_items, scan_browser
from play import actions

_STORE = Path("data/cookies.txt")

class GuGuZhenCli:

	def __init__(self, forum=None, game=None):
		"""
		:param forum: 绯月GalGame 网站的 Origin
		:param game: 咕咕镇网站的 Origin
		"""
		cookies = LWPCookieJar(_STORE)
		try:
			cookies.load()
		except FileNotFoundError:
			pass

		self.api = GuGuZhen(forum, game, cookies)

	def _save_cookies(self):
		_STORE.parent.mkdir(parents=True, exist_ok=True)
		cast(LWPCookieJar, self.api.client.cookies.jar).save()

	def clone(self):
		"""复制浏览器的 Cookies"""
		url = urlsplit(self.api.game)
		src = scan_browser(url.hostname)

		dist = self.api.client.cookies.jar
		for cookie in src:
			dist.set_cookie(cookie)

		self._save_cookies()

	def login(self, user, password):
		"""使用用户名和密码登录"""
		self.api.login(user, password)
		self._save_cookies()

	def items(self, short=False):
		"""查看卡片和装备"""
		self.api.connect()
		print_cards(self.api)
		print_items(self.api, short)
		self._save_cookies()

	def play(self):
		"""运行自动游戏脚本"""
		try:
			self.api.connect()

			for action in actions:
				self.api.rest()
				action.run(self.api)

			self._save_cookies()
			logging.info("Completed.")
		except ClientVersionError as e:
			logging.warning(str(e))


if __name__ == '__main__':
	fire.Fire(GuGuZhenCli)
