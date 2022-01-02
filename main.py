import logging
import os

import dotenv
import fire

from guguzhen.api import GuGuZhen
from guguzhen.api.base import ClientVersionError
from guguzhen.helper import print_cards, print_items
from play import actions

dotenv.load_dotenv()

cookies = {
	"fyg2019_gameuid": os.getenv("FYG_UID"),
	"fyg2019_gamepw": os.getenv("FYG_PW"),
}


class GuGuZhenCli:

	@staticmethod
	def login(user, password):
		api = GuGuZhen({})
		api.login(user, password)
		api.save_cookies()

	@staticmethod
	def items(short=False):
		"""查看卡片和装备"""
		api = GuGuZhen(cookies)
		api.connect()

		print_cards(api)
		print_items(api, short)
		api.save_cookies()

	@staticmethod
	def play():
		"""运行自动游戏脚本"""
		api = GuGuZhen(cookies)
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
