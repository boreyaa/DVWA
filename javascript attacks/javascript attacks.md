# JavaScript Attacks

页面要提交一个 `phrase` 和一个 `token`。token 由前端 JS 算出来塞进隐藏字段。

模块要表达的东西只有一句：**前端算出来的东西，攻击者也能算**。逻辑在前端，等于公开。

三档的区别只是"算法看起来复杂了多少"。

## Low：md5(rot13(phrase))

F12 → Sources，找到页面里的 JS：

```javascript
function rot13(inp) {
    return inp.replace(/[a-zA-Z]/g, function(c) {
        return String.fromCharCode(
            (c <= "Z" ? 90 : 122) >= (c = c.charCodeAt(0) + 13) ? c : c - 26
        );
    });
}

function generate_token() {
    document.getElementById("token").value = md5(rot13(document.getElementById("phrase").value));
}
```

一句话：先 ROT13，再 MD5。

目标是让 `phrase` 等于 `success`。手算：

```
success  --ROT13-->  fhpprff
md5("fhpprff") = 38581812b435834ebf84ebcc2c6424d6
```

### 两种提交方式

控制台直接改两个字段：

```javascript
document.querySelector('[name="phrase"]').value = 'success';
document.querySelector('[name="token"]').value = '38581812b435834ebf84ebcc2c6424d6';
```

然后点提交。

或者 Burp 拦下请求，直接改请求体：

```
phrase=success&token=38581812b435834ebf84ebcc2c6424d6
```

![控制台计算结果](low1.png)

![提交成功](low2.png)

第二种更接近真实场景：攻击者根本不打开你的页面，他自己构造请求。

## Medium：XX + 反转 + XX

算法换了，从 JS 里能看出来：token 是 `phrase` 反转后前后各加 `XX`。

默认值 `ChangeMe` 对应的 token 是 `XXeMegnahCXX`，一眼就能对上。

目标 `success`：

```
success  --反转-->  sseccus
前后加 XX  -->  XXsseccusXX
```

提交：

```
phrase=success&token=XXsseccusXX
```

这个"加密"连哈希都不是，就是一个字符串反转。看到默认值就能推出来算法。

## High：反转 + XX + SHA256

第 3 个在反转和拼接外面又套了一层 SHA256：

```
token = sha256("XX" + reverse(phrase) + "XX")
```

`XXsseccusXX` 的 SHA256 得用工具算。三条路：

1. CyberChef：输入 `XXsseccusXX` → `SHA2` → SHA-256
2. 控制台：`crypto.subtle.digest` 是异步的，写起来麻烦
3. 直接调用页面自己的函数

我用的第一条，主要是省事。

### 怎么找到算法

这级的 token 生成函数不在页面内联 JS 里，在外部文件。做法：

1. F12 → Sources，看页面引了哪些 js
2. `Ctrl + Shift + F` 全局搜关键词：`token`、`sha256`、`XX`、`phrase`
3. 在可疑的 js 里下断点，提交一次看调用栈
4. 也可以在 Console 里 `console.log(window)` 看挂了哪些全局函数

这一步练的是读混淆代码。真实项目里 JS 会被压缩、变量名变成 `a`、`b`、`c`，但字符串常量（比如那个 `XX`）改不了，从常量入手最快。

## Impossible 为什么打不进去

token 不再由前端生成。服务端生成、跟 Session 绑定、服务端校验，前端只负责把值带回去。

攻击者能改 `phrase`，但算不出对应的 token，因为算法和密钥都在服务端。

## 这个模块真正想说的

前三级表面上难度在上升：ROT13+MD5 → 反转 → 反转+SHA256。但如果把这三条并排看，会发现它们是同一个问题：

**校验逻辑在客户端，攻击者就能自己算出一个合法的值。**

算法复杂度不构成安全性。ROT13 和 SHA256 在这里地位一样，因为攻击者不需要破哈希，他只需要知道你在算什么。

## 我卡住的地方

- Low 第一次只改了 `phrase`，忘了 token 也要一起改，提交失败。前端在提交时会重新算一遍 token，覆盖掉我手填的值。必须两个一起改，或者干脆走 Burp。
- 控制台改值的那段代码，`querySelector` 里用 `[name="phrase"]` 而不是 `#phrase`，因为元素的 id 和 name 不一定一样。第一次用 id 选择器返回 null。
- High 在 Sources 里搜 `sha256` 搜不到，因为代码里调用的是 `CryptoJS.SHA256`。换成搜 `SHA` 才找到。

## 怎么修

1. 安全判断放服务端。前端只做体验，不做校验。
2. token 由服务端生成，随机、不可预测、跟 Session 绑定。
3. 前端不要出现密钥、算法参数、验证规则。
4. 前端混淆只有心理作用，压缩过的代码照样能读。
