from .beach import *
from .character import *
from .gift import *
from .pk import *
from .wish import *
from ..api.base import ClientVersionError


class CheckVersion:

	def __init__(self, date: str):
		self.date = date

	def run(self, api: GuGuZhen):
		current = api.get_version()
		if current != self.date:
			raise ClientVersionError(f"版本不匹配，要求={self.date}，当前={current}")
