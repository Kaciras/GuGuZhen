from guguzhen.api import GuGuZhen


def test_get_info(fyg_server):
	fyg_server.mock_res("ReadRepository.html")

	api = GuGuZhen({})
	repo = api.items.get_info()

	assert repo.size == 11

	fyg_server.verify_read(f="7")

