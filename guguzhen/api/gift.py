import re
from dataclasses import dataclass
from typing import Literal

from .base import FYGClient, ReadType, LimitReachedError, ClickType

_gp = re.compile(r"今日奖池中共有 (\d+)贝壳 \+ (\d+)星沙 \+ (\d+)装备 \+ (\d+)卡片 \+ ([0-9.]+)%光环点数")
_cp = re.compile(r"\s*([^+]+)\+([0-9.]+)\*(\d+)%")
_gxp = re.compile(r"消耗 (\d+) 星沙", re.MULTILINE)

GiftType = Literal["贝壳", "星沙", "装备", "卡片", "光环"]


@dataclass(eq=False, slots=True)
class PKInfo:
	rank: str
	progress: int
	fatigue: int
	creepsEnhance: int


@dataclass(eq=False, slots=True)
class CardInfo:
	type: GiftType
	base: float
	ratio: float

	@property
	def value(self):
		return self.base * self.ratio


class GiftApi:

	def __init__(self, api: FYGClient):
		self.api = api

	def get_pool(self):
		html = self.api.get_page("/fyg_gift.php")
		el = html.xpath('//*[@id="giftinfo"]/div/h2')
		match = _gp.match(el[0].text)

		return {
			"贝壳": int(match.group(1)),
			"星沙": int(match.group(2)),
			"装备": int(match.group(3)),
			"卡片": int(match.group(4)),
			"光环": float(match.group(5))
		}

	def get_cards(self):
		html = self.api.fyg_read(ReadType.Gifts)
		cards, index = {}, 0

		for el in html.iter():
			if el.tag != "button":
				continue
			index += 1
			match = _cp.match(el.text)
			if match is None:
				continue
			info = CardInfo(match.group(1), float(match.group(2)), float(match.group(3)) / 100)
			cards[index] = info

		return cards

	def open(self, index, use_sand=False):
		form = {
			"id": index,
		}
		if use_sand:
			form["gx"] = "1"

		res_text = self.api.fyg_click(ClickType.OpenGift, **form)

		match = _gxp.search(res_text)
		if match:
			raise LimitReachedError()


