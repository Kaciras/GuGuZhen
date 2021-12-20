from setuptools import setup

setup(
	name="guguzhen",
	version="1.0.0",
	description='咕咕镇自动化脚本',
	author="Kaciras",
	platforms='any',
	python_requires='>=3.10',
	install_requires=[
		"httpx",
		"lxml",
		"pytest",
		"pytest-httpx",
		"python-dotenv",
	],
)
