# 枪包脚本环境缺 `string` 库修复（1.21.11 线，2026-09-07）

> 症状（CurseForge [TACZ] Phoenix Gunpack 用户报告，玩家 `sunzukiTH`）：
> `Ticking player` → `org.luaj.vm2.LuaError: ra1k_gun_logic:216 attempt to index ? (a nil value)`，
> 崩溃路径 `LivingEntity.tick → tacz mixin onTickServerSide → LivingEntityHeat#tickHeat:19
> → ModernKineticGunItem#tickHeat:213-214 → LuaClosure`（tacz 1.1.8+neoforge.1.21.11.R2）。
> 手持该枪包武器即崩、再进世界秒崩循环。
>
> 修复落点：`com.tacz.guns.resource.manager.ScriptManager#secureStandardGlobals`
> —— 补回被移植过程丢掉的 Lua `string` 库加载。

## 1. 结论

**这是本移植线的兼容性缺陷，不是 Phoenix 枪包的错。** 官方 TaCZ 1.1.8 的脚本
环境里有 `string` 库，第三方枪包（Phoenix 等）按官方环境编写，使用
`string.format / string.sub / ("…"):format()` 等是合法且常见的写法；本线移植
`ScriptManager` 时把加载 string 库的那一行丢了，Lua 全局里根本没有 `string`
表，脚本第一次访问 `string.xxx`（或对字符串值做 `:method()` 调用）就抛
`attempt to index ? (a nil value)`。`tick_heat` 是每 tick 在服务端主线程裸调的
高频入口，于是表现为「拿到枪就 Ticking player 崩溃循环」。

luaj 对「对 nil 取字段/调方法」的报错文案就是 `attempt to index ? (a nil value)`
（`LuaValue#indexerror`，报告堆栈里的 `LuaValue.gettable/get` 与此吻合），
与「调用 nil」的 `attempt to call a nil value` 不同——报告的签名指向
**索引型访问**，`string` 全局缺失正产生这种签名。

## 2. 根因与证据

### 2.1 官方行为（语义权威侧）

官方 TACZ `ScriptManager#secureStandardGlobals`（仓库 `MCModderAnchor/TACZ`，
`1.20.1` 分支，2026-09-07 经 GitHub raw 拉取比对）：

```java
private static Globals secureStandardGlobals() {
    Globals globals = new Globals();
    globals.load(new JseBaseLib());
    globals.load(new PackageLib());
    globals.load(new Bit32Lib());
    globals.load(new TableLib());
    globals.load(new JseStringLib());     // ← 官方有这一行
    // No CoroutineLib
    globals.load(new JseMathLib());
    // No JseIoLib
    // No JseOsLib
    // No LuajavaLib
    LoadState.install(globals);
    LuaC.install(globals);
    return globals;
}
```

其余库与注释逐行一致，唯一差异就是这一行。

官方的 `JseStringLib` 来自其 build.gradle（同分支，第 197–202 行）：

```groovy
minecraftLibrary(jarJar('com.github.FiguraMC.luaj:luaj-jse:3.0.8-figura')) { ... }
```

即官方用 **Figura fork 的 luaj 3.0.8-figura**，该 fork 里有
`org.luaj.vm2.lib.jse.JseStringLib`。

### 2.2 本线为什么没有这一行

本线 `libs/luaj-jse-3.0.1.jar` 是 **上游 Apache luaj 3.0.1**（jar 内 class 时间戳
2015-04-29，与上游 release 一致）。上游 3.0.1 的 jar 里：

- 有 `org/luaj/vm2/lib/StringLib.class`（连同 `format/gsub/gmatch/sub/find/rep/…`
  内部类，已 `unzip -l` 核对）；
- **没有** `org/luaj/vm2/lib/jse/JseStringLib`（jse 包内逐类核对）。

上游等价物与安装惯用法（上游 `JsePlatform#standardGlobals`，tag `v3.0.1`，
第 96–105 行）：`globals.load(new StringLib());`，位置与官方 TaCZ 中
`JseStringLib` 完全同位（`TableLib` 之后、`CoroutineLib` 之前）。
`StringLib extends TwoArgFunction`，其 `call(modname, env)` 安装 `string` 表并
设置 `LuaString.s_metatable`（上游 `StringLib.java` 第 62–105 行），即
`string.format` 与 `("x"):sub(1,2)` 两种语法都依赖它。

**推断（不移除）**：移植者照抄官方代码时 `new JseStringLib()` 在本线 jar 里
编译不过，于是连库带行一起删了；环境静默劣化，R1/R2 均未暴露。

