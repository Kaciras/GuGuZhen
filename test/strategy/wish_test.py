from datetime import datetime
from unittest.mock import Mock

from pytest import fixture

from guguzhen.api import GuGuZhen, WishInfo, WishBuffers
from guguzhen.strategy import Wish


@fixture
def mock_api():
	return Mock(spec=GuGuZhen({}))


_buffers = WishBuffers(1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5)


def test_no_needed(mock_api):
	mock_api.wishing.get_info.return_value = WishInfo(
		datetime.max, 123000, 10, _buffers
	)

	Wish(9).run(mock_api)

	mock_api.wishing.wish.assert_not_called()
	mock_api.wishing.get_info.assert_called_once()


def test(mock_api):
	mock_api.wishing.get_info.side_effect = [WishInfo(
		datetime.max, 123000, 7, _buffers
	), WishInfo(
		datetime.max, 123000, 8, _buffers
	), WishInfo(
		datetime.max, 123000, 9, _buffers
	)]

	Wish(9).run(mock_api)

	assert mock_api.wishing.wish.call_count == 2
