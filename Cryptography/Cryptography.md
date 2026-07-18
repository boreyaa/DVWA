# Cryptography密码学

DVWA的Cryptography模块主要演示常见密码学实现错误，包括：
1. 把编码或简单混淆当成加密
2. 使用 ECB 这种不安全分组模式
3. CBC 模式下的 Padding Oracle 攻击
4. 正确使用认证加密算法作为安全实现参考

# Low 等级实操：XOR + Base64 不是安全加密
## 漏洞原理
>Low 等级展示的是一个非常典型的错误：开发者使用 XOR + Base64 来“保护”数据，但这本质上更接近编码或简单混淆，不是真正的安全加密 
根据网络资料，low等级的token结构大致是：
>Base64-encoded XOR
使用的秘钥类似：wachtwoord
>这个等级的核心问题是:XOR 加密在密钥重复、密钥可猜、明文可知的情况下非常容易被还原

## 实操目标：
一般目标是：
1. 获取页面中给出的密文 token
2. Base64 解码
3. 使用 XOR 还原明文
4. 理解为什么这不是安全加密

## 手工分析流程
1. 假设页面给了你一个token,例如:Gx0f...
2. 第一步，Base64解码
3. 可以使用CyberChef:From Base64
4. 然后尝试XOR
5. 如果你知道密钥是：wachtwoord
6. 则可继续使用:XOR with key: wachtwoord
7. 最终会得到类似JSON或可读字符串，例如：
>XOR with key: wachtwoord
具体内容取决于DVWA版本和页面给出的challenge

## Python实操脚本
```html
import base64

token = "把页面中的token放这里"
key = b"wachtwoord"

cipher = base64.b64decode(token)

plain = bytes([
    cipher[i] ^ key[i % len(key)]
    for i in range(len(cipher))
])

print(plain.decode(errors="ignore"))
```

## 如果不知道密钥怎么办
1. 如果你知道部分明文，可以利用 XOR 的性质：

```html
ciphertext = plaintext XOR key
key = ciphertext XOR plaintext
```
例如你猜测明文中包含：

```html
"user"
"admin"
"role"
```
可以用已知明文攻击恢复密钥片段。

**这就是 Low 等级真正想让你理解的点：XOR 不是不能用，但如果密钥短、重复使用、可预测，就会非常危险。**

# Low等级知识点总结
| 知识点 | 说明 |
|---|---|
| 编码 vs 加密 | Base64 只是编码，不提供安全性 |
| XOR 原理 | 明文、密文、密钥三者任意知道两个可以推出第三个 |
| 重复密钥风险 | 短密钥循环使用容易被恢复 |
| 已知明文攻击 | 猜测部分明文可以推导密钥 |
| 密码学误用 | 自己设计“加密算法”通常非常危险 |

# Medium 等级实操：AES-ECB 分组替换攻击
## 漏洞原理
Medium等级使用的是：
>AES-128-ECB
公开资料中提到，Medium 等级使用 AES-128-ECB，每个分组独立加密，不使用 IV
ECB最大的问题是：
```html
明文块1 -> 密文块1
明文块2 -> 密文块2
明文块3 -> 密文块3
```
每个块彼此独立，所以攻击者可以进行
>复制、剪切、重排密文块
这就是所谓的 cut-and-paste attack，即分组替换攻击

## 实操目标
medium等级通常会给你多个用户token,例如：
```html
user token
admin token
guest token
```
你的目标可能是：
1. 观察不同 token 的密文块
2. 将 token 按 16 字节分组
3. 找到包含目标权限字段的密文块
4. 拼接一个新的 token
5. 使用伪造 token 访问系统
## 分组分析方法
AES的分组大小是：
>16 bytes = 128 bits
如果 token 是 Base64 编码的，需要先 Base64 解码。
```html
python示例
import base64

token = "页面中的token"
raw = base64.b64decode(token)

for i in range(0, len(raw), 16):
    block = raw[i:i+16]
    print(i // 16, block.hex())
```
输出可能类似：
```html
0 8f2a1c...
1 7b9d3e...
2 cc45ab...
3 19ef72...
```
### 对比多个token
假设有三个token
```html
token_user
token_admin
token_guest
```
可以这样分组打印
```python
import base64

tokens = {
    "user": "用户token",
    "admin": "管理员token",
    "guest": "访客token"
}

for name, token in tokens.items():
    raw = base64.b64decode(token)
    print(f"\n{name}:")
    for i in range(0, len(raw), 16):
        print(i // 16, raw[i:i+16].hex())
```
如果某个块对应的是：
>"role":"admin"
或者：
>"is_admin":true

