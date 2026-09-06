<!-- release-version: 1.1.8+neoforge.26.1.2.R3 -->
# TaCZ: Renovated — Minecraft 26.1.2 / NeoForge（R3）

> **非官方社区移植，不是 TaCZ 官方发布，也未获 TACZ Dev Team 审核或背书。
> 本移植的问题请提交到本仓库，不要打扰原作者。**

## 环境

- Minecraft：**26.1.2**
- NeoForge：**26.1.2.x**（开发基于 **26.1.2.97**）
- Java：**25+**
- Mod：**`1.1.8+neoforge.26.1.2.R3`**
- 必需前置：**无**

不同 Minecraft 版本的文件不能混用；这不是 1.21.11 的 R3 包。

## 本次变化（相对 R2）

- **Lua `string` 标准库恢复**：共用脚本环境补载内置 LuaJ 3.0.1 的 `StringLib`，
  修复 `string.format` 等函数因缺库而报 nil 错误，并恢复字符串方法式调用。
  不升级为 Figura fork，不承诺其全部行为完全等价。
- **创造模式搜索同步的防御性修复**：枪包同步重建标签内容后同步重建搜索树；
  保留 26.1.2 的触发时序与实现，不将其他版本的复现过程当成本线的复现日志。
- **事件处理器接线修复**：跨维度枪械状态重置、服务端 BURST / 异步任务 tick、
  配置加载/热重载、重生自动装弹、子弹射钟/碎玻璃、界面快捷栏遮挡与持枪挖掘拦截。
- **收枪动画修复**：恢复旧物品的渲染保留窗口，并处理快速连续切换时的窗口接管。
- **发布工具**：按本线 tag 构建、L0 门禁、Lua 回归及 commit / SHA-256 留痕的
  Release 工作流已由维护者上线，默认创建草稿，不覆盖已有 Release 或同名资产。

详细变化见本线 [CHANGELOG](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.1.2/CHANGELOG.md)。

## 验证范围

- **本线 R3 修复：维护者实机测试 PASS（2026-09-07）**。本条按维护者本轮确认记录，
  不是把 1.21.11 的 PASS 自动复制过来；确认来源与本线 R3 构建结果见
  [R3 签收记录](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.1.2/docs/records/R3_CONFIRMATION_2612_20260907.md)。
- Lua 修复另有独立 Java 25 / LuaJ 红绿回归，涵盖字符串 API、require/preload、连续
  创建脚本环境；47 个内置 Lua 脚本可编译（**独立测试不执行游戏逻辑**）。发布门禁另有
  17 项离线回归，不代替实机测试。
- **构建与发布验收分开记录**：R3 编译/完整构建以签收记录中的实际 CI 提交为准；
  正式发布仍须在最终 tag 上执行 build 和 L0。工作流已上线不表示发布上传已运行。
- **不扩大 PASS 范围**：没有新增枪包逐版本、光影/视角模组组合或部署形态的逐项记录。
  LAN 双人加入、原生专服等发布检查仍按发布规范逐项核对；不能用历史 R1/R2 记录
  代替最终构建的验收。混合服、代理、面板等环境没有因此获得新的兼容性保证。

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
