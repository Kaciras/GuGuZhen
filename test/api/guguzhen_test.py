from guguzhen.api import GuGuZhen

def test_get_safeid(fyg_server):
	fyg_server.mock_res("index.html")

	api = GuGuZhen({})
	api.fetch_safeid()

	assert api.safe_id == "aaaaaa"

	fyg_server.verify("/fyg_index.php")


def test_get_version(fyg_server):
	fyg_server.mock_res("fyg_ulog.html")

	api = GuGuZhen({})
	version = api.get_version()

	assert version == "2021/10/28"
	fyg_server.verify("/fyg_ulog.php")


def test_get_user(fyg_server):
	fyg_server.mock_res("ReadUser.html")

	api = GuGuZhen({})
	user = api.get_user()

	assert user.name == "test"
	assert user.level == 166
	assert user.couch == 4810940
	assert user.sand == 57
	assert user.crystal == 0

	fyg_server.verify_read(f="13")
