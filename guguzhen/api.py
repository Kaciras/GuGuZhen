import json
import re
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
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
_sidp = re.compile(r"&safeid=([0-9a-z]+)", re.MULTILINE)
_gxp = re.compile(r"消耗 (\d+) 星沙", re.MULTILINE)


class ReadType(Enum):
	Beach = 1		 # 海滩装备
	Bag = 2			 # 海滩背包
	Talent = 5		 # 光环天赋
	Repository = 7   # 武器装备
	CardList = 8     # 角色卡片列表
	Character = 9    # 我的战斗信息
	Gifts = 10       # 抽奖
	Chips = 11		 # 筹码（不知道啥用）
	PK = 12			 # 争夺战场
	Statistics = 13  # 统计信息
	CardDetail = 18  # 卡片详情
	Wish = 19		 # 许愿池


class ClickType(Enum):
	OpenGift = 8	 # 点好运奖励的卡片
	Pillage = 16	 # 搜刮资源


class VS(Enum):
	Creeps = 1  # 打野
	Player = 2  # 打人


_z2e = {
	"贝壳": "conch",
	"星沙": "sand",
	"装备": "equipment",
	"卡片": "cards",
	"光环": "halo",
}


class LimitReachedError(Exception):

	def __init__(self):
		super().__init__("次数已达上限")


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

	@property
	def value(self):
		return self.base * self.ratio


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

	def get_page(self, path):
		r = self.client.get(path)
		r.raise_for_status()
		return etree.HTML(r.text)

	def fyg_read(self, type_, **kwargs):
		kwargs["f"] = str(type_.value)
		r = self.client.post("/fyg_read.php", data=kwargs)
		r.raise_for_status()
		return etree.HTML(r.text)

	def fyg_click(self, form):
		form["safeid"] = self.safe_id
		r = self.client.post("/fyg_click.php", data=form)
		r.raise_for_status()
		return r.text

	def fyg_v_intel(self, target,):
		form = {
			"id": target,
			"safeid": self.safe_id
		}
		self.client.post("/fyg_v_intel.php", data={"form": form})

	def get_gift_pool(self):
		html = self.get_page("/fyg_gift.php")
		el = html.xpath('//*[@id="giftinfo"]/div/h2')
		match = _gp.match(el[0].text)

		return GiftInfo(int(match.group(1)),
						int(match.group(2)),
						int(match.group(3)),
						int(match.group(4)),
						float(match.group(5)))

	def get_gift_cards(self):
		html = self.fyg_read(ReadType.Gifts)
		cards, index = {}, 0

		for el in html.iter():
			if el.tag != "button":
				continue
			index += 1
			match = _cp.match(el.text)
			if match is None:
				continue
			info = CardInfo(_z2e[match.group(1)], float(match.group(2)), int(match.group(3)))
			cards[index] = info

		return cards

	def open_gift(self, index, use_sand=False):
		form = {
			"c": "8",
			"id": index,
		}
		if use_sand:
			form["gx"] = "1"

		res_text = self.fyg_click(form)

		match = _gxp.search(res_text)
		if match:
			raise LimitReachedError()

	def get_version(self):
		html = self.get_page("/fyg_ulog.php")
		return html.xpath("/html/body/div/div[2]/div/div/div[2]/div[1]/h3")[0].text

	def get_pk_info(self):
		r = self.client.post("/fyg_read.php", data={"form": {"f": "12"}})
