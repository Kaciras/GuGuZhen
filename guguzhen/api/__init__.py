import random
import re
import time
from dataclasses import dataclass

from lxml import etree

from .base import (
	FYGClient, ClickType, ReadType, VS, FygAPIError,
	ClientVersionError, LimitReachedError
)
from .beach import BeachApi
from .character import CharacterApi, Talent, TalentPanel, Card, EquipConfig, Role, Properties
from .gift import GiftApi, Gift, GiftType
from .items import (
	Equipment, Amulet, EquipAttr, AmuletAttr, EquipType,
	ItemApi, ItemsInfo, Item, Grade, RandomCard
)
from .pk import VS, PKInfo, PKApi, Player, Creep, CreepType, Trophy, PKRank, Action, Battle
from .wish import WishApi, WishInfo, WishBuffers

_safeid_param = re.compile(r"&sf=([0-9a-z]+)", re.MULTILINE)


@dataclass(eq=False)
class UserInfo:
	name: str			# 我的游戏名
	level: int			# 争夺等级
	couch: int			# 贝壳
	sand: int			# 星沙
	crystal: int		# 星晶


class GuGuZhen(FYGClient):
	"""
	咕咕镇网页 API 的封装。

	由于功能太多，部分 API 放在了子对象中：
		pk 			- 争夺战场
		wishing		- 许愿池
		character	- 我的角色（卡片和天赋）
		items		- 我的角色（武器装备）
		beach		- 海滩收获
		gift		- 好运奖励
	"""

	@staticmethod
	def rest():
		"""
		等待几秒，避免请求太快增加服务器压力，毕竟本程序是爬虫不是 DOS 攻击。
		"""
		time.sleep(random.uniform(0.8, 3))

	def get_version(self):
		"""查询当前咕咕镇版本的更新日期"""
		html = etree.HTML(self.get_page("/fyg_ulog.php"))
		return html.find("body/div/div[2]/div/div/div[2]/div[1]/h3").text

	def get_user(self):
		"""查询统计信息"""
		html = self.fyg_read(ReadType.User)
		lines = etree.HTML(html).findall("body/p/span")

		return UserInfo(
			lines[0].text,
			int(lines[1].text),
			int(lines[2].text),
			int(lines[3].text),
			int(lines[4].text),
		)

	def drop_quagmire(self, value: int):
		"""
		主站右边的泥潭，可以把自己不需要的 KFB 和贡献扔掉。

		value 参数可以是以下值：
			5	- 扔掉 5万KFB
			50	- 扔掉 50万KFB
			1	- 扔掉 1贡献
			10	- 扔掉 10万KFB
			600	- 扔掉 50万KFB + 10贡献
		"""
		url = self.forum + "/kf_drop.php"
		html = etree.HTML(self.get_page(url))

		href = html.find(".//table/tr[2]/td/a[1]").get("href")
		sf = _safeid_param.search(href).group(1)

		html = self.get_page(f"{url}?r={value}&sf={sf}")
		html = etree.HTML(html)

		prev = html.find(".//div[@id='alldiv']/div[3]/div[2]/div/br[3]")
		span = prev.getnext()
		if (span is None) or (span.tag != "span"):
			raise FygAPIError(prev.tail)

	@property
	def pk(self):
		return PKApi(self)

	@property
	def wishing(self):
		return WishApi(self)

	@property
	def gift(self):
		return GiftApi(self)

	@property
	def beach(self):
		return BeachApi(self)

	@property
	def items(self):
		return ItemApi(self)

	@property
	def character(self):
		return CharacterApi(self)
