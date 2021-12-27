import sys

from .beach import *
from .character import *
from .gift import *
from .pk import *
from .wish import *


class CheckVersion:

	def __init__(self, date):
		self.date = date

	def run(self, client):
		current = client.get_version()
		if current != self.date:
			logging.warning(f"版本不匹配，要求={self.date}，当前={current}")
			sys.exit()
