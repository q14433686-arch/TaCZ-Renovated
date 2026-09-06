# 枪包脚本环境缺 `string` 库修复（26.2 线，2026-09-06）

> 本修自 1.21.11 姊妹线回传（同仓 `arena/01a07887-tacz-renovated` commit
> `47960ae`，2026-09-06）。26.2 线并非该姊妹线的下游，但两线共用同一套 Lua
> 脚本底座（见 §0），缺陷与修法逐字等价，故「移植」实为等价的落点复现。
>
> 症状（1.21.11 姊妹线记录的用户报告；本线同底座，预期同症状）：`Ticking player`
> → `org.luaj.vm2.LuaError: ra1k_gun_logic:216 attempt to index ? (a nil value)`，
> 手持 [TACZ] Phoenix Gunpack 武器即崩、再进世界秒崩循环。

## 0. 为什么 26.2 线也适用 / 与本线的对应关系

两线在 Lua 脚本底座上是**同一份**：

- `src/main/java/com/tacz/guns/resource/manager/ScriptManager.java` 在本修前与本修后
  均与 1.21.11 姊妹线**逐字节相同**（本修即把 26.2 侧文件改到与姊妹侧 `47960ae`
  后完全一致，`diff` 为空）；
- 依赖件同为 NeoForge jarJar vendor 的本地上游
  `libs/luaj-jse-3.0.1.jar`（两线 `build.gradle` 的 `jarJarLocalLib('luaj-jse-3.0.1.jar', …)`
  与 `implementation files("libs/luaj-jse-3.0.1.jar")` 同位同内容）。

因此：①两线同缺 Lua `string` 库（缺的是 vendor 上游 jar 里不存在的类所对应的
加载行）；②本修法两线通用；③此修复在 26.2 侧是**缺陷修复**（未带病发船的内容
不受影响，见 §3）。

## 1. 结论

**这是本移植（NeoForge jarJar-vendor 线）的兼容性缺陷，不是第三方枪包的错。**
官方 TaCZ 1.1.8 的脚本环境里有 `string` 库，Phoenix 等第三方枪包按官方环境编写，
`string.format / string.sub / ("…"):format()` 是合法常见写法；本线移植
`ScriptManager` 时把加载 string 库那一行丢了，Lua 全局里根本没有 `string` 表，
脚本第一次访问 `string.xxx`（或对字符串值做 `:method()`）就抛
`attempt to index ? (a nil value)`。`tick_heat` 是服务端主线程每 tick 裸调的高频
入口，于是表现为「拿到枪就 Ticking player 崩溃循环」。

报错文案 `attempt to index ? (a nil value)` 是 luaj 对「对 nil 取字段/调方法」的
措辞（`LuaValue#indexerror`），与「调用 nil」的 `attempt to call a nil value`
不同——签名指向**索引型访问**，`string` 全局缺失正产生这种签名。

## 2. 根因与证据

### 2.1 官方行为（语义权威侧）

官方 TACZ `ScriptManager#secureStandardGlobals`（`MCModderAnchor/TACZ` `1.20.1`
分支）其余库与注释逐行一致，唯一差异就是：

```java
globals.load(new JseStringLib());     // ← 官方有这一行
```

官方 `JseStringLib` 来自其 build.gradle 的
`minecraftLibrary(jarJar('com.github.FiguraMC.luaj:luaj-jse:3.0.8-figura'))`，
即官方用 **Figura fork luaj 3.0.8-figura**，该 fork 里有
`org.luaj.vm2.lib.jse.JseStringLib`。（出处同 1.21.11 姊妹线记录：2026-09-07 经
GitHub raw 拉取比对。）

### 2.2 本线为什么没有这一行

本线 `libs/luaj-jse-3.0.1.jar` 是**上游 Apache luaj 3.0.1**（jar 内 class 时间戳
2015-04-29，与上游 release 一致）。上游 3.0.1 的 jar 里：

- 有 `org/luaj/vm2/lib/StringLib.class`（连同 `byte/char/dump/find/format/gmatch/
  gsub/lower/len/match/rep/reverse/sub/upper` 内部类，本线已 `unzip -l` 核对）；
- **没有** `org/luaj/vm2/lib/jse/JseStringLib`。

上游等价物与安装惯用法（上游 `JsePlatform#standardGlobals`，tag `v3.0.1`）：
`globals.load(new StringLib());`，位置与官方 TaCZ 中 `JseStringLib` 完全同位
（`TableLib` 之后、`CoroutineLib` 之前）。`StringLib extends TwoArgFunction`，
其 `call(modname, env)` 安装 `string` 表并设置 `LuaString.s_metatable`——即
`string.format` 与 `("x"):sub(1,2)` 两种语法都依赖它。

