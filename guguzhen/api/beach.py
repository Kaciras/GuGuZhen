import re
from datetime import timedelta

from lxml import etree

from .base import FYGClient, ReadType, ClickType, LimitReachedError, FygAPIError
from .items import parse_item_button

_time_re = re.compile(r"还有 (\d+) 分钟")


def _parse_drifting_item(buttons):
	id_and_item = []

	for button in buttons:
		onclick = button.get("onclick")
		if not onclick:
			continue
		item = parse_item_button(button)
		id_ = int(onclick[7:-1])
		id_and_item.append((id_, item))

	return id_and_item


class BeachApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_next_time(self):
		"""获取下次装备被冲上沙滩的时间"""
		text = self.api.get_page("fyg_beach.php")
		m = _time_re.search(text).group(1)
		return timedelta(minutes=int(m))

	def get_items(self):
		"""查看沙滩"""
		html = self.api.fyg_read(ReadType.Beach)
		html = etree.HTML(html)

		buttons = html.iterfind(".//button")
		return _parse_drifting_item(buttons)

	def clear(self):
		"""批量清理沙滩（清除史诗以下装备）"""
		self.api.fyg_click(ClickType.ClearBeach)

	def refresh(self):
		"""强制刷新，立即获得下一批随机装备"""
		self.api.fyg_click(ClickType.RefreshBeach)

	def pick(self, bc_id: int):
		"""
		捡起装备，装备必须在沙滩上。

		:param bc_id 装备在沙滩上的 ID
		"""
		text = self.api.fyg_click(ClickType.PickUp, id=bc_id)

		if text.startswith("背包已满") or text.startswith("卡片栏已满"):
			raise LimitReachedError(text)
		if not text.endswith("ok"):
			raise FygAPIError("拾取失败：" + text)

	def throw(self, bp_id: int):
		"""
		丢弃到沙滩，装备必须在背包中。

		:param bp_id 装备在背包中的 ID
		"""
		text = self.api.fyg_click(ClickType.Throw, id=bp_id)
		if not text.startswith("已将装备丢弃到沙滩"):
			raise FygAPIError("丢弃失败：" + text)
