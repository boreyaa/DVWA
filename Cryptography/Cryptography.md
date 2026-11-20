# Cryptography

这个模块演示的全是"密码学用错"，不是算法被破。四档对应四种典型错误：把编码当加密、分组模式选错、错误信息泄露、以及正确做法。

说明在前：这个模块我以读源码和推演为主，四档没有全部在本机跑通。下面每写一段都标了是实测还是资料推演，没跑通的不硬凑。

## 漏洞在哪

密码学误用不在某一行代码，而在选择和用法上。四种典型错误：

| 错误 | 表现 |
|---|---|
| 把编码当加密 | Base64、异或循环套一下就上线 |
| 分组模式选错 | 用 ECB，相同明文块产生相同密文块 |
| 错误信息泄露 | 解密失败时区分"填充错"与"校验错" |
| 只加密不校验 | 密文可被篡改，服务端照样解密使用 |

## 等级对照

| 等级 | 算法 | 错误 | 状态 |
|---|---|---|---|
| Low | XOR + Base64 | 把混淆当加密 | 逻辑推演，未完整复现 |
| Medium | AES-128-ECB | 分组独立、无 IV | 脚本验证过切分与拼接，伪造未提交 |
| High | AES-128-CBC | Padding Oracle | 原理推演，未用工具打通 |
| Impossible | AES-256-GCM | 正确做法 | 篡改后认证失败，已观察 |

## Low：XOR + Base64

| 项 | 内容 |
|---|---|
| 做法 | 明文异或密钥，再 Base64 |
| 问题 | 密钥短、重复使用、Base64 不提供任何安全性 |
| 还原 | Base64 解码后按密钥循环异或 |
| 密钥 | 资料给的是 `wachtwoord`，我未在本机核对 |

```python
import base64

token = "页面给出的 token"
key = b"wachtwoord"

cipher = base64.b64decode(token)
plain = bytes([cipher[i] ^ key[i % len(key)] for i in range(len(cipher))])
print(plain.decode(errors="ignore"))
```

CyberChef 等价操作：`From Base64` → `XOR` → 填 key。

密钥不知道也能恢复部分内容。异或满足 `密文 = 明文 XOR 密钥`，所以 `密钥 = 密文 XOR 明文`。猜到明文里有固定串（`user`、`role`）就能反推密钥片段，这叫已知明文攻击。

结论：异或不是不能用，但密钥短、重复用、可预测时等于没加密。

## Medium：AES-ECB 分组替换

| 项 | 内容 |
|---|---|
| 特点 | 每个 16 字节分组独立加密，不用 IV |
| 后果 | 相同明文块产生相同密文块，密文可搬运 |
| 攻击 | 把自己 token 里某一块换成管理员 token 的对应块 |
| 状态 | 切分与拼接脚本验证过，伪造 token 未实际提交 |

```python
import base64

raw = base64.b64decode("页面给出的 token")
for i in range(0, len(raw), 16):
    print(i // 16, raw[i:i+16].hex())
```

把多个用户的 token 并排切开，找哪一块在不同用户之间不同，那一块大概率存的就是身份或权限。然后拼接：

```python
import base64

u = base64.b64decode("普通用户 token")
a = base64.b64decode("管理员 token")

ub = [u[i:i+16] for i in range(0, len(u), 16)]
ab = [a[i:i+16] for i in range(0, len(a), 16)]

forged = ub.copy()
forged[1] = ab[1]
print(base64.b64encode(b"".join(forged)).decode())
```

ECB 的经典图示是加密企鹅图片，轮廓还在。用在 token 上，问题就是可以拼接伪造身份。

## High：CBC 与 Padding Oracle

| 项 | 内容 |
|---|---|
| 解密 | `P1 = Dec(C1) XOR IV`，`P2 = Dec(C2) XOR C1` |
| 关键性质 | 改前一块密文，就能控制当前块的明文 |
| Oracle | 服务端对 padding 是否正确给出不同响应 |
| 结论 | 每次能拿一位，一个块最多 16×256 次请求 |
| 状态 | 原理推演，未用 padbuster 打通 |

PKCS#7 填充规则是补几个字节就填几：

```text
缺 1 字节 → 01
缺 2 字节 → 02 02
整块都缺 → 10 × 16
```

攻击步骤：

| 步 | 动作 |
|---|---|
| 1 | 构造 `C0'`，暴力改最后一个字节，0x00 到 0xff |
| 2 | 某个值让 padding 合法为 `01`，服务端返回正常 |
| 3 | `I[15] = C0'[15] XOR 0x01`，拿到中间值 |
| 4 | `P1[15] = I[15] XOR C0[15]`，得到原文字节 |
| 5 | 目标改成 `02 02`，继续攻倒数第二位 |

工具层面有 padbuster：

```bash
padbuster <URL> <ciphertext> 16 -encoding 0
```

DVWA 这级的 token 还套了 Base64 与 IV，用工具前要把参数对齐：找到 token 与 IV、判断编码、确认两种响应的差异。

## Impossible：AES-256-GCM

| 特点 | 说明 |
|---|---|
| 认证加密 | 加密同时产生 tag，解密先验 tag |
| 随机 IV | 每次加密唯一 |
| 防篡改 | 改一个字节即认证失败 |
| 无 padding | Padding Oracle 天然不存在 |

自己可以验：拿 token 改任意一个字符提交，结果是认证失败，而不是像 High 那样区分 padding 对错。这个观察我做过。

## 容易记错的地方

- Base64 解出来是乱码不代表没解对，后面还有异或这一层。
- ECB 切块不一定从第一个字节开始，token 前面可能有前缀，先试几个偏移。
- `P = Dec(C) XOR 前一块`，`Dec(C)` 固定，所以改前一块就能控明文，这一点想通了 Padding Oracle 才通。
- 只加密不校验等于允许别人改密文，这是四档里最核心的一条。

## 怎么修

| 措施 | 作用 |
|---|---|
| 不自己设计加密 | 用标准库的标准模式 |
| 不用 ECB | 多块数据用 CBC 加随机 IV，或直接 GCM |
| 加密必配完整性校验 | AEAD 或加密后 HMAC |
| 解密失败统一报错 | 不区分填充错与校验错，否则就是 Oracle |
| IV 每次随机 | CBC 的 IV 可公开但必须随机 |
| 密钥管理 | 单独存放，不进代码、不与密文同处 |

## 参考

- 各级算法与模式参考 DVWA 官方文档与项目源码说明。
- Padding Oracle 部分参考 PKCS#7 填充标准与公开的 Oracle 攻击说明。
- 实测范围：ECB 切分拼接脚本、GCM 篡改后认证失败。其余为资料研读。
