# DVWA 靶场复现笔记

DVWA 十五个模块，每个模块从 Low 打到 Impossible，记录 payload、页面回显、卡住的地方和正确的修法。

靶场跑在本机 `127.0.0.1`，没有对任何真实站点发起过请求。

## 环境

| 项 | 值 |
|---|---|
| 靶场 | DVWA（phpStudy 集成环境） |
| PHP | 7.3.4 nts |
| 数据库 | MySQL |
| 系统 | Windows 10 |
| 抓包 | Burp Suite Pro 2025.9.4 |
| 代理 | Chrome → `127.0.0.1:8080` |

安全等级在 `DVWA Security` 页切换，页面地址 `http://127.0.0.1/dvwa/`。

## 模块

| 模块 | 练的内容 | 覆盖等级 |
|---|---|---|
| [SQL Injection](SQL%20Injection/SQL%20Injection.md) | 字符型与数字型、ORDER BY 判列、UNION 取数、注释截断 | Low–Impossible |
| [SQL Injection(Blind)](SQL%20Injection%28Blind%29/SQL%20Injection%28Blind%29.md) | 布尔盲注、时间盲注、逐位枚举 | Low–Impossible |
| [Brute Force](Brute%20Force/Brute%20Force.md) | Intruder 爆破、Hydra、High 的 token 宏 | Low–Impossible |
| [File Upload](File%20Upload/File%20Upload.md) | 直接传 shell、改 Content-Type、图片马、与文件包含组合 | Low–High |
| [File Inclusion](File%20Inclusion/File%20Inclusion.md) | 路径穿越、`php://filter` 读源码、双写绕过、`file://` 绕过前缀 | Low–Impossible |
| [Command Injection](Command%20Injection/Command%20Injection.md) | 连接符、黑名单缺口、有无回显 | Low–Impossible |
| [CSRF](CSRF/CSRF.md) | GET 改密、img 自动触发、Referer 绕过、token 被 XSS 带走 | Low–Impossible |
| [XSS(Reflected)](XSS%28Reflected%29/XSS-%28Reflected%29.md) | 三档绕过、输出上下文对应编码 | Low–Impossible |
| [XSS(Stored)](XSS%28Stored%29/XSS-%28Stored%29.md) | 持久触发、读 Cookie、改页面、Burp 绕 maxlength | Low–Impossible |
| [XSS(DOM)](XSS%28DOM%29/xss%28DOM%29.md) | source 与 sink、hash 不发给服务器 | Low–Impossible |
| [CSP Bypass](CSP%20Bypass/CSP%20Bypass.md) | 宽白名单、固定 nonce、JSONP callback | Medium–High 实测 |
| [CAPTCHA](CAPTCHA/CAPTCHA.md) | `step` 跳过、`passed_captcha` 伪造、硬编码后门 | Low–Medium 实测 |
| [Weak Sessions IDs](Weak%20Sessions%20IDs/Weak%20Sessions%20IDs.md) | 自增、时间戳、`md5(自增)`、Sequencer 看熵 | Low–Impossible |
| [Cryptography](Cryptography/Cryptography.md) | XOR+Base64、ECB 分组替换、CBC Padding Oracle | 部分推演 |
| [javascript attacks](javascript%20attacks/javascript%20attacks.md) | 前端 token 生成逻辑逆推 | Low–High |

## 每个文件的结构

统一五段，方便对照：

| 段落 | 内容 |
|---|---|
| 漏洞在哪 | 一句话定义 + 有问题的代码 |
| 等级对照 | 表：等级 / 防护 / 本机结果 |
| 各等级做法 | 表：项 / 内容 + payload 代码块 + 截图 |
| 容易记错的地方 | 4 到 5 条，具体到某一步 |
| 怎么修 | 表：措施 / 作用 |

## 三种 XSS 的分界

| 类型 | 数据流向 | 落库 | 触发 |
|---|---|---|---|
| 反射型 | 参数 → 同次响应 | 否 | 诱导点链接 |
| 存储型 | 提交 → 数据库 → 他人访问 | 是 | 打开页面即可 |
| DOM 型 | URL → 前端 JS → DOM | 否 | 诱导点链接，payload 可能不到服务器 |

## 关于"哪些真做过"

CSP 的 Low、CAPTCHA 的 High、Cryptography 的大部分，我标了"未跑通"并给出参考来源。这几处是读文档与源码得出的，不是打出来的。其余为实测。

标出来不是为了好看，是为了面试被追问细节时对得上。

## 免责

所有内容仅用于本地靶场学习与防御研究。请勿用于未授权的真实目标。
