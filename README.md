# GuGuZhen

[![Test](https://github.com/Kaciras/GuGuZhen/actions/workflows/test.yml/badge.svg)](https://github.com/Kaciras/GuGuZhen/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Kaciras/GuGuZhen/branch/master/graph/badge.svg?token=OQ13CHUQ12)](https://codecov.io/gh/Kaciras/GuGuZhen)

**本项目还未完成**

[咕咕镇](https://www.guguzhen.com)小游戏的自动化脚本。

# 使用

## 登录

要玩游戏，首先得登录。本项目支持两种登录方式，成功后 Cookies 会保存在 `data/cookies.txt`，下次无需再登录。

使用密码：

```shell
python main.py login <用户名> <密码>
```

如果在浏览器中登录过，还可以直接复制浏览器的 Cookies：

```shell
python main.py clone
```

## 自动游戏脚本

本项目的主要功能就是自动玩游戏，这部分内容较多请见：[GET_STARTED.md](doc/GET_STARTED.md)

## API

自带的一些自动操作可能无法满足需求，对此本项目也提供了低层的 API 封装，可以用来编写自己的程序。这部分功能在 `guguzhen.api` 模块中，文档见源码。

使用示例：

```python
from guguzhen.api import *

# 创建一个到咕咕镇的连接。
api = GuGuZhen()

# 使用密码登录。
api.login("foobar", "password123")

# 检查和刷新（如果需要）Cookies。
api.connect()

# 查看所有翻开的好运奖励。
opened = api.gift.get_opened()

# 如果今日还没有翻过，就翻开第二张。
if len(opened) == 0:
    api.gift.open(2)
```

# 常见问题

## 中断与一致性

由于一些不可抗力（比如网络问题）可能导致自动游戏脚本中止，此时可以简单地重新运行。本项目里的所有的策略都可以中断，然后重试直到成功，跟一次运行成功的效果一样。

**请注意在自动进行游戏的同时不能上网页玩，或者同时运行两个脚本玩一个号**，这会造成不一致的状态。如果要手动上网页玩，请避开脚本的运行时间。
