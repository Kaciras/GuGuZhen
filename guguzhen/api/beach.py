import re
from datetime import datetime, timedelta

from lxml import etree

from .base import FYGClient, ReadType, ClickType
from .character import Item

_time_re = re.compile(r"还有 (\d+) 分钟")


class BeachApi:

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
		self.api.fyg_click(ClickType.PickUp, id=item)

	def throw(self, item):
		"""丢弃到沙滩"""
		if isinstance(item, Item):
			item = item.id
		self.api.fyg_click(ClickType.Throw, id=item)
