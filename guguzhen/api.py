import httpx
from lxml import etree
import re
from dataclasses import dataclass

_HOST = "https://www.guguzhen.com"

# 虽然咕咕镇没有反爬，但还是习惯模仿一下浏览器。
_HEADERS = {
	"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
	"X-Requested-With": "XMLHttpRequest",
	"Accept-Language": "zh-CN,en-US;q=0.7,en;q=0.3",
}

_gp = re.compile("今日奖池中共有 (\\d+)贝壳 \\+ (\\d+)星沙 \\+ (\\d+)装备 \\+ (\\d+)卡片 \\+ ([0-9.]+)%光环点数")


@dataclass(eq=False, slots=True)
class GiftInfo:
	conch: int
	sand: int
	equipment: int
	cards: int
	halo: float


class GuGuZhen:

	def __init__(self, cookies):
		self.client = httpx.Client(headers=_HEADERS,
								   base_url=_HOST,
								   cookies=httpx.Cookies(cookies))

	def get_gift(self):
		res = self.client.get("/fyg_gift.php")
		el = etree.HTML(res.text).xpath('//*[@id="giftinfo"]/div/h2')
		match = _gp.match(el[0].text)

		return GiftInfo(int(match.group(1)),
						int(match.group(2)),
						int(match.group(3)),
						int(match.group(4)),
						float(match.group(5)))

	def get_version(self):
		r = self.client.get("https://www.guguzhen.com/fyg_ulog.php")
		html = etree.HTML(r.text)
		return html.xpath("/html/body/div/div[2]/div/div/div[2]/div[1]/h3")[0].text
