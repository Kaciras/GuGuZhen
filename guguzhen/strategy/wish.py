import logging

from .core import AbstractStrategy
from ..api import GuGuZhen

logger = logging.getLogger("Wish")


class Wish(AbstractStrategy):

	def __init__(self, times: int):
		self.times = times

	def run(self, api: GuGuZhen):
		info = api.wishing.get_info()
		count = self.times - info.point

		while self.times > info.point:
			api.rest()
			api.wishing.wish()
			info = api.wishing.get_info()

		if count > 0:
			logger.info(f"许愿了 {count} 次")
		else:
			logger.info("无需许愿")
