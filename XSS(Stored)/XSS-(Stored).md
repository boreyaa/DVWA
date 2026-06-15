# XSS(Stored)的原理
>服务端会把这些内容保存到数据库中，然后在页面中展示出来,如果服务端没有正确过滤或编码用户输入，攻击者就可以把 JavaScript 代码写入留言内容中。之后，任何访问这个页面的用户都会执行这段恶意脚本。

### 基本流程
1. 攻击者提交恶意脚本
2. 服务端保存到数据库
3. 其他用户访问页面
4. 浏览器渲染页面
5. 恶意 JavaScript 被执行

### 你需要知道
>XSS 的本质不是“把脚本提交进去”，而是“浏览器把攻击者输入当成代码执行”。

### 输入过滤和输出编码的区别
#### 输入过滤
过滤script
```javascript
str_replace('<script>', '', $message);
```
#### 输出编码 
```javascript
htmlspecialchars($message, ENT_QUOTES, 'UTF-8');
```
#### 这会把危险字符转义
| 原字符 | 编码后 |
|---|---|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#039;` |
| `&` | `&amp;` |

###  为什么 Stored XSS 危害比 Reflected XSS 更大
>Stored XSS 不需要诱导用户点击恶意链接，只要用户访问被污染的页面就会中招,例如:

1. 窃取 Cookie
2. 劫持用户会话
3. 篡改页面内容
4. 伪造用户操作
5. 获取用户输入
6. 钓鱼
7. 内网攻击跳板
8. 管理员后台沦陷
9. 蠕虫式传播

### Stored XSS的触发点和存储点

#### 存储点
>也就是恶意代码被保存的位置。
#### 触发点
>也就是恶意代码被展示并执行的位置。

## 在真实环境下，一个输入点和输出点可能并不在同一个页面,比如以下流程
1. 用户修改昵称
2. 昵称存入数据库
3. 管理员后台查看用户列表
4. 管理员浏览器触发 XSS

# Low 等级基本不做过滤或编码，用户输入会被原样保存并原样输出。
```html
在Message中输入<script>alert('XSS')</script>,name可以随便填,出现下图中的内容即说明Stored XSS成功
```
>效果图:https://github.com/boreyaa/DVWA/blob/main/XSS(Stored)/xss-low.png

### 你需要理解的是
1. 用户输入不能直接信任
2. 数据库存储了恶意脚本
3. 每次刷新页面都会再次触发
4. 其他用户访问该页面也会执行脚本
5. Stored XSS 具有持久性

## cookie获取测试
```html
在message里面输<script>alert(document.cookie)</script>,name任意填，就可以获取到cookie,内容如下图
```
>效果图:https://github.com/boreyaa/DVWA/blob/main/XSS(Stored)/xss-cookie.png

## 页面篡改测试
> <script>document.body.innerHTML='页面已被修改'</script>
>效果图：https://github.com/boreyaa/DVWA/blob/main/XSS(Stored)/xss-page-test.png


# Medium 等级通常会做一些简单过滤
>比如过滤script标签
```javascript
str_replace('<script>', '', $message);
```
```html
当使用Low难度里面的<script>alert('XSS')</script>,会发现没有弹窗，说明被过滤了
```
### 可以使用以下方法绕过
| 绕过方式 | 绕过代码 | 方式 |
|---|---|---|
| 使用图片事件 | `<img src=x onerror=alert('XSS')>` | 放在name字段,放在message会被处理掉 |
| 使用SVD | `<svg onload=alert(XSS)>` |放在name字段,|
| 使用大小写 | `<ScRiPt>alert('XSS')</ScRiPt>` |放在Name字段|
| 嵌套构造绕过 | `<scr<script>ipt>alert(1)</script>` | 方式：源码删除中间的script标签后，就变成正常的了 |

***值得注意的是***
>由于源码设置的Name的Maxlength为10，所以想输入绕过代码的时候会被"截断"，这个时候我推荐使用burp抓包工具将name那一栏的内容直接修改为想要的代码，这样就可以绕过原本的源码maxlength的限制，直接起到真正的攻击体验作用，当然也可以有其他修改方法,curl构造请求，或者是在console里面直接输入document.querySelector('[name=txtName]').removeAttribute('maxlength'),不建议直接动源码内容，因为当前靶场为靶机测试环境，直接修改源码起不到实操训练的作用。
>以下为嵌套构造绕过在Burp的实操图https://github.com/boreyaa/DVWA/blob/main/XSS(Stored)/xss-burp.png

绕过成功效果图https://github.com/boreyaa/DVWA/blob/main/XSS(Stored)/xss-medium.png

# High 等级通常会使用更强的过滤，例如正则过滤script标签，可能大小写不敏感。
>在high难度里面你需要了解到：
1. 正则过滤比简单替换强，但仍然不是最佳防御
2. 只拦截危险标签不能覆盖全部 XSS 场景
3. XSS 防御不能依赖单一黑名单
4. 正确的输出编码比过滤更关键
5. 不同输出上下文需要不同编码策略


过滤代码
```html
preg_replace('/<(.*)s(.*)c(.*)r(.*)i(.*)p(.*)t/i', '', $message);
```

>当测试script的时候,通常会被过滤，如果做了大小写不敏感匹配，一般会失败

尝试非scripte标签
```html
<img src=x onerror=alert('XSS')>
```
尝试SVG
```html
<svg onload=alert('XSS')>
```

**如果能够执行，可以说明浏览器中可执行 JavaScript 的 HTML/SVG 上下文很多。**

# Impossible 等级通常采用了较完善的防御方式，例如：
1. 使用 token 防 CSRF
2. 对输入做严格处理
3. 对输出做 HTML 实体编码
4. 使用 htmlspecialchars
5. 对数据库操作使用预处理语句

### 你需要理解到
1. 正确编码可以让恶意输入变成普通文本
2. 不应该依赖黑名单过滤
3. 输出位置决定编码方式
4. 防御 XSS 的核心是“上下文感知的输出编码”
5. 安全开发应结合输入校验、输出编码、CSP、HttpOnly、SameSite 等机制


# 不同安全等级对比
| 安全等级 | 防护方式 | 是否容易利用 | 典型绕过思路 | 学习重点 |
|---|---|---|---|---|
| Low | 基本无过滤 | 非常容易 | 直接 `<script>` | 理解 Stored XSS 基本原理 |
| Medium | 简单字符串过滤 | 容易 | 大小写、事件属性、非 script 标签 | 理解黑名单过滤缺陷 |
| High | 更强正则过滤 | 中等 | 非 script 标签、事件属性、上下文绕过 | 理解单点过滤仍不可靠 |
| Impossible | 输出编码和安全处理 | 很难 | 正常情况下无法利用 | 理解正确防御方式 |
