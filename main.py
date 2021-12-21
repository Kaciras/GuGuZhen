import os
import time

import dotenv
from guguzhen.strategy import *
from guguzhen.api import GuGuZhen

dotenv.load_dotenv()


def play(actions):
	api = GuGuZhen(cookies)
	api.fetch_safeid()

	for action in actions:
		action.run(api)
		time.sleep(2)

	api.save_cookies()
	logging.info("Completed.")


cookies = {
	"fyg2019_gameuid": os.getenv("UID"),
	"fyg2019_gamepw": os.getenv("PW"),
}

acts = [
	# CheckVersion("2021/10/20"),
	GetGift([
		GiftSandRule("halo", 5, 1)
	])
]

if __name__ == '__main__':
	play(acts)
