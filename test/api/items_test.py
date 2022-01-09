def test_get_info(api, fyg_server):
	fyg_server.mock_res("ReadEquipments.html")

	repo = api.items.get_info()

	assert repo.size == 11

	fyg_server.verify_read(f="7")


def test_put_out(api, fyg_server):
	fyg_server.mock_res(content="ok")
	api.items.put_out(1234567)
	fyg_server.verify_click(c="22", id="1234567")

