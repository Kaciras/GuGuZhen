import re
from dataclasses import dataclass
from typing import Literal

from lxml import etree

from .base import FYGClient, ReadType, LimitReachedError, ClickType

_gp = re.compile(r"(\d+)贝壳[\s+]+(\d+)星沙[\s+]+(\d+)件?装备[\s+]+(\d+)张?卡片[\s+]+([0-9.]+)%光环点数")

_gift_desc = re.compile(r"\s*([^+]+)\+([0-9.]+)\*(\d+)%")

_sand_cost = re.compile(r"消耗 <b>(\d+)</b> 星沙", re.MULTILINE)

GiftType = Literal["贝壳", "星沙", "装备", "卡片", "光环"]


@dataclass(frozen=True, slots=True)
class Gift:
	"""表示一个翻开的礼物"""

	type: GiftType		# 类型
	base: float			# 基本值
	ratio: float		# 倍率

	@property
	def value(self):
		return self.base * self.ratio

	def __str__(self):
		return f"{self.type}+{self.base}*{self.ratio:.0%}"


class GiftApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_pool(self):
		"""
		获取今日的奖池数据,包含总数和我的基本数值两项。

		【注意：光环的值】
		光环的单位是点数，比如 123.45% 光环将返回 123.45 而不是 1.2345，
		因为光环并不与其它数据做运算，它的百分比无意义。

		:return: (总共, 基本数值) 二元组
		"""
		html = self.api.get_page("/fyg_gift.php")
		html = etree.HTML(html)

		el = html.find('.//*[@id="giftinfo"]/div/h2')
		total = _gp.search(el.text)

		el = html.find('.//*[@id="giftinfo"]/div/h4')
		base = _gp.search(el.text)

		return  {
			"贝壳": int(total.group(1)),
			"星沙": int(total.group(2)),
			"装备": int(total.group(3)),
			"卡片": int(total.group(4)),
			"光环": float(total.group(5))
		}, {
			"贝壳": int(base.group(1)),
			"星沙": int(base.group(2)),
			"装备": int(base.group(3)),
			"卡片": int(base.group(4)),
			"光环": float(base.group(5))
		}

	def get_opened(self):
		"""
		获取所有已打开的礼物，返回 dict[编号，礼物信息] 字典
		"""
		html = self.api.fyg_read(ReadType.Gifts)
		html = etree.HTML(html)

		opened = {}
		for i, el in enumerate(html.iterfind(".//button")):
			match = _gift_desc.match(el.text)
			if match is None:
				continue
			opened[i] = Gift(
				match.group(1),
				float(match.group(2)),
				float(match.group(3)) / 100
			)

		return opened

	def open(self, index, use_sand=False):
		"""
		翻开一个礼物，如果免费次数用完且不使用星沙则抛异常。

		编号的排列为先竖后横：
			1	4	7	10
			2	5	8	11
			3	6	9	12

		:param index: 礼物的编号，从 1 开始
		:param use_sand: 是否使用星沙
		"""
		form = {
			"id": index,
		}
		if use_sand:
			form["gx"] = "1"

		res_text = self.api.fyg_click(ClickType.OpenGift, **form)

		match = _sand_cost.search(res_text)
		if match:
			raise LimitReachedError()
