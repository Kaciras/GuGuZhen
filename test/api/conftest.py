from os import PathLike
from pathlib import Path
from urllib.parse import parse_qsl

from pytest import fixture
from pytest_httpx import HTTPXMock

from guguzhen.api import GuGuZhen

_fixtures = Path(__file__).parent.parent.joinpath("fixtures")

_safe_id = "abc123"

_api_instance = GuGuZhen()


@fixture
def api():
	_api_instance.safe_id = _safe_id
	return _api_instance


@fixture
def fyg_server(httpx_mock):
	return FYGServerMock(httpx_mock)


class FYGServerMock:
	"""
	简单的 Mock 请求封装，让请求相关的准备和断言一行就能搞定。
	"""

	def __init__(self, httpx_mock: HTTPXMock):
		self.httpx_mock = httpx_mock

	def mock_res(
			self,
			filename: PathLike = None,
			enc="utf8",
			content: str = None
	):
		if filename:
			html = _fixtures.joinpath(filename).read_text(enc)
		elif content:
			html = content
		else:
			raise TypeError("至少得有一个内容参数")

		self.httpx_mock.add_response(html=html)

	def verify(self, path, method="GET", **kwargs):
		request = self.httpx_mock.get_request()
		form = request.content.decode()

		assert request.method == method
		assert request.url.path == path
		assert dict(parse_qsl(form)) == kwargs

	def verify_read(self, **kwargs):
		self.verify("/fyg_read.php", "POST", **kwargs)

	def verify_click(self, **kwargs):
		kwargs["safeid"] = _safe_id
		self.verify("/fyg_click.php", "POST", **kwargs)
