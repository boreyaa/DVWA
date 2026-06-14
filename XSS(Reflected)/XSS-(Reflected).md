# XSS(Reflected)的原理
```javascript
当 Web 应用把用户输入的数据直接反射到页面中，而没有进行正确过滤、编码或校验时，攻击者可以构造恶意 JavaScript，使浏览器执行非预期脚本。
```

| 特点 | 说明 |
|---|---|
| 输入来源 | 通常来自 URL 参数、表单、搜索框等 |
| 输出位置 | 服务端立即把输入内容返回到页面 |
| 持久性 | 不存储在数据库中 |
| 触发方式 | 诱导用户访问恶意链接 |
| 典型危害 | Cookie 窃取、钓鱼、页面篡改、跳转、键盘记录等 |



 
 ### HTML中的正文输出场景
| 上下文 | 示例 | 防御方式 |
|---|---|---|
| HTML 正文 | `<div>用户输入</div>` | HTML 实体编码 |
| HTML 属性 | `<input value="用户输入">` | 属性编码 |
| JavaScript 上下文 | `var a = "用户输入"` | JS 字符串编码 |
| URL 上下文 | `<a href="用户输入">` | URL 编码和协议校验 |

## low难度:无任何过滤，可以使用script语法
>当在地址框中输入以下内容
```scripte
http://127.0.0.1/dvwa/vulnerabilities/xss_r/?name=<script>alert(1)<script>#
```
如果应用没有任何过滤，浏览器就会执行alert(1)
>以下图片为效果图https://github.com/boreyaa/DVWA/blob/main/XSS(Reflected)/xss-low.png

## medium难度:仅仅过滤scripte，可以使用以下其他方式过滤

| 绕过方式 | 绕过代码 |
|---|---|
| 使用图片事件 | `<img src=x onerror=alert(1)>` |
| 使用SVD | `<svg onload=alert(1)>` |
| 使用大小写 | `<ScRiPt>alert(1)</ScRiPt>` |
| 关键字拆分绕过 | `<scr<script>ipt>alert(1)</scr</script>ipt>` |
>以下为效果图https://github.com/boreyaa/DVWA/blob/main/XSS(Reflected)/xss-medium.png

### 以下是一些防御方式以及推荐程度以及原因
| 防御方式 | 是否推荐 | 原因 |
|---|---|---|
| 黑名单过滤 | 不推荐 | 绕过方式多 |
| 删除关键字 | 不推荐 | 容易大小写、编码、嵌套绕过 |
| 正则粗暴过滤 | 不推荐 | 容易漏场景 |
| 输出编码 | 推荐 | 从根源避免浏览器解析成代码 |
| 白名单校验 | 推荐 | 限制输入格式 |
| CSP | 辅助防护 | 减少脚本执行风险 |

## High难度:正则过滤增强，但仍然不能覆盖所有XSS向量

### 使用正则进行第一步过滤
```javascript
$name = preg_replace('/<(.*)s(.*)c(.*)r(.*)i(.*)p(.*)t/i', '', $_GET['name']);
echo "<pre>Hello {$name}</pre>";
```
>他尝试更宽泛的过滤scripte标签，并且使用i忽略了大小写

### 但是当使用medium难度里面的绕过方法时，你会发现
| 绕过方式 | 绕过代码 | 结果 |
|---|---|---|
| 使用图片事件 | `<img src=x onerror=alert(1)>` | 成功 |
| 使用SVD | `<svg onload=alert(1)>` | 成功 |
| 使用大小写 | `<ScRiPt>alert(1)</ScRiPt>` | 失败 |
| 关键字拆分绕过 | `<scr<script>ipt>alert(1)</scr</script>ipt>` | 失败 |
>以下为效果图https://github.com/boreyaa/DVWA/blob/main/XSS(Reflected)/xss-high.png

>这说明，服务器虽然过滤了script标签，但是没有防止浏览器解析事件处理器

## impossible难度：输出编码,无法作为HTML执行
安全编码
```javascript
$name = htmlspecialchars($_GET['name']);
echo "<pre>Hello {$name}</pre>";
```
>当输入<script>alert(1)</script>之后，会输出<script>alert(1)</script>，浏览器会把它当成普通文本，而不是HTML标签
>你需要知道
1. 输出编码是防御 XSS 的核心
2. htmlspecialchars() 的作用
3. ENT_QUOTES 的意义
4. 字符集 UTF-8 的重要性
5. 正确防护不是过滤，而是根据上下文编码


>重点逻辑用户输入进入服务端 → 服务端处理或不处理 → 输出到 HTML 页面 → 浏览器按 HTML/JS 解析 → 如果没有正确编码，就可能执行脚本。
### 真正安全的做法是
```javascript
htmlspecialchars($input, ENT_QUOTES, 'UTF-8')
```

>额外补充一下THML一些元素的事件属性https://github.com/boreyaa/DVWA/blob/main/XSS(Reflected)/HTML-page.md



# 四种难度的区别表奉上
| 安全等级 | 防护方式 | 示例防护代码 | 可否绕过 | 典型可用 Payload | 学习重点 |
|---|---|---|---|---|---|
| Low | 无防护 | 直接输出 `$_GET['name']` | 很容易 | `<script>alert(1)</script>` | 理解 XSS 基础原理 |
| Medium | 简单字符串替换 | `str_replace('<script>', '', $name)` | 容易 | `<img src=x onerror=alert(1)>`、`<SCRIPT>alert(1)</SCRIPT>` | 黑名单过滤缺陷 |
| High | 正则过滤 script | `preg_replace('/<.*script/i', '', $name)` | 仍可绕过 | `<img src=x onerror=alert(1)>` | script 不是唯一 XSS 向量 |
| Impossible | 输出编码 | `htmlspecialchars($name)` | 正常情况下不可绕过 | 无法作为 HTML 执行 | 正确防御方式 |


