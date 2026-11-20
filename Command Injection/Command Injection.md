# Command Injection

页面让你输一个 IP，点提交，服务器去 ping 它。后端大概是这样：

```php
$target = $_REQUEST['ip'];
$cmd = shell_exec('ping -c 4 ' . $target);
```

问题在最后那个点号。用户输的东西原样粘在命令后面，所以只要塞一个命令分隔符，后面写什么都执行。

## 连接符先记一遍

| 符号 | 行为 |
|---|---|
| `;` | 顺序执行，前一个成功失败都继续 |
| `&&` | 前一个成功才执行后一个 |
| `\|\|` | 前一个失败才执行后一个 |
| `\|` | 管道，前一个的输出给后一个当输入 |
| `&` | 放后台，命令照样执行 |
| `` `cmd` `` | 命令替换，先把反引号里的跑完再拼回去 |
| `$(cmd)` | 同上，现代写法 |

URL 里发的时候要编码：`&` 是 `%26`，`|` 是 `%7c`，`;` 是 `%3b`，空格 `%20`，换行 `%0a`。

## Low

```php
$target = $_REQUEST['ip'];
if (stristr(php_uname('s'), 'Windows NT')) {
    $cmd = shell_exec('ping ' . $target);
} else {
    $cmd = shell_exec('ping -c 4 ' . $target);
}
```

一个字的过滤都没有。

先输 `127.0.0.1`，能 ping 通，页面回显 ping 的结果。再输：

```
127.0.0.1; whoami
```

回显 ping 结果下面多了一行 `www-data`，说明 `;` 后面的命令执行了。实际跑的是：

```
ping -c 4 127.0.0.1; whoami
```

![执行 whoami](whoami.png)

换个命令看看当前路径：

```
127.0.0.1; pwd
```

![执行 pwd](pwd.png)

到这里性质就定了：任意命令执行，权限跟 Web 服务一致。真实环境里下一步一般是读 `/etc/passwd`、看 `env` 找数据库密码、找能不能提权。

## Medium

加了两个替换：

```php
$substitutions = array('&&' => '', ';' => '');
$target = str_replace(array_keys($substitutions), $substitutions, $target);
```

只删了 `&&` 和 `;`。剩下的符号一个都没管：

```
127.0.0.1 & whoami
127.0.0.1 | whoami
127.0.0.1 || whoami
```

`&` 最容易过，因为规则只匹配两个 `&`，单个的不匹配。`|` 也能用，直接拿管道。

还有一个位置要注意：`str_replace` 把 `;` 删掉之后，`127.0.0.1; whoami` 变成 `127.0.0.1 whoami`，这就不是两个命令了，而是给 ping 传了两个参数，会失败。所以这里不是"删了就没事"，是删得不对反而绕不过去，得换符号。

## High

过滤表加长了：

```php
$substitutions = array(
    '&'    => '',
    ';'    => '',
    '| '   => '',   ← 注意这里有空格
    '-'    => '',
    '$'    => '',
    '('    => '',
    ')'    => '',
    '`'    => '',
    '||'   => '',
);
```

看起来该封的都封了。问题出在第三行：`'| '` 匹配的是"管道符加一个空格"，不是管道符本身。

所以 `127.0.0.1 | whoami` 会被拦，因为中间有空格。但：

```
127.0.0.1|whoami
```

没有空格，规则匹配不上，直接过。

顺带一个坑：`-` 也在过滤表里，所以 `ping -c 4` 里的 `-c` 会被删掉，页面上 ping 的行为会变得奇怪。这是黑名单式过滤的连带伤害。

## Impossible 为什么打不进去

```php
$target = stripslashes($_REQUEST['ip']);
$octet = explode(".", $target);

if (is_numeric($octet[0]) && is_numeric($octet[1]) &&
    is_numeric($octet[2]) && is_numeric($octet[3]) &&
    sizeof($octet) == 4) {

    $target = escapeshellarg($target);
    $cmd = shell_exec('ping -c 4 ' . $target);
    echo "<pre>{$cmd}</pre>";
} else {
    echo '<pre>ERROR: You have entered an invalid IP.</pre>';
}
```

三层：

1. 按点切成四段，段数必须正好是四。
2. 每段必须是纯数字。`127.0.0.1;whoami` 切开以后最后一段是 `1;whoami`，`is_numeric` 直接 false。
3. `escapeshellarg()` 把整个值包成单个字符串参数，就算里面有符号也只会被当参数的一部分。

第 2 条是关键。它是白名单思路：只接受"长得像 IP 的东西"，其他一律不认，不跟你玩过滤游戏。

## 有回显和无回显

DVWA 是有回显的，命令输出直接显示在页面上，最好办。

真实环境更多是没回显的。这时候靠时间判断：

```
127.0.0.1; sleep 5
```

页面明显停 5 秒才返回，就说明命令执行了。再往后就是往自己机器上打外带请求（DNS 或 HTTP），把结果带出来。这一步超出本靶场范围，没在这里做。

## 我卡住的地方

- High 那档试了 `| whoami`、`; whoami` 全失败，卡了一阵。看到源码里 `'| '` 带空格才反应过来，改成无空格写法一次过。
- `&&` 在 URL 里必须编码成 `%26%26`，直接写 `&&` 会被服务端解析成两个参数。第一次没编码，回显一直不对。
- `-` 被过滤导致 ping 本身行为异常，一开始以为是自己命令写错，其实是被过滤表削掉了。

## 怎么修

1. 能不调系统命令就别调。查连通性用语言自带的网络库，比 `ping` 安全得多。
2. 必须调的话，先严格校验输入。这里是 IP，就用 `filter_var($ip, FILTER_VALIDATE_IP)`，只放合法 IP。
3. 再用 `escapeshellarg()` 转义。校验加转义是两道，别只做一道。
4. 命令别用字符串拼接。PHP 的 `proc_open` 支持数组形式传参，参数不会经过 shell 解析。
5. Web 进程降权，别用 root 跑 PHP-FPM。