## 拼接伪造token
```python
import base64

user_raw = base64.b64decode("普通用户token")
admin_raw = base64.b64decode("管理员token")

user_blocks = [
    user_raw[i:i+16]
    for i in range(0, len(user_raw), 16)
]

admin_blocks = [
    admin_raw[i:i+16]
    for i in range(0, len(admin_raw), 16)
]

# 示例：把 admin 的第 2 个块替换到 user 的第 2 个块
forged_blocks = user_blocks.copy()
forged_blocks[1] = admin_blocks[1]

forged_raw = b"".join(forged_blocks)
forged_token = base64.b64encode(forged_raw).decode()

print(forged_token)
```
然后把生成的forget token提交到DVWA页面

## 为什么ECB不安全
ECB模块的问题是：
>相同明文块 -> 相同密文块
它不会隐藏数据模式。

经典例子是“ECB 加密企鹅图”：

1. 明文图像有明显轮廓
2. ECB 加密后轮廓仍可被看出
3. 因为相同像素块产生相同密文块
在 DVWA 的 Medium 等级中，这个问题体现在用户 token 上：攻击者可以通过分组替换构造新的身份或权限。

## Medium等级知识点总结
| 知识点 | 说明 |
|---|---|
| AES 分组加密 | AES 固定 16 字节分组 |
| ECB 模式缺陷 | 相同明文块产生相同密文块 |
| 无 IV 风险 | ECB 不使用 IV，无法隐藏重复结构 |
| 分组替换攻击 | 攻击者可以重排密文块 |
| token 安全设计 | 加密不等于完整性保护 |
| 认证加密必要性 | 需要防止密文被篡改 |

# High 等级实操：CBC Padding Oracle 攻击
## 漏洞原理
该等级使用的是：
>AES-128-CBC
公开资料中提到，High 等级展示的是针对 AES-CBC 的 Padding Oracle 攻击。

CBC 模式比 ECB 安全，因为它引入了 IV，并且每个密文块依赖前一个密文块。但如果服务端在解密失败时泄露“padding 是否正确”的信息，就可能产生 Padding Oracle 漏洞。
## CBC解密结构
CBC解密过程可以表示为：
```html
P1 = Dec(C1) XOR IV
P2 = Dec(C2) XOR C1
P3 = Dec(C3) XOR C2
```
其中
```html
P 是明文块
C 是密文块
IV 是初始化向量
Dec 是 AES 解密函数
```
攻击者虽然不知道密钥，但可以修改前一个密文块，从而影响当前明文块。

## Padding 是什么？
1. AES 块大小是 16 字节。

2.  如果明文不足 16 字节，需要填充。

3. 常见填充方式是 PKCS#7：

4. 如果缺 1 字节，填充：

>01
5. 如果缺 2 字节，填充：

>02 02
6. 如果缺 3 字节，填充：


>03 03 03
7. 如果整个块都需要填充，则填充：

>10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10
Padding Oracle 攻击就是利用服务端对 padding 是否正确的不同响应，逐字节恢复明文。

## 实操目标
1. 页面给出 token 和 IV
2. 你提交 token
3. 服务端会尝试解密
4. 如果 padding 错误，返回一种响应
5. 如果 padding 正确，返回另一种响应
6. 利用响应差异还原明文或伪造 token

## 手工理解攻击过程
假设有两个块
```html
C0 = IV
C1 = 密文块
```
服务端解密
>P1 = Dec(C1) XOR C0
攻击者不能控制 Dec(C1)，但可以控制 C0。

