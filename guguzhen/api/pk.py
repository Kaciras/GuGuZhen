from .base import FYGClient


class PKApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_info(self):
		r = self.api.post("/fyg_read.php", data={"f": "12"})
