import logging

from guguzhen.api import GuGuZhen


class Wish:

	def __init__(self, times: int):
		self.times = times

	def run(self, api: GuGuZhen):
		info = api.wishing.get_info()
		count = self.times > info.point

		while self.times > info.point:
			api.wishing.wish()
			info = api.wishing.get_info()
			api.rest()

		logging.info(f"许愿了 {count} 次")
