import abc

from ..api import GuGuZhen, ClientVersionError


class AbstractStrategy(abc.ABC):
	"""
	策略指的是自动脚本的一个单元，执行一系列动作，比如自动 PK，换装等等。
	"""

	def run(self, api: GuGuZhen):
		"""运行该策略"""


class NopStrategy(AbstractStrategy):
	"""什么都不做，可用于一些场合默认参数等等"""

	def run(self, _: GuGuZhen): pass


class CheckVersion(AbstractStrategy):
	"""检查游戏版本，如果不符合则抛出异常中止执行"""

	def __init__(self, date: str):
		self.date = date

	def run(self, api: GuGuZhen):
		current = api.get_version()
		if current != self.date:
			raise ClientVersionError(f"版本不匹配，要求={self.date}，当前={current}")
