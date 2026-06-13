# DOM source 和DOM sink
source:输入来源
sink:危险输出点
### 常见source
```javascript
location.href
location.search
location.hash
document.URL
document.documentURI
document.referrer
window.name
localStorage
sessionStorage
document.cookie
```
### 常见sink
```javascript
document.write()
element.innerHTML
element.outerHTML
insertAdjacentHTML()
eval()
setTimeout("code")
setInterval("code")
Function()
```
## 如果用户可控内容进入document.write(),就很容易产生XSS


#URL参数解析问题
### DVWA的DOM XSS模块通常用URL参数传递默认语言：
```javascript
正常情况下为?default=English,它的原理是document.location.href.substring(...)
```
### 如果在LOW难度下将default的值进行修改，如下
```javascript
?default=<script>alert(1)</script>
```
### 如果页面没有进行过滤，浏览器就会执alert(1),就会显示xss-low.png

# HAsh片段的特殊性
URL中#后面的内角叫fragment或者hash.
比如
```javascript
http://example.com/page?default=English#<script>alert(1)</script>
```
关键：#后面的内容不会发送给服务器
也就是说：服务器仅仅可以看到?default=English
服务器前端JS看到打的：完整URL,包括#后面的内容
**这是DVWA DOM XSS高等级绕过中的重要知识点**


# 黑名单过滤的局限性
如果禁止出现<script>标签
XSS不只有<script>一种方式，还可以使用是件处理器
比如：
```javascript
<img src=x onerror=alert(1)>
```
```javascript
<svg onload=alert(1)>
```
**所以利用黑名单仅仅过滤一个<script>一个标签是无法做到安全防御的**

# medium难度黑名单过滤
```javascript
<svg onload=alert(1)>
```
## medium建议手动进行的实操过程
>当在URL中将?default的内容改为?default=<script>alert(1)</script>后，就会被拦截<
>这是因为该难度进行了黑名单防御，但是当在?default=的后面输入<svg onload=alert(1)>或者<img src=x onerror=alert(1)>就可以绕过继续运行<

## hash绕过思路
>由于#后面的内容不发送给服务器,所有有时可以使用?default=English#<script>alert(1)</script>来进行绕过，因为后端看到的内容只为default=English,但是如果前端读取的时document.location.href，那么它可能会把#后面的内容也拿进去,**这是DVWA DOM XSS中非常重要的绕过点**<

### Medium可以学到的内容有
```javascript
1. 黑名单过滤的不足
2. 只过滤 <script> 没有意义
3. XSS 可以通过事件属性触发
4. 后端检查与前端读取范围可能不一致
5. Hash 不发送给服务器的特性
6. payload 需要根据过滤逻辑变化
```

# High等级
## 后端白名单限制了default=English,仅允许
测试：
当?default=<script>alert(1)</script>，结果就是被重定向或者无效,说明白名单生效

## 绕过关键:Hash
虽然后端白名单限制了：default=English
但是如果前端javaScript读取完整URL，例如:document.location.herf，那么攻击者就可以构造?default=English#<script>alert(1)</script>，服务器接收到的参数是default=English，所以白名单通过

### High等级可以学习到的内容有
```javascript
1. 白名单比黑名单更安全，但实现不当仍可能被绕过
2. 后端只校验 query 参数，不代表前端使用的数据也安全
3. location.href 包含 hash
4. fragment 不发送给服务器
5. DOM 型 XSS 的防护必须考虑前端代码
6. 服务端白名单无法单独解决所有 DOM XSS
```

# impossible难度
仅做参考说明
1. 后端严格白名单
2. 不再使用不安全的 document.write 拼接用户输入
3. 输出时进行安全编码
4. 前端不从完整 URL 中直接取值写入 DOM
5. 使用固定选项，而不是让用户控制 HTML


# 总结
| 安全等级 | 防护方式 | 典型问题 | 是否容易利用 | 主要学习点 |
|---|---|---|---|---|
| Low | 基本无过滤 | 直接把 URL 输入写入 DOM | 很容易 | 理解 DOM XSS 基础流程 |
| Medium | 黑名单过滤 `<script>` | 过滤不完整，可用事件绕过 | 容易 | 黑名单不足、事件型 payload |
| High | 白名单限制参数 | 后端只校验 query，不处理 hash 风险 | 中等 | Hash 绕过、前后端数据差异 |
| Impossible | 安全实现 | 避免危险 sink，严格白名单/编码 | 很难 | 正确防御方案 |