**推断（不移除）**：移植者照抄官方代码时 `new JseStringLib()` 在本线 jar 里编译
不过，于是连库带行一起删了；环境静默劣化，R1/R2 均未暴露。

### 2.3 为什么这条分叉只在 NeoForge jarJar-vendor 线出现（姊妹对照）

姊妹项目 `TaCZ_Refabricated_Unofficial` 的三条线（`26.2(main)` / `26.1.2` /
`1.21.11`）的 `ScriptManager` **均有** `globals.load(new JseStringLib())`——因为
姊妹的 build.gradle 用 Fabric `include` 直接内嵌**官方同款**
`com.github.FiguraMC.luaj:luaj-jse:3.0.8-figura`，官方类在 classpath 里，照抄官方
代码天然编译通过。它们不存在「坏过再修」的提交痕迹。

分叉点在**依赖件**：NeoForge jarJar 不能照搬 Fabric `include`，本线
`build.gradle` 注释载明——`implementation files()` 不进发布 jar（真实启动器
`NoClassDefFoundError: org/luaj/vm2/LuaError`），ModDevGradle 2 拒绝 jarJar 无
JPMS 模块名的本地文件，于是走「vendor 本地 jar + 盖 `Automatic-Module-Name`」
的离线方案；vendor 的上游 `luaj-jse-3.0.1` 无 `jse.JseStringLib` → 该行未落地。
`git log -S JseStringLib` 仅命中本修复相关提交：本线历史从未有过 string 库加载，
非中途删除。

### 2.4 为什么自带默认枪包没暴露

`grep -rn "string\." src/main/resources --include=*.lua`（含 tacz_default 与
lrtactical 全部自带脚本）零命中——默认枪包脚本不用 `string` 库，所以 R1/R2 的
枪包实测全部通过。第三方枪包没有义务规避官方环境里存在的标准库。

## 3. 修复

`ScriptManager#secureStandardGlobals` 在官方同位补一行（含来源注释）：

```java
globals.load(new StringLib());
```

import 增加 `org.luaj.vm2.lib.StringLib`。脚本可见效果与官方一致：`string` 表
恢复、字符串元表恢复。改动后 26.2 侧文件与 1.21.11 姊妹侧 `47960ae` 后**逐字节
相同**。

### 兼容面与残余差异（诚实声明）

- 官方/姊妹是 Figura fork 3.0.8-figura，本线上游 3.0.1；两者 `string` 库的 Lua
  可见面（`byte/char/dump/find/format/gmatch/gsub/lower/len/rep/reverse/sub/upper`）
  一致；Figura fork 对 `string.format` 有 JVM 性能与对齐微调，未见 Lua 语义级
  差异（**未逐行 diff fork 源码，标注未逐项核对**）。
- 安全边界不变：依旧不装 Coroutine/Io/Os/Luajava，`loadfile/dofile` 等仍按 base
  库的沙箱语义处理。
- **本线运行期未实机验证**；编译门走 CI（`compile-check`/`build` workflow）。

## 4. 验收清单（实测时逐项打勾）

> **维护者实机测试 PASS（2026-09-07）** —— Phoenix 枪包崩溃场景本线复测通过
> （姊妹 1.21.11 线同字节修复亦已 PASS，见其 `b7eb785`）。

1. 装载 Phoenix Gunpack（Ra1k_gunpack v2.0.x），创造/生存拿取其任一武器
   （VSS / AK-74 / Groza 等），原地站 30 秒不崩（原症状为即时 `Ticking player`）；
2. 对该武器射击至过热锁定，散热恢复正常（验证 `tick_heat` 全流程）；
3. 默认枪包回归：默认武器射击/换弹/过热/拉栓正常（本修复对默认包应为零影响）；
4. 服务端日志无新增 `ScriptLoader`/`ScriptAPI` warn；
5. 客户端状态机动画正常（同一 `ScriptManager`，客户端一并恢复 string 库）。

## 5. 后续建议（未实施，另立工单）

脚本调用点（至少 `tick_heat / tick_bolt / tick_reload / shoot` 等每 tick 高频路径）
目前对 `LuaError` 无捕获，任何第三方包的脚本缺陷仍会崩整个游戏/服务端。可评估：
捕获 `LuaError` → 按「脚本+函数」限频 warn（带包名与函数名）→ 回退内置默认行为
（如 `defaultTickHeat`）。属行为面变更，需按宪章另走评审。

可选对齐项：将 vendor 依赖从上游 luaj 3.0.1 换成官方/姊妹同款 Figura fork
`com.github.FiguraMC.luaj:luaj-jse:3.0.8-figura`，可一并消除 3.0.1 → 3.0.8 的
版本差与 fork 差异；属依赖面变更，风险与收益另行评估，不并入本热修。
