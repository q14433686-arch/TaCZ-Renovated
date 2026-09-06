# Lua string 库修复适配记录（NeoForge 26.1.2，2026-09-06 UTC）

## 1. 时间窗与逐提交取舍

本次按接单时刻固定最近 24 小时：**2026-09-05 21:36:49 至 2026-09-06 21:36:49 UTC**。
来源分支 `arena/01a07887-tacz-renovated` 固定在
[`ccdd9b7c`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/ccdd9b7c25234cb98b485c1e89e95d5c8d214e38)。
本地基线为 `68b1857c2579a9ee5112688ece0d3db621c7b34f`，工作分支始终为
`arena/01a078a6-tacz-renovated`；只 fetch 来源历史作对照，未切换分支或整批 cherry-pick。

| 来源提交（提交时间 UTC） | 内容 | 处理 |
|---|---|---|
| [`47960aec`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/47960aec11c83baa89a6c6d873c50825dbc00367)（09-06 21:19:04） | `ScriptManager` 补载 StringLib，附更新日志与审计 | 移植代码语义；文档按 26.1.2 重写 |
| [`7d4f940d`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/7d4f940d0e913999bef8b2ef650c6ccd1852116f)（09-06 21:20:42） | 1.21.11 CI 编译日志 | 不移植；不能作为本线构建证据 |
| [`ccdd9b7c`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/ccdd9b7c25234cb98b485c1e89e95d5c8d214e38)（09-06 21:35:00） | 补充姊妹项目依赖差异的证据 | 核对本线与 Fabric 26.1.2 后纳入本记录，不复制旧审计快照 |

窗口内只有 **一项代码修复**。其父提交 `ea01f9f4` 为 09-03 的合并，不在窗口内；
不夹带更早的事件、搜索树、网络 codec 或渲染改动。

## 2. 移植前环境核对

| 项目 | 本线 | 来源线 |
|---|---|---|
| Minecraft | **26.1.2，未混淆** | **1.21.11，混淆版本** |
| NeoForge | **26.1.2.97** | **21.11.45** |
| Java toolchain | **25** | **21** |
| ModDevGradle | 2.0.144 | 2.0.144 |
| mod_version | `1.1.8+neoforge.26.1.2.R2` | `1.1.8+neoforge.1.21.11.R2` |
| LuaJ | 本地 `libs/luaj-jse-3.0.1.jar` | 同一 jar |
| 发布打包 | 给本地 jar 补 `Automatic-Module-Name` 后 jarJar | 同样的 jarJar 方案 |

依据为两线的 `gradle.properties` / `build.gradle` 与实际文件，而非分支名猜测。
本线 Gradle Wrapper 仍为 **9.2.1**；不更换版本、依赖、mappings、加载器接口或 jarJar 方案。

关键的相同点已逐字节核对：

- 本线基线与来源修复前 `ea01f9f4` 的 **整个 `ScriptManager.java` blob 相同**：
  `77689b38e34c950fc670bf9126d26d100bd0c461`。
- 两线 LuaJ jar 的 SHA-256 均为
  `9b1f0a3e8f68427c6d74c2bf00ae0e6dbfce35994d3001fed4cef6ecda50be55`。
- jar 内有 `org/luaj/vm2/lib/StringLib.class` 及其实现类，**无**
  `org/luaj/vm2/lib/jse/JseStringLib.class`（用 ZIP 类清单核对）。
- 本线 `CommonAssetsManager` 与 `ClientAssetsManager` 都创建此 `ScriptManager`；
  `prepare()` 每次先经 `initGlobals()` 调用该工厂，再装自定义常量与模块 preload。
  因而修复落在共用工厂，不另加客户端/服务端事件或单独打补丁到某个枪包。

**适用性结论**：此处是同一内置 LuaJ、同一工厂遗漏标准库的问题，不涉及跨 Minecraft
版本 API 迁移；可以共享这一库加载语义，不能照搬来源线的构建配置或验证结论。

## 3. 语义与 API 证据

### 3.1 姊妹 26.1.2 与官方的意图

重新读取姊妹项目 Fabric 26.1.2 固定提交
[`a1e469b6`](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial/commit/a1e469b62841da2097bff30fd65f3e9b9db24e0d)：

- [`ScriptManager#secureStandardGlobals()`](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial/blob/a1e469b62841da2097bff30fd65f3e9b9db24e0d/src/main/java/com/tacz/guns/resource/manager/ScriptManager.java)
  在 `TableLib` 之后加载 `JseStringLib`。