### 2.4 姊妹线对照（2026-09-07 补充）：不是静默修复，是从来没坏

姊妹项目三条线（`26.2(main)` / `26.1.2` / `1.21.11`）的 `ScriptManager`
**均有** `globals.load(new JseStringLib())`——因为姊妹的 build.gradle 用
Fabric `include` 直接内嵌**官方同款** `com.github.FiguraMC.luaj:luaj-jse:3.0.8-figura`，
官方类就在 classpath 里，照抄官方代码天然编译通过。姊妹不存在「坏过再修」
的提交痕迹。

本线分叉点在**依赖件**：NeoForge jarJar 不能照搬 Fabric `include`，
`build.gradle`（第 141–180 行）注释载明——`implementation files()` 不进发布
jar（真实启动器 `NoClassDefFoundError: org/luaj/vm2/LuaError`），ModDevGradle 2
拒绝 jarJar 无 JPMS 模块名的本地文件，于是走「vendor 本地 jar + 盖
`Automatic-Module-Name`」的离线方案，vendor 的上游 `luaj-jse-3.0.1` 无
`jse.JseStringLib` → 该行未落地。`git log -S JseStringLib --all` 仅命中本修复
提交：本线历史从未有过 string 库加载，非中途删除。

### 2.5 为什么自带默认枪包没暴露

`grep -rn "string\." src/main/resources --include=*.lua`（含服务端 gun_logic 与
客户端状态机全部自带脚本）零命中——默认枪包脚本不用 `string` 库，所以
R1/R2 的枪包实测（`SERVER_TEST_20260821_*`）全部通过。第三方枪包没有义务
规避官方环境里存在的标准库，Phoenix 的 `assets/ra1k/scripts/gun_logic.lua`
在其 `tick_heat`（第 216 行）用到即崩。

## 3. 修复

`ScriptManager#secureStandardGlobals` 在官方同位补一行（含来源注释）：

```java
globals.load(new StringLib());
```

import 增加 `org.luaj.vm2.lib.StringLib`。脚本可见效果与官方一致：
`string` 表恢复、字符串元表恢复。

### 兼容面与残余差异（诚实声明）

- 官方是 Figura fork 3.0.8-figura，本线上游 3.0.1；两者 `string` 库的
  Lua 可见面（`byte/char/dump/find/format/gmatch/gsub/lower/len/rep/reverse/
  sub/upper`）一致；Figura fork 对 `string.format` 有 JVM 性能与对齐微调，
  未见到 Lua 语义级差异（未逐行 diff fork 源码，标注**未逐项核对**）。
- 安全边界不变：依旧不装 Coroutine/Io/Os/Luajava，`loadfile/dofile` 等仍按
  base 库的沙箱语义处理。
- **运行期未实机验证**；编译门走 CI（`compile-check`/`build` workflow）。

## 4. 验收清单（实测时逐项打勾）

1. 装载 Phoenix Gunpack（Ra1k_gunpack v2.0.x），创造/生存拿取其任一武器
   （VSS / AK-74 / Groza 等），原地站 30 秒不崩（原症状为即时 `Ticking player`）；
2. 对该武器射击至过热锁定，散热恢复正常（验证 `tick_heat` 全流程）；
3. 默认枪包回归：默认武器射击/换弹/过热/拉栓正常（本修复对默认包应为零影响）；
4. 服务端日志无新增 `ScriptLoader`/`ScriptAPI` warn；
5. 客户端状态机动画正常（同一 `ScriptManager`，客户端一并恢复 string 库）。

## 5. 后续建议（未实施，另立工单）

脚本调用点（至少 `tick_heat / tick_bolt / tick_reload / shoot` 等每 tick 高频
路径）目前对 `LuaError` 无捕获，任何第三方包的脚本缺陷仍会崩整个游戏/服务端。
可评估：捕获 `LuaError` → 按「脚本+函数」限频 warn（带包名与函数名）→ 回退
内置默认行为（如 `defaultTickHeat`）。属行为面变更，需按宪章另走评审。

可选对齐项：将 vendor 依赖从上游 luaj 3.0.1 换成官方/姊妹同款 Figura fork
`com.github.FiguraMC.luaj:luaj-jse:3.0.8-figura`（官方 TACZ 本身即 maven jarJar
该构件，需接 FiguraMC maven 仓库；MDG 远程 jarJar 可行性另验）。可一并消除
3.0.1 → 3.0.8 的版本差与 fork 差异；属依赖面变更，风险与收益另行评估，
不并入本热修。
