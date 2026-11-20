# Cryptography

这个模块演示的是"密码学用错"，不是算法被破。四档对应四种典型错误，从"把编码当加密"一路到正确的认证加密。

先说明一句：这个模块我主要以读源码和算法推演为主，本机没有把四档全部跑通。下面的状态标注里写清了哪些是我实测的、哪些是看资料推出来的。写这份笔记的目的不是凑一个"通关记录"，是把四种错误分清楚，面试被问到能答上来。

四档对应的算法：

| 等级 | 算法 | 错误类型 |
|---|---|---|
| Low | XOR + Base64 | 把编码/混淆当加密 |
| Medium | AES-128-ECB | 分组模式选错，无 IV |
| High | AES-128-CBC | Padding Oracle，错误信息泄露 |
| Impossible | AES-256-GCM | 认证加密，正确做法 |

## Low：XOR + Base64

页面给一个 token，开发者的想法是"我异或一下再 Base64，别人看不懂了"。

问题有三个：密钥短、密钥重复使用、Base64 只是编码不提供任何安全性。

还原步骤：

1. Base64 解码，拿到字节串
2. 用密钥循环异或还原

```python
import base64

token = "页面里给出的 token"
key = b"wachtwoord"          # 资料里给出的固定密钥，我没在本机核对过

cipher = base64.b64decode(token)
plain = bytes([cipher[i] ^ key[i % len(key)] for i in range(len(cipher))])
print(plain.decode(errors="ignore"))
```

CyberChef 也能做：`From Base64` → `XOR` → 填 key。

密钥不知道怎么办？异或有个性质：`密文 = 明文 XOR 密钥`，所以 `密钥 = 密文 XOR 明文`。只要猜到明文里有一段固定内容（比如 `"user"`、`"role"`），就能反推密钥片段。这就是已知明文攻击。

这一级的结论一句话：**异或不是不能用，但密钥短、重复用、可预测的时候等于没加密**。自己设计加密算法基本都是这个结局。

状态：算法和脚本逻辑我自己推过，token 的实际还原没有在本机完成（页面 challenge 格式与资料里的版本不完全一致）。

## Medium：AES-ECB 分组替换

ECB 的特点是每个 16 字节分组独立加密，同样的明文块永远得到同样的密文块，也没有 IV。

```
明文块1 → 密文块1
明文块2 → 密文块2
明文块3 → 密文块3
```

后果是密文可以被随意搬运。攻击者拿到自己的 token 和管理员的 token，就能把管理员 token 里"权限"那一块剪切下来，拼进自己的 token。

先按 16 字节切开看结构：

```python
import base64

token = "页面里的 token"
raw = base64.b64decode(token)

for i in range(0, len(raw), 16):
    print(i // 16, raw[i:i+16].hex())
```

输出类似：

```
0 8f2a1c...
1 7b9d3e...
2 cc45ab...
```

把多个 token 并排切，找哪一块在不同用户之间不同——那一块大概率存的就是身份或权限。然后拼接：

```python
import base64

user_raw  = base64.b64decode("普通用户的 token")
admin_raw = base64.b64decode("管理员的 token")

u = [user_raw[i:i+16]  for i in range(0, len(user_raw), 16)]
a = [admin_raw[i:i+16] for i in range(0, len(admin_raw), 16)]

forged = u.copy()
forged[1] = a[1]                 # 把第 2 块换成管理员的

print(base64.b64encode(b"".join(forged)).decode())
```

生成的 token 提交回去，权限就变了。

经典图示是 ECB 加密企鹅图片，轮廓还在，就是因为相同像素块产生相同密文块。用在 token 上，问题就是可以拼接伪造。

状态：分组切分和拼接脚本我写过并验证过逻辑，实际提交伪造 token 这一步受页面 token 格式限制，没有完整跑通。

## High：CBC 与 Padding Oracle

CBC 引了 IV，每个明文块和前一块密文异或，比 ECB 安全。但它有个前提：解密失败时不能告诉外面"为什么失败"。

