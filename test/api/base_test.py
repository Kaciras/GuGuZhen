def test_get_safeid(api, fyg_server):
	fyg_server.mock_res("index.html")

	api.connect()

	assert api.safe_id == "aaaaaa"
	fyg_server.verify("/fyg_index.php")