- [`build.gradle`](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial/blob/a1e469b62841da2097bff30fd65f3e9b9db24e0d/build.gradle)
  使用 Fabric `include` 内嵌 `com.github.FiguraMC.luaj:luaj-core/luaj-jse:3.0.8-figura`。
  **本线不是这个 fork，也不能照抄 Fabric 的 include / reload listener 接口。**
- 官方 TaCZ 1.20.1 固定提交
  [`b43eb84c` 的同一工厂](https://github.com/MCModderAnchor/TACZ/blob/b43eb84c38e9768d8e73c8b14f0b845669704b38/src/main/java/com/tacz/guns/resource/manager/ScriptManager.java)
  同样加载 `JseStringLib`，作为原始业务意图的交叉核对，不采用其旧游戏 API。

这不是从 Fabric 侧发现的近期热修；该姊妹快照本来就有 string 库。对更早移植者为何
漏掉加载行，不以猜测补写历史。本次能直接证明的是上述两个 NeoForge 基线都缺该行。

### 3.2 本线所用 LuaJ 3.0.1 的确切调用

新增调用完全属于第三方 LuaJ API，**没有新增 Minecraft / NeoForge API 调用**。
查证的是实际 vendored jar 和 LuaJ 官方源码 tag `v3.0.1`，固定提交
`70cb74b4d65851ef69240d35b58d9f8d20a73ed1`，不使用训练记忆作签名依据：

| API | 证据与语义 |
|---|---|
| `org.luaj.vm2.lib.StringLib#StringLib()` | [源码](https://github.com/luaj/luaj/blob/70cb74b4d65851ef69240d35b58d9f8d20a73ed1/src/core/org/luaj/vm2/lib/StringLib.java)；公开无参构造器，类继承 `TwoArgFunction` |
| `org.luaj.vm2.LuaValue#load(LuaValue): LuaValue`（`Globals` 继承） | [源码](https://github.com/luaj/luaj/blob/70cb74b4d65851ef69240d35b58d9f8d20a73ed1/src/core/org/luaj/vm2/LuaValue.java)；调用 `library.call(EMPTYSTRING, this)` |
| `StringLib#call(LuaValue, LuaValue): LuaValue` | 同上 StringLib 源码；建立 `env.string`、`package.loaded.string`，并在 `LuaString.s_metatable == null` 时安装字符串 `__index` 元表 |
| `org.luaj.vm2.lib.jse.JsePlatform#standardGlobals(): Globals` | [源码](https://github.com/luaj/luaj/blob/70cb74b4d65851ef69240d35b58d9f8d20a73ed1/src/jse/org/luaj/vm2/lib/jse/JsePlatform.java)；同样在 TableLib 后加载 StringLib，证明 3.0.1 的标准安装方式；**不替换为整个 standardGlobals()** |

新增 import 和工厂方法已用实际 jar、Java 25 目标字节码编译，并执行下述回归。

## 4. 最小修改与未扩大范围

在本线 `ScriptManager#secureStandardGlobals()` 的 `TableLib` 后增加：

```java
globals.load(new StringLib());
```

同时补 import 与简短的依赖差异注释。保留 `JseBaseLib / PackageLib / Bit32Lib /
TableLib / JseMathLib / LoadState / LuaC` 的原有顺序和接线。不改游戏 tick 行为，
不吞掉 `LuaError`，不替换 LuaJ，不修改 modId 或 `mod_version`。

需要明确保留的边界：

- **标准库恢复不等于 Figura fork 全部兼容**：本次只测试列出的 LuaJ 3.0.1 字符串行为，
  未逐项证明与 Figura 3.0.8 的格式化、编码等行为完全一致。
- **未额外加载库，不等于完整安全沙箱**：仍不加载 Coroutine / Io / Os / Luajava / Debug。
  不沿用来源文档关于 `loadfile/dofile` 沙箱的泛化表述；现有
  [`JseBaseLib#findResource(String): InputStream`](https://github.com/luaj/luaj/blob/70cb74b4d65851ef69240d35b58d9f8d20a73ed1/src/jse/org/luaj/vm2/lib/jse/JseBaseLib.java)
  本身能打开本地文件。本补丁不做安全隔离改造。
- **LuaString 元表是 JVM 共享状态**：上游只在 null 时设置，不主动清空它，也不宣称
  不同 manager 或 reload 后具有独立字符串元表。回归覆盖未篡改标准库情况下的连续初始化。
- 来源线记录的 Phoenix `ra1k_gun_logic:216` 崩溃是其用户报告，**本次没有取得该枪包的
  完整脚本并实机复现**；本线使用最小脚本证明缺库缺陷。不能仅凭同一 nil 报错文案断言
  所有第三方脚本异常都源于此处，更不能把本改动写成“所有枪包崩溃已修复”。

## 5. 本线验证（不继承来源 CI / 用户 PASS）

### 5.1 可重复的红绿回归

入口：[`scripts/test_script_globals.py`](../../scripts/test_script_globals.py)，
断言：[`scripts/tests/script_globals.lua`](../../scripts/tests/script_globals.lua)。
正常 JDK 25 环境执行：

```bash
python3 scripts/test_script_globals.py
```

测试提取**生产文件的 LuaJ imports 与原样工厂方法**，临时编译一个不依赖 Minecraft
启动的类；不另维护一份库列表，也不改变生产方法的可见性。

| 检查 | 实际结果 |
|---|---|
| 修改前同一工厂执行 `string.format` | **按预期失败**：`script_globals_0:3 attempt to index ? (a nil value)`，测试退出 1 |
| 加入 StringLib 后运行同一测试 | **通过** |
| string 的 format / sub / find / match / gsub / gmatch / byte / char / dump / len / lower / upper / rep / reverse | **通过**，含方法式 `:format` / `:sub` 和 dump/load 往返 |
| `package.loaded.string`、`require("string")`、preload 模块调用与 require 缓存 | **通过** |
| 原有 math / table / bit32 / base 能力，未加载库检查 | **通过** |
| 同一 JVM 连续新建 3 个 Globals，保留共享元表，各自的全局标记与 package 表不串用 | **通过**；不模拟真实 NeoForge reload 事件 |
| 47 个内置 Lua 脚本（含客户端/服务端和 LR 资源）的语法/字节码编译 | **通过**；没有执行其游戏逻辑 |

沙箱起初没有 Java。官方 JDK/Gradle 二进制下载也受网络阻挡；独立回归实际使用
**Temurin Java runtime 25.0.2+10**（PyPI `jdk4py==25.0.2.1` 内置运行时）+
**Eclipse Compiler 3.45.0**（npm `@vscjava/java-language-server@0.1.2` 内附的
`org.eclipse.jdt.core.compiler.batch_3.45.0.v20260224-0835.jar`），指定 `--release 25`。
通过测试的 `--java` / `--javac` 参数指向这两个工具；工具和临时产物均在仓库外的缓存/
临时目录，未提交 jar 或修改构建依赖。这不是完整 ModDevGradle 构建环境。

### 5.2 静态门禁与构建边界

- `bash scripts/check_release_consistency.sh --strict`：**通过**；版本仍为本线 R2，
  修复只记入 CHANGELOG 未发布区。
- `.github/workflows/consistency.yml` 同款本地文档链接检查：**通过**。
- `git diff --check`：**通过**。
- 完整 `compileJava`：**未完成**。实际尝试 Gradle Wrapper 时，在下载
  `https://services.gradle.org/distributions/gradle-9.2.1-bin.zip` 阶段发生
  `SSLHandshakeException: Remote host terminated the handshake`；NeoForge Maven
  的直接探测也发生 TLS 连接失败。未通过降级版本、绕开依赖或改仓库配置伪造成功。
- **未运行本工作分支的 GitHub CI，也未完成整包 build 或游戏实机验证**。
  来源 `7d4f940d` 的成功日志没有复制到本线 `build-reports/`。

## 6. 游戏实机待验收

1. Minecraft **26.1.2 + NeoForge 26.1.2.97**，使用包含本补丁的新构建、备份世界，
   装 Phoenix 等会调用 string 的枪包：持枪持续 tick、射击到过热及散热恢复不因缺库报错。
2. 默认枪包的射击、换弹、拉栓、过热回归；检查服务端脚本加载与 tick 日志。
3. 客户端含字符串调用的状态机、F3+T 资源重载，以及专用服务器 `/tacz reload` 后的
   脚本重新加载；确认没有新增 `ScriptLoader` / `ScriptAPI` 警告。

上述均是**待实机清单**，独立 Lua 测试不能代替加载器、枪包或联机验收。
