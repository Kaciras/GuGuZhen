import logging
import re
from enum import Enum
from http.cookiejar import CookieJar

from httpx import Client

_FORUM_ORIGIN = "https://bbs.9shenmi.com"

_GAME_ORIGIN = "https://www.guguzhen.com"

# 虽然咕咕镇没有反爬，但还是习惯模仿一下浏览器。
_HEADERS = {
	"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
	"X-Requested-With": "XMLHttpRequest",
	"Accept-Language": "zh-CN,en-US;q=0.7,en;q=0.3",
}

class ClientVersionError(Exception):
	"""与服务端版本不匹配"""


class FygAPIError(Exception):
	"""调用 API 时的参数无效"""


class LimitReachedError(Exception):
	"""达到了体力、星沙、格子不够等限制"""


# @formatter:off

class ReadType(Enum):
	Beach = 1			# 海滩装备
	Bag = 2				# 海滩背包
	Talent = 5			# 光环天赋
	Equipments = 7 		# 武器装备
	CardList = 8   		# 角色卡片列表
	Character = 9  		# 我的战斗信息
	Gifts = 10     		# 抽奖
	Chips = 11			# 筹码（不知道啥用）
	PK = 12				# 争夺战场
	User = 13			# 统计信息
	CardDetail = 18		# 卡片详情
	Wish = 19			# 许愿池
	ZbTip = 20			# 查询装备信息


class VS(Enum):
	Creep = 1		# 打野
	Player = 2		# 打人


class ClickType(Enum):
	PickUp = 1			# 获取沙滩上的装备
	PutOn = 3  			# 穿上装备
	SetTalent = 4		# 保存光环天赋
	SwitchCard = 5		# 装备卡片
	Throw = 7			# 丢弃到沙滩
	OpenGift = 8	 	# 点好运奖励的卡片
	Destroy = 9	 		# 销毁护身符
	LevelUp = 10	 	# 升级卡片
	DeleteCard = 11	 	# 销毁护身符
	RefreshBeach = 12   # 强制刷新海滩，每次 5 星沙
	Rejuvenate = 13		# 恢复体力到 100
	Rebuild = 13		# 重置卡片的加点
	Pillage = 16	 	# 搜刮资源
	Wish = 18	 		# 许愿
	ReWish = 19	 		# 重随许愿点
	ClearBeach = 20	 	# 批量清理沙滩
	PutIn = 21  		# 将物品移入仓库
	PutOut = 22  		# 将物品移入背包

# @formatter:on


_safeid_param = re.compile(r"&safeid=([0-9a-z]+)", re.MULTILINE)


class FYGClient:
	"""
	说实话我也不知道 fyg 是什么意思，可能指绯月Gal？
	"""

	def __init__(self, forum_origin: str = None,
				 game_origin: str = None,
				 cookies: CookieJar = None):
		"""
		:param forum_origin: 绯月 GalGame 网站的 Origin
		:param game_origin: 咕咕镇网站的 Origin
		:param cookies: Cookies 存储，用于外部导入和保存 Cookies
		"""
		self.safe_id = None
		self.forum = forum_origin or _FORUM_ORIGIN
		self.game = game_origin or _GAME_ORIGIN

		self.client = Client(
			http2=True,
			headers=_HEADERS,
			base_url=self.game,
			cookies=cookies,
			follow_redirects=True
		)

	def _check_safe_id(self):
		if self.safe_id is None:
			raise Exception("请先调用 connect()")
		return self.safe_id

	def _post(self, url, form=None):
		r = self.client.post(url, data=form)
		r.raise_for_status()
		return r.text

	def login(self, user: str, password: str):
		"""通过用户名和密码登录绯月论坛"""
		data = {
			"cktime": "31536000",
			"hideid": 0,
			"step": 2,
			"lgt": 1,
			"pwuser": user,
			"pwpwd": password,
		}
		text = self._post(self.forum + "/login.php", data)

		if "您已经顺利登录" not in text:
			raise FygAPIError("登录失败，请检查输入的信息。")

	def connect(self):
		"""
		抓取 safeid，顺便检测当前的 Cookies 是否有效，如果失效则尝试刷新。

		刷新可能需要较长的时间，也不知道是网络问题还是服务端限制。
		"""
		r = self.client.get("/fyg_index.php")
		r.raise_for_status()
		match = _safeid_param.search(r.text)

		if match is None:
			logging.info("当前 Cookies 无法登录，尝试刷新，这可能要一点时间。")
			r = self.client.get(self.forum + "/fyg_sjcdwj.php?go=play", timeout=15)
			r.raise_for_status()
			match = _safeid_param.search(r.text)

		if match:
			self.safe_id = match.group(1)
		else:
			raise FygAPIError("safeid 获取失败，请尝试重新登录论坛，或者程序出了 BUG")

	def get_page(self, path):
		r = self.client.get(path)
		r.raise_for_status()
		return r.text

	def fyg_read(self, type_, **kwargs):
		kwargs["f"] = str(type_.value)
		return self._post("/fyg_read.php", kwargs)

	def fyg_click(self, type_, **kwargs):
		kwargs["c"] = type_.value
		kwargs["safeid"] = self._check_safe_id()
		return self._post("/fyg_click.php", kwargs)

	def fyg_v_intel(self, target: VS):
		form = {
			"id": target.value,
			"safeid": self.safe_id
		}
		return self._post("/fyg_v_intel.php", form)
