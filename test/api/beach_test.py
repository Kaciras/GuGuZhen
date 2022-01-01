from guguzhen.api import GuGuZhen


def test_pick_card():
	"新的卡片已放入你的卡片栏，请查看。ok"


def test_get_beach(fyg_server):
	fyg_server.mock_res("ReadBeach.html")

	api = GuGuZhen({})
	items = api.beach.get_items()

	fyg_server.verify_read(f="1")

	assert len(items) == 11

