import logging

from guguzhen.api import GuGuZhen, VS, PKInfo
from guguzhen.strategy import CharacterPreset


class PK:
	"""
	自动玩争夺战场，该策略详细的说明见 play.py 中的注释。
	"""

	def __init__(self, pve: CharacterPreset, pvp: CharacterPreset):
		self.pve = pve
		self.pvp = pvp

	def run(self, api: GuGuZhen):
		state = api.pk.get_info()
		action = self._start

		while action is not None:
			api.rest()
			action = action(state, api)

		logging.info("争夺战场结束")

	def _start(self, state: PKInfo, _):
		if state.strengthen < 5:
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
