import logging
from enum import Enum

from .core import NopStrategy, AbstractStrategy
from .profile import Profile
from ..api import GuGuZhen, VS, PKInfo


class _Mode(Enum):
	Default = 0		# 野怪强度小于 5 时打野，大于 5 时打人，但进度小于 92 时也会打人。
	CreepFirst = 1	# 跟 Default 相似，但即便进度小于 92 也不会打人。
	PVPOnly = 2		# 只打人不打野。


_NO_CHANGE = NopStrategy()

logger = logging.getLogger("PK")

class PK(AbstractStrategy):
	"""
	自动玩争夺战场，该策略详细的说明见 play.py 中的注释。
	"""

	mode = _Mode

	def __init__(
			self,
			pve: Profile = _NO_CHANGE,
			pvp: Profile = _NO_CHANGE,
			mode=_Mode.Default):
		self.pve = pve
		self.pvp = pvp
		self.mode = mode

	def run(self, api: GuGuZhen):
		state = api.pk.get_info()
		action = self._start

		logger.info(f"开始争夺战场，初始状态：{state}")

		while action is not None:
			api.rest()
			action = action(state, api)

		logger.info(f"争夺战场完毕，结束状态：{state}")

	def _start(self, state: PKInfo, _):
		if self.mode == _Mode.PVPOnly:
			return self._pillage_player
		if self.mode == _Mode.CreepFirst:
			if state.strengthen < 5:
				return self._pillage_creep
			else:
				return self._pillage_player
		else:
			if state.strengthen < 5 and state.progress >= 92:
				return self._pillage_creep
			else:
				return self._pillage_player

	def _pillage_creep(self, state: PKInfo, api: GuGuZhen):
		if state.progress <= 95:
			return self._battle_creep
		if state.power < 10:
			return None

		api.pk.pillage()
		state.progress -= 1
		state.power -= 10

		return self._pillage_creep

	def _battle_creep(self, state: PKInfo, api: GuGuZhen):
		if state.power < 5:
			return None

		battle = api.pk.battle(VS.Creep)
		state.power -= 5

		if battle.is_win:
			state.progress += 4
			state.strengthen += 1
			return self._start
		else:
			state.progress -= 1
			return self._battle_creep

	def _pillage_player(self, state: PKInfo, api: GuGuZhen):
		if state.progress <= 89:
			return self._battle_player
		if state.power < 10:
			return None

		api.pk.pillage()
		state.progress -= 1
		state.power -= 10

		return self._pillage_player

	def _battle_player(self, state: PKInfo, api: GuGuZhen):
		if state.power < 5:
			return None

		battle = api.pk.battle(VS.Player)
		state.power -= 5

		if battle.is_win:
			state.progress += 10
			state.strengthen -= 5
			return self._start
		else:
			state.progress -= 5
			return self._battle_player
