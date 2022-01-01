def test_pick_card(api, fyg_server):
	"新的卡片已放入你的卡片栏，请查看。ok"


def test_get_beach(api, fyg_server):
	fyg_server.mock_res("ReadBeach.html")

	items = api.beach.get_items()

	assert len(items) == 11
	fyg_server.verify_read(f="1")