如果我们修改 C0 的最后一个字节，使得 P1 的最后一个字节变成：

>01

服务端会认为padding正确，攻击公式
```html
中间值 I = Dec(C1)
P1 = I XOR C0
```
如果想让最后一个明文字节变成01：
>C0'[15] = I[15] XOR 0x01
攻击者不知道 I[15]，但可以暴力尝试 0x00 到 0xff。

当服务端返回 padding 正确时，就能推出：
>I[15] = C0'[15] XOR 0x01
再推出原始明文字节
>P1[15] = I[15] XOR C0[15]
然后继续攻击倒数第二个字节，使 padding 变成：
>02 02
以此类推，最终恢复整个明文块。

## 使用工具实操思路
如果你只是学习，不想手写完整 Padding Oracle 脚本，可以使用工具，例如
>padbuster
一般的使用逻辑是：
>padbuster <URL> <ciphertext> <block_size> -encoding 0
但 DVWA 的 High 等级 token 通常还涉及 IV、Base64、JSON 等格式，所以实际使用时你需要：
```html
抓包
找到 token 参数
找到 IV 参数
判断 token 是否 Base64 编码
判断 padding 错误和 padding 正确时页面响应差异
配置工具或编写脚本自动尝试
```
# high等级知识点总结
| 知识点 | 说明 |
|---|---|
| CBC 模式 | 每个明文块与前一个密文块或 IV 异或 |
| IV 作用 | 防止相同明文产生相同密文 |
| PKCS#7 Padding | 分组加密需要填充 |
| Padding Oracle | 服务端泄露 padding 是否正确 |
| 密文可塑性 | CBC 密文被修改后会影响解密明文 |
| 完整性保护 | 仅加密不能防止篡改 |
| 错误信息处理 | 不应暴露 padding 错误细节 |
| 认证加密 | 应使用 GCM、ChaCha20-Poly1305 等 AEAD 算法 |

# Impossible 等级实操：安全实现参考
## 实现思路
Impossible 等级不是让你攻击成功，而是展示安全实现。

公开资料显示，Impossible 等级使用的是：
>AES-256-GCM
其特点包括
1. 使用认证加密
2. 每次加密生成随机 IV
3. 使用 authentication tag 验证数据完整性
4. 不容易受到 Padding Oracle 攻击，因为 GCM 不需要传统 padding
## 为什么 AES-GCM 更安全？
AES-GCM 属于 AEAD：
>Authenticated Encryption with Associated Data
也就是:
>加密 + 完整性校验
它不仅保护数据机密性，还保护数据不被篡改。

如果攻击者修改了密文、IV 或 tag，解密时认证会失败，服务端不会返回被篡改后的明文。

## 实操观察
你可以尝试：
1. 获取 Impossible 等级页面中的 token
2. 修改 token 任意一个字符
3. 提交
4. 观察结果
通常结果应该是：
```html
认证失败
无法解密
token 无效
```
而不会像 High 等级那样暴露 padding 是否正确。

# Impossible 等级知识点总结
| 知识点 | 说明 |
|---|---|
| AES-GCM | 认证加密模式 |
| 随机 IV | 每次加密使用唯一 IV |
| Authentication Tag | 验证密文完整性 |
| 防篡改 | 修改密文会导致认证失败 |
| 无 Padding Oracle | GCM 不使用传统 CBC padding |
| 安全设计 | 机密性和完整性都要考虑 |

# 四个等级对比总结
| 等级 | 算法 / 方式 | 主要问题 | 攻击方式 |
|---|---|---|---|
| Low | XOR + Base64 | 把编码/混淆当加密 | Base64 解码、XOR 还原 |
| Medium | AES-128-ECB | ECB 分组独立、无 IV | 分组替换、剪切粘贴攻击 |
| High | AES-128-CBC | Padding Oracle | 利用 padding 错误响应恢复明文 |
| Impossible | AES-256-GCM | 安全实现参考 | 正常情况下无法篡改成功 |