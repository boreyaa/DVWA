# DVWA 靶场复现笔记

DVWA 是我拿来练手的第一套 Web 靶场。我用本机 phpStudy 起服务，Burp Suite 抓包，把 15 个模块从 Low 一路打到 Impossible，每个模块留下 payload、页面回显和当时的判断过程。

这些东西不是看完教程抄的步骤，是我自己一条条打过去、卡住、再想明白的记录。所以里面会有"第一次以为是这样，其实不是"的内容。

## 环境

| 项 | 值 |
|---|---|
| 靶场 | DVWA（phpStudy 集成环境） |
| PHP | 7.3.4 nts |
| 数据库 | MySQL |
| 系统 | Windows 10 |
| 抓包 | Burp Suite Pro 2025.9.4 |
| 浏览器 | Chrome + 代理 127.0.0.1:8080 |

页面地址固定在 `http://127.0.0.1/dvwa/`，安全等级在 `DVWA Security` 页切换。

## 15 个模块

| 模块 | 我练的东西 | 记录 |
|---|---|---|
| SQL Injection | 字符型和数字型的区别、ORDER BY 判列、UNION 取数、注释截断 | [SQL Injection](SQL%20Injection/SQL%20Injection.md) |
| SQL Injection(Blind) | 布尔盲注、时间盲注、substr 逐字符、ASCII 判断 | [SQL Injection(Blind)](SQL%20Injection%28Blind%29/SQL%20Injection%28Blind%29.md) |
| Brute Force | Intruder 爆破、Hydra 命令行、high 的 token 宏 | [Brute Force](Brute%20Force/Brute%20Force.md) |
| File Upload | 直接传 shell、改 Content-Type、图片马、和文件包含组合 | [File Upload](File%20Upload/File%20Upload.md) |
| File Inclusion | 路径穿越、php://filter 读源码、双写绕过、file:// 绕过白名单 | [File Inclusion](File%20Inclusion/File%20Inclusion.md) |
| Command Injection | 命令连接符、黑名单绕过、无回显怎么判 | [Command Injection](Command%20Injection/Command%20Injection.md) |
| CSRF | GET 改密、img 自动触发、Referer 绕过、Token + XSS 组合 | [CSRF](CSRF/CSRF.md) |
| XSS(Reflected) | 反射型三档绕过、输出编码为什么是正解 | [XSS(Reflected)](XSS%28Reflected%29/XSS-%28Reflected%29.md) |
| XSS(Stored) | 存储型、改 Cookie、改页面、Burp 绕 maxlength | [XSS(Stored)](XSS%28Stored%29/XSS-%28Stored%29.md) |
| XSS(DOM) | source 和 sink、hash 不发给服务器、白名单为什么也拦不住 | [XSS(DOM)](XSS%28DOM%29/xss%28DOM%29.md) |
| CSP Bypass | 宽白名单、固定 nonce、JSONP callback | [CSP Bypass](CSP%20Bypass/CSP%20Bypass.md) |
| CAPTCHA | step 跳过、passed_captcha 伪造、high 的硬编码后门 | [CAPTCHA](CAPTCHA/CAPTCHA.md) |
| Weak Sessions IDs | 自增、时间戳、md5(自增)、Burp Sequencer 看熵 | [Weak Sessions IDs](Weak%20Sessions%20IDs/Weak%20Sessions%20IDs.md) |
| Cryptography | XOR+Base64、ECB 分组替换、CBC Padding Oracle | [Cryptography](Cryptography/Cryptography.md) |
| JavaScript Attacks | 前端 token 生成逻辑逆推、ROT13/MD5/SHA256 | [javascript attacks](javascript%20attacks/javascript%20attacks.md) |

## 三种 XSS 的区别

一开始我三个模块是分开练的，练完才分清楚。

- **反射型**：参数进来，同一次响应里就回显出去。不落库，要靠人点链接。
- **存储型**：内容先进数据库，别人访问页面才触发。不用点链接，危害最大。
- **DOM 型**：后端可能完全没参与，前端 JS 从 `location` 取参数、往 `innerHTML` 里塞。看流量看不到 payload，因为 `#` 后面的东西根本不发给服务器。

## 每个文件怎么写的

固定几块，方便以后回来查：

1. 这个模块到底哪里出的问题（一句话 + 有漏洞的那行代码）
2. Low / Medium / High 三档分别怎么打，用什么 payload，页面回显是什么
3. Impossible 为什么打不进去
4. 我卡住的地方
5. 正确的修法

## 说明

- 所有操作都在本机 `127.0.0.1` 的靶场里做，没有对任何真实站点发起过请求。
- 有几处我引用了公开资料（CSP 白名单、CAPTCHA 后门、Cryptography 的算法模式），文件里写明了"看了资料，没在本机跑通"，跟实测的部分分开标。面试被问到不会答错。
- 图片在原目录下，文件名没改，可以直接对照。
