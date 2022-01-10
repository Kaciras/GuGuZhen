from unittest.mock import Mock, call

from pytest import fixture

from guguzhen.api import GuGuZhen, PKInfo, VS, PKRank, Battle
from guguzhen.strategy import PK


@fixture
def mock_api():
	return Mock(spec=GuGuZhen)


def assert_actions(mock_api, actions: str):
	index = 0

	for e in mock_api.pk.method_calls:
		if e == call.pillage():
			actual = "刮"
		elif e == call.battle(VS.Creep):
			actual = "野"
		elif e == call.battle(VS.Player):
			actual = "人"
		else:
			continue

		expect= actions[index]
		index += 1
		if actual != expect:
			raise AssertionError(f"第{index}个动作错误，预期：{expect}，实际：{actual}")

	assert index == len(actions), "预期的动作没有执行完"


def test_creep_first(mock_api):
	info = PKInfo(PKRank.A, 89, 100, 0)
	mock_api.pk.battle.return_value = Battle(None, None, True, ())
	mock_api.pk.get_info.return_value = info

	PK(None, None, PK.mode.CreepFirst).run(mock_api)

	assert_actions(mock_api, "野野刮刮野刮刮刮刮野刮刮")
	assert info == PKInfo(PKRank.A, 97, 0, 4)

