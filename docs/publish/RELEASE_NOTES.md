<!-- release-version: UNRELEASED -->
# TaCZ: Renovated — Minecraft 26.1.2 / NeoForge（未发布草稿）

> **非官方社区移植，不是 TaCZ 官方发布，也未获 TACZ Dev Team 审核或背书。
> 本移植的问题请提交到本仓库，不要打扰原作者。**
>
> 本文是 R2 之后的发布正文草稿，**不是 R3 已发布或已实测的声明**。
> 当前 `mod_version` 仍为 `1.1.8+neoforge.26.1.2.R2`；发布前须先确定新版本、
> 同步 README / CHANGELOG、核对本线测试记录，再更新本段和首行 `release-version`
> 为最终完整版本号。发布预检会拒绝 `UNRELEASED`，不能拿这份草稿替换已发布的 R2。

## 环境

- Minecraft：**26.1.2**
- NeoForge：**26.1.2.x**（开发基于 **26.1.2.97**）
- Java：**25+**
- 必需前置：**无**
- Mod：**尚未确定新的发布版本**（以最终 tag 内 `gradle.properties` 为准）

不同 Minecraft 版本的文件不能混用；这不是 1.21.11 的 R3 包。

## 本次变化（相对 R2；发布前按最终 CHANGELOG 复核）

- **Lua `string` 标准库恢复**：共用脚本环境补载内置 LuaJ 3.0.1 的 `StringLib`，
  修复 `string.format` 等函数因缺库而报 nil 错误，并恢复字符串方法式调用。
  不升级为 Figura fork，不承诺其全部行为完全等价。
- **创造模式搜索同步的防御性修复**：枪包同步重建标签内容后同步重建搜索树；
  26.1.2 的触发时序与已复现的 1.21.11 / 26.2 不同，不能直接搬用其复现或 PASS 结论。
- **此前已在本线接线的事件处理器修复**：跨维度枪械状态重置、服务端 BURST / 异步任务
  tick、配置加载/热重载、重生自动装弹、子弹射钟/碎玻璃、界面快捷栏遮挡与持枪挖掘拦截。
- **收枪动画修复**：恢复旧物品的渲染保留窗口，并处理快速连续切换时的窗口接管。
- **发布工具**：提供按本线 tag 构建、L0 门禁、Lua 回归及 commit / SHA-256 留痕的
  Release 工作流；工作流部署状态不等于已完成模组实机验证。

详细变化以本线 [CHANGELOG](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.1.2/CHANGELOG.md)
为准；不要混入 1.21.11 特有的渲染修复列表。

## 验证范围

- Lua 修复已做独立 Java 25 / LuaJ 红绿回归，涵盖字符串 API、require/preload、连续
  创建脚本环境；47 个内置 Lua 脚本可编译（**未执行游戏逻辑**）。记录见
  [Lua 移植审计](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.1.2/docs/records/SCRIPT_STRINGLIB_RESTORE_2612_20260906.md)。
- **本次完整模组构建、L0 产物检查与实机结果，发布前必须以最终 tag 对应记录补填**；
  不能把其他提交的 CI 通过写成本构建的通过。
- **本线待实机**：Phoenix 等第三方枪包、默认枪械射击/换弹/过热、客户端状态机、
  F3+T 与 `/tacz reload`、LAN 双人加入及原生 NeoForge 专用服务器。
- 1.21.11 已写入其记录的实机 PASS **不跨版本继承**；历史 R1/R2 测试也不能替代本次复测。

## 安装与已知边界

将对应版本的 jar 放入 `mods/`，先备份世界和枪包。现代枪包放入 `tacz/`；
旧布局包备份后放入 `tacz_backup/` 并执行 `/tacz convert`。联机枪包需双端安装，
服务端执行 `/tacz reload`，客户端新增包按 F3+T 重载。

不支持明确依赖 TacZ:Arcana 的内容。LRTactical 不含 flash_shield 或原作完整美术资源。
混合服、代理与面板环境的问题应先在原生 NeoForge 专服复现；兼容范围见本线
[兼容矩阵](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.1.2/docs/COMPATIBILITY.md)。

## 许可与来源

- [源码与对应 tag](https://github.com/q14433686-arch/TaCZ_Renovated) ·
  [问题反馈](https://github.com/q14433686-arch/TaCZ_Renovated/issues)
- [原始 TaCZ](https://github.com/MCModderAnchor/TACZ) ·
  [直接上游](https://github.com/Sh1roCu/TACZ-Refabricated) ·
  [Fabric 姊妹语义主线](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial)
- [NeoForge 移植骨架参考（GPL-3.0）](https://github.com/MUKSC/TACZ-1.21.1)，未采用其渲染代码。
- [内置 TML 上游（GPL-3.0）](https://github.com/VellEagle/TacZMeshLoader)

代码 GPL-3.0-only；默认枪包资源 CC BY-NC-ND 4.0；LuaJ 为 MIT，commons-math3 为
Apache-2.0。完整说明见
[LICENSES.md](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.1.2/LICENSES.md)。
Release 的 Source code 归档必须对应所挂二进制；热修使用新版本与新 tag，不覆盖旧资产。
