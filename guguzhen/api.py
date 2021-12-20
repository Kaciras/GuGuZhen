import json
import re
from dataclasses import dataclass
from pathlib import Path

from httpx import Cookies, Client
from lxml import etree

_HOST = "https://www.guguzhen.com"

_STORE = Path("data/cookies.json")

# 虽然咕咕镇没有反爬，但还是习惯模仿一下浏览器。
_HEADERS = {
	"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
	"X-Requested-With": "XMLHttpRequest",
	"Accept-Language": "zh-CN,en-US;q=0.7,en;q=0.3",
}

_gp = re.compile(r"今日奖池中共有 (\d+)贝壳 \+ (\d+)星沙 \+ (\d+)装备 \+ (\d+)卡片 \+ ([0-9.]+)%光环点数")
_cp = re.compile(r"\s*([^+]+)\+([0-9.]+)\*(\d+)%")
_sidp = re.compile(r"&safeid=([0-9a-z]+)")
_gxp = re.compile(r"消耗 (\d+) 星沙")


class LimitReachedError(Exception):

	def __init__(self, sand=None):
		super().__init__("次数已达上限")
		self.sand = sand


@dataclass(eq=False, slots=True)
class GiftInfo:
	conch: int
	sand: int
	equipment: int
	cards: int
	halo: float


@dataclass(eq=False, slots=True)
class PKInfo:
	rank: str
	progress: int
	fatigue: int
	creepsEnhance: int


@dataclass(eq=False, slots=True)
class CardInfo:
	type: str
	base: float
	ratio: int


class GuGuZhen:

	def __init__(self, login_info, host=_HOST):
		self.safe_id = None

		try:
			with _STORE.open() as fp:
				cookies = Cookies(json.load(fp))
		except FileNotFoundError:
			cookies = Cookies(login_info)

		self.client = Client(headers=_HEADERS, base_url=host, cookies=cookies)

	def save_cookies(self):
		_STORE.parent.mkdir(exist_ok=True)
		with _STORE.open("w") as fp:
			values = dict(self.client.cookies)
			json.dump(values, fp)

	def fetch_safeid(self):
		r = self.client.get("/fyg_index.php")
		self.safe_id = _sidp.match(r.text).group(1)

	def get_gift_pool(self):
		r = self.client.get("/fyg_gift.php")
		el = etree.HTML(r.text).xpath('//*[@id="giftinfo"]/div/h2')
		match = _gp.match(el[0].text)

		return GiftInfo(int(match.group(1)),
						int(match.group(2)),
						int(match.group(3)),
						int(match.group(4)),
						float(match.group(5)))

	def get_gift_cards(self):
		r = self.client.post("/fyg_read.php", data={"form": {"f": "10"}})
		cards, index = [], 0

		for el in etree.HTML(r.text).iter():
			if el.tag != "button":
				continue
			index += 1
			match = _cp.match(el.text)
			if match is None:
				continue
			info = CardInfo(match.group(1), float(match.group(2)), int(match.group(3)))
			cards.append(info)

		return cards

	def open_gift(self, index, sand=False):
		form = {
			"safeid": self.safe_id,
			"c": "8",
			"id": str(index),
		}

		if sand:
			form["gx"] = "1"

		r = self.client.post("/fyg_click.php", data={"form": form})
		match = _gxp.match(r.text)
		if match:
			raise LimitReachedError(int(match.group(1)))

	def get_version(self):
		r = self.client.get("/fyg_ulog.php")
		html = etree.HTML(r.text)
		return html.xpath("/html/body/div/div[2]/div/div/div[2]/div[1]/h3")[0].text

	def get_pk_info(self):
		r = self.client.post("/fyg_read.php", data={"form": {"f": "12"}})