CBC 解密：

```
P1 = Dec(C1) XOR IV
P2 = Dec(C2) XOR C1
P3 = Dec(C3) XOR C2
```

关键性质：改前一块密文，就能控制当前块的明文，因为两者是异或关系。

### Padding 是什么

AES 分组固定 16 字节，明文不满要补。PKCS#7 规则是补几个字节就填几：

```
缺 1 字节 → 01
缺 2 字节 → 02 02
缺 3 字节 → 03 03 03
整块都缺 → 10 10 ... （16 个 0x10）
```

### 攻击怎么走

服务端解密后要检查 padding 合不合法。如果它对这个检查结果给出不同响应（比如报错页 vs 正常页），就泄露了一位信息。

1. 构造 `C0'`，暴力改最后一个字节，从 0x00 试到 0xff
2. 某一个值让 padding 变成合法的 `01`，服务端返回"正常"
3. 这时 `I[15] = C0'[15] XOR 0x01`，中间值拿到了
4. 原始明文 `P1[15] = I[15] XOR C0[15]`
5. 把目标改成 `02 02`，继续攻倒数第二位

一个块 16 字节，最坏 16 × 256 次请求就能拿下一个块。

工具层面有 padbuster：

```bash
padbuster <URL> <ciphertext> 16 -encoding 0
```

DVWA 这一级的 token 还套了 Base64 和 IV，实际用工具要先把参数对齐：抓包找到 token 和 IV、判断编码、确认 padding 错和 padding 对时的响应差异。

状态：这一级我只做了原理推演和工具调研，没有真的拿 padbuster 打完整个 token。原因同上，页面 token 的封装格式和工具默认输入对不上，硬试的时间成本高于收益。

## Impossible：AES-256-GCM

GCM 属于认证加密（AEAD）：加密的同时产生一个认证 tag，解密时先验 tag，不合法直接拒。

三个特点：

1. 每次加密用随机 IV
2. 密文被改一个字节，tag 校验就失败，不会返回被篡改的明文
3. 不需要传统 padding，Padding Oracle 这条路天然不存在

可以自己验一下：拿页面 token 改任意一个字符提交，结果是"认证失败/无法解密"，而不是像 High 那样区分 padding 对错。这个观察我做过，结论和预期一致。

## 我卡住的地方

- Low 一开始以为 Base64 解出来就能看到明文，结果是一堆乱码。忘了还有异或这一层。
- ECB 切块时第一块切错位置，因为 token 前面有前缀，不是从第一个字节开始就是数据。要先试几个偏移。
- Padding Oracle 那块看了两遍才想通"为什么改前一块能控制当前块"。关键在于 `P = Dec(C) XOR 前一块`，`Dec(C)` 是固定的，前一块变，P 就跟着变。

## 怎么修

1. 不要自己设计加密。用标准库的标准模式。
2. 分组模式别用 ECB。要加密多条数据，用 CBC 加随机 IV，或者直接上 GCM。
3. 加密必须配完整性校验。要么用 AEAD（GCM、ChaCha20-Poly1305），要么加密后再 HMAC。只加密不校验，等于允许别人改密文。
4. 解密失败统一报错。"填充错误"和"校验失败"不能区分，否则就是 Oracle。
5. IV 每次随机，且不能和密钥一起暴露。CBC 的 IV 可以公开，但必须随机。
6. 密钥管理比算法重要。密钥写在代码里、写在配置文件里、和密文放一起，前面做得再对也白搭。

## 参考来源

- 各级算法与模式（XOR+Base64、AES-128-ECB、AES-128-CBC、AES-256-GCM）参考 DVWA 官方文档与项目源码说明。
- Padding Oracle 部分参考了 PKCS#7 填充标准和公开的 Oracle 攻击说明。
- 我实际验证的是：ECB 分组切分与拼接的脚本逻辑、GCM 篡改后认证失败的观察。其余为资料研读，未在本机完整复现。
