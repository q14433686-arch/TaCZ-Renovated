**环境：较新的 Minecraft 版本 · NeoForge · 无必装前置 · 具体支持范围以当前发布文件的兼容性标签为准**

> **Unofficial NeoForge port of TaCZ (Timeless & Classics Guns: Zero). Not an
> official TaCZ release; not reviewed or endorsed by the TACZ Dev Team. GPL-3.0.**
>
> **非官方社区移植，不是 TaCZ 官方发布，也未获 TACZ Dev Team 审核或背书。
> 问题请报本仓库 Issues，不要打扰原作者。**

### 这是什么

TaCZ 枪械 mod 面向 Minecraft 26.2 / NeoForge 的社区移植，代码开源（GPL-3.0-only）、
谱系可审计（26.1.2 线 R1 完整基线前滚）。游戏语义源自姊妹项目
[TaCZ Refabricated Unofficial](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial)（Fabric 姊妹项目，26.2 线为语义权威）。

### 本次更新（相对上一版 R2）

- **修复：第三方枪包脚本一使用 `string.*` 即崩服**（实测：Phoenix Gunpack 持枪即
  `Ticking player` 崩溃循环；官方 TaCZ 上正常）——脚本环境补回 Lua `string` 库，
  `string.format` 与 `("…"):method()` 写法恢复可用；
- **修复：创造模式搜索栏搜不到任何物品**（含 tacz / lrtactical 全部条目）——
  枪包同步后补建 `SessionSearchTrees` 搜索树；
- **修复：开镜 mesh 枪身/配件裁剪判据时序**——高模枪身在二次渲染下从未被镜内
  孔径裁掉，现按孔径正确裁切；
- **修复：七个「静默失效」事件处理器批量接线**——跨维度枪械状态机不刷新、
  服务端 BURST 连发只出第一发、第三方生物自定义爆头 AABB 与交互键黑白名单配置
  不加载等；
- 以上四批修复均经维护者实机测试 PASS（2026-09-07）。R2 起的内容（LRTactical 内置层、
  镜内画中画 PIP、内置 TacZ Mesh Loader GPU 烘焙、镜内裁手/文字、Iris 时域隔离等）
  见仓库 [CHANGELOG](https://github.com/q14433686-arch/TaCZ_Renovated/blob/26.2/CHANGELOG.md)。

### 实测覆盖（如实分级）

✅ **本次四批修复**：维护者实机测试 PASS（含 Phoenix Gunpack 崩溃场景复现与复测）
✅ **历史基线**（日志归档于源码仓库 docs/records/）：单机 · 局域网双客户端 ·
专用服务器（生产 jar + 双客户端，含 /give、工作台合成、枪包热重载）
❌ **本次未重跑**：面板服、Velocity 代理、混合服（Youer/Arclight 系）、Geyser——
这些环境的问题**须先在原生 NeoForge 专服复现**后再提交。

### 安装

1. 安装 Minecraft 26.2 与 NeoForge `26.2.0.64`（release；以发布文件兼容性标签为准）；
2. jar 放入 `mods/`（无必装前置）；首次启动默认枪包自动解压到 `游戏目录/tacz/`；
3. 第三方枪包放 `游戏目录/tacz/`；联机需**双端安装**同一枪包
   （服务端 `/tacz reload` 生效；客户端新增包按 F3+T 重载）。

### 反馈

[Issues](https://github.com/q14433686-arch/TaCZ_Renovated/issues) 按模板提交，
必附完整 latest.log（联机问题双端都要）。

### 许可与源码

- 代码 **GPL-3.0-only**：本 Release 的 Source code 归档即完整对应源码
  （构建脚本、文档、审计记录齐全）；
- 默认枪包资源 **CC BY-NC-ND 4.0**（沿用上游声明）；内嵌 LuaJ（MIT）、
  commons-math3（Apache-2.0）；内置 TacZ Mesh Loader（GPL-3.0，源自
  VellEagle/TacZMeshLoader），详见仓库 `LICENSES.md`；
- 谱系：MCModderAnchor/TACZ → Sh1roCu/TACZ-Refabricated →
  TaCZ_Refabricated_Unofficial → 本仓库（LRTactical 原作：LesRaisins-Studios，
  Programmer xjqsh / Artist LeComte，代码 GPL-3.0）。

本项目按"原样"提供，不附带担保。
