import random
import time

from .base import FYGClient
from .beach import *
from .character import *
from .gift import *
from .items import *
from .pk import *
from .wish import *


@dataclass(eq=False)
class UserInfo:
	name: str		# 我的游戏名
	level: int		# 争夺等级
	couch: int		# 贝壳
	sand: int		# 星沙
	crystal: int	# 星晶


class GuGuZhen(FYGClient):

	@staticmethod
	def rest():
		"""
		等待几秒，避免请求太快增加服务器压力，毕竟本程序是爬虫不是 DOS 攻击。
		"""
		time.sleep(random.uniform(1, 4))

	def get_version(self):
		html = self.get_page("/fyg_ulog.php")
		return html.xpath("/html/body/div/div[2]/div/div/div[2]/div[1]/h3")[0].text

	def get_user(self):
		html = self.fyg_read(ReadType.User)
		lines = etree.HTML(html).xpath("/html/body/p/span")

		return UserInfo(
			lines[0].text,
			int(lines[1].text),
			int(lines[2].text),
			int(lines[3].text),
			int(lines[4].text),
		)

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
