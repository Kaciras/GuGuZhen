import logging

import fire

from guguzhen.api import GuGuZhen
from guguzhen.api.base import ClientVersionError
from guguzhen.helper import print_cards, print_items
from play import actions


class GuGuZhenCli:

	@staticmethod
	def login(user, password):
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
