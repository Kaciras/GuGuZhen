from unittest.mock import Mock, call

from pytest import fixture

from guguzhen.api import GuGuZhen, Gift
from guguzhen.strategy import GetGift, GiftSandRule

total = {
	"贝壳": 408870,
	"星沙": 22,
	"装备": 34,
	"卡片": 1,
	"光环": 4.51
}


@fixture
def mock_api():
	return Mock(spec=GuGuZhen)


def test_open_free(mock_api):
	mock_api.gift.get_pool.return_value = (total, total)
	mock_api.gift.get_opened.return_value = {}

	GetGift().run(mock_api)

	mock_api.gift.open.assert_called_once_with(1, False)


def test_not_open_if_no_free(mock_api):
	mock_api.gift.get_pool.return_value = (total, total)
	mock_api.gift.get_opened.return_value = {1: Gift("贝壳", 68532, 3.63)}

	GetGift().run(mock_api)

	mock_api.gift.open.assert_not_called()


def test_rule_value(mock_api):
	action = GetGift([GiftSandRule("卡片", 2, 20), GiftSandRule("光环", 2, 20)])
	mock_api.gift.get_pool.return_value = (total, total)

	mock_api.gift.get_opened.side_effect = [
		{1: Gift("贝壳", 68532, 3.63)},
		{1: Gift("贝壳", 68532, 3.63), 2: Gift("光环", 2, 1.23)},
		{1: Gift("贝壳", 68532, 3.63), 2: Gift("光环", 2, 1.0), 3: Gift("光环", 2.1, 1.23)},
	]

	action.run(mock_api)

	mock_api.gift.open.assert_has_calls([call(2, True), call(3, True)])


def test_rule_sand_limit(mock_api):
	action = GetGift([GiftSandRule("光环", 2, 4)])
	mock_api.gift.get_pool.return_value = (total, total)

	mock_api.gift.get_opened.side_effect = [
		{1: Gift("贝壳", 68532, 3.63)},
		{1: Gift("贝壳", 68532, 3.63), 2: Gift("光环", 2, 1.23)},
	]

	action.run(mock_api)

	mock_api.gift.open.assert_called_once_with(2, True)
