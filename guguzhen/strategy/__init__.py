from .beach import PickBeach, EC, CardCleaner
from .character import CharacterPreset
from .gift import GetGift, GiftSandRule
from .pk import PK
from .wish import Wish
from ..api import ClientVersionError, GuGuZhen


class CheckVersion:

	def __init__(self, date: str):
		self.date = date

	def run(self, api: GuGuZhen):
		current = api.get_version()
		if current != self.date:
			raise ClientVersionError(f"版本不匹配，要求={self.date}，当前={current}")
