import json
import re
from enum import Enum
from pathlib import Path
from typing import Literal

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

Role = Literal["梦", "默", "薇", "艾", "冥", "琳", "伊", "命", "野怪"]


class LimitReachedError(Exception):

	def __init__(self):
		super().__init__("次数已达上限")


# @formatter:off

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


class VS(Enum):
	Creeps = 1		 # 打野
	Player = 2		 # 打人


class ClickType(Enum):
	PickUp = 1			# 获取沙滩上的装备
	SetHalo = 4			# 保存光环天赋
	SwitchCard = 5		# 装备卡片
	Throw = 7			# 丢弃到沙滩
	OpenGift = 8	 	# 点好运奖励的卡片
	RefreshBeach = 12   # 强制刷新海滩，每次 5 星沙
	Pillage = 16	 	# 搜刮资源
	ClearBeach = 20	 	# 批量清理沙滩

# @formatter:on


_sidp = re.compile(r"&safeid=([0-9a-z]+)", re.MULTILINE)


class FYGClient:
	"""
	说实话我也不知道 fyg 是什么意思。
	"""

	def __init__(self, login_info, host=_HOST):
		self.safe_id = None

		try:
			with _STORE.open() as fp:
				cookies = Cookies(json.load(fp))
		except FileNotFoundError:
			cookies = Cookies(login_info)

		self.client = Client(
			http2=True,
			headers=_HEADERS,
			base_url=host,
			cookies=cookies
		)

	def _check_safe_id(self):
		if self.safe_id is None:
			raise Exception("请先调用 fetch_safeid()")
		return self.safe_id

	def save_cookies(self):
		_STORE.parent.mkdir(exist_ok=True)
		with _STORE.open("w") as fp:
			values = dict(self.client.cookies)
			json.dump(values, fp)

	def fetch_safeid(self):
		r = self.client.get("/fyg_index.php")
		self.safe_id = _sidp.search(r.text).group(1)

	def get_page(self, path):
		r = self.client.get(path)
		r.raise_for_status()
		return etree.HTML(r.text)

	def fyg_read(self, type_, **kwargs):
		kwargs["f"] = str(type_.value)
		r = self.client.post("/fyg_read.php", data=kwargs)
		r.raise_for_status()
		return r.text

	def fyg_click(self, type_, **kwargs):
		kwargs["c"] = type_.value
		kwargs["safeid"] = self._check_safe_id()

		r = self.client.post("/fyg_click.php", data=kwargs)
		r.raise_for_status()
		return r.text

	def fyg_v_intel(self, target: VS):
		form = {
			"id": target.value,
			"safeid": self.safe_id
		}
		self.client.post("/fyg_v_intel.php", data=form)
