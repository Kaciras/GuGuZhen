import re
from datetime import datetime, timedelta

from lxml import etree

from .base import FYGClient, ReadType, ClickType, LimitReachedError, FygAPIError
from .items import Item, parse_item_button

_time_re = re.compile(r"还有 (\d+) 分钟")


class BeachApi:
	"""
	注意：沙滩的物品虽然也是用的 character.Item 类，但与物品栏中的物品 id 不同。
	"""

	def __init__(self, api: FYGClient):
		self.api = api

	def get_next_time(self):
		"""获取下次装备被冲上沙滩的时间，返回的是日期"""
		text = self.api.get_page("fyg_beach.php").text
		m = _time_re.search(text).group(1)
		return datetime.now() + timedelta(minutes=int(m))

	def get_items(self):
		"""查看沙滩"""
		html = self.api.fyg_read(ReadType.Beach)
		html = etree.HTML(html)

		buttons = html.xpath("//button")
		return list(map(parse_item_button, buttons))

	def clear(self):
		"""批量清理沙滩（清除史诗以下装备）"""
		self.api.fyg_click(ClickType.ClearBeach)

	def refresh(self):
		"""强制刷新，立即获得下一批随机装备"""
		self.api.fyg_click(ClickType.RefreshBeach)

	def pick(self, item):
		"""捡起装备"""
		if isinstance(item, Item):
			item = item.id
		text = self.api.fyg_click(ClickType.PickUp, id=item)

		if text.startswith("背包已满"):
			raise LimitReachedError("背包已满")
		if text != "ok":
			raise FygAPIError("拾取装备失败：" + text)

	def throw(self, item):
		"""丢弃到沙滩"""
		if isinstance(item, Item):
			item = item.id
		text = self.api.fyg_click(ClickType.Throw, id=item)

		if not text.startswith("已将装备丢弃到沙滩"):
			raise FygAPIError("丢弃失败：" + text)
