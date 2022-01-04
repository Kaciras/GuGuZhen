def test_get_info(api, fyg_server):
	fyg_server.mock_res("ReadEquipments.html")

	repo = api.items.get_info()

	assert repo.size == 11

	fyg_server.verify_read(f="7")

