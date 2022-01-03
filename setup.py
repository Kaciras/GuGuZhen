from setuptools import setup

setup(
	name="guguzhen",
	version="1.0.0",
	description='咕咕镇自动化脚本',
	author="Kaciras",
	platforms='any',
	python_requires='>=3.10',
	install_requires=[
		"colorama",
		"fire",
		"httpx[http2]",
		"inquirer",
		"browser_cookie3",
		"lxml",
		"pytest",
		"pytest-httpx",
	],
)
