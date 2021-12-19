import os

import dotenv

from guguzhen.api import GuGuZhen

dotenv.load_dotenv()

cookies = {
	"fyg2019_gameuid": os.getenv("UID"),
	"fyg2019_gamepw": os.getenv("PW"),
}

if __name__ == '__main__':
	api = GuGuZhen(cookies)
	print(api.get_gift())
