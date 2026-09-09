# Fabric 26.2(main) 全量语义同步回执：`1b4af9f`（2026-09-09）

- **语义来源**：`q14433686-arch/TaCZ_Refabricated_Unofficial` 的
  `26.2(main)`，GitHub compare
  `dee2578d3ffe0f373543f1d3fa9fb9b8d453f6e0...1b4af9f71d6918d9c00a775a52f6940634a21f47`。
- **本线**：TaCZ Renovated 26.2 / NeoForge，`arena/01a07f93-tacz-renovated`。
- **要求**：这是从上述明确取货点到 tip 的**全量语义核对**，不是把 Fabric
  文件、lifecycle、access widener、Loom 配置或其日志机械复制过来。游戏、渲染、网络、
  配置和诊断语义必须逐项有去处；原有 recipe-viewer 修复不得倒退。
- **compare 边界**：API 返回 `ahead_by=57`、`total_commits=57`、最终 tree 的
  `files=58`。本回执同时列出全部 57 笔和全部 58 条路径。不要用未筛选的 merge
  祖先遍历替代这个 compare 边界：那会把 merge second-parent 的历史搬运链重复算入，
  而不会增加本次 tip 相对基线的最终树差异。

## 1. 结论与状态口径

本次真正缺失的最终功能是 Fabric PR #95 的 **Fix-A Iris 26.2 终态**。它现在已按
NeoForge 类型/配置层落入本线：默认只给 HAND 程序注入 scope-mask GLSL，配置可选
`HAND_ONLY` / `ALL` / `OFF`，并为每个被注入 GL program 分配不会与已有 active sampler
冲突的 texture unit。旧的全程序 `@ModifyVariable` 路径和 Fabric 中间的 ThreadLocal
桥均不保留。

PR #86/#87（mesh draw-time clip、put-away `keep()`）和 PR #94（用户日志可见问题集）
经源代码逐项复核后均已在本线有等价终态，故不重复改动。Fabric 的 CI 日志、上传日志、
另分支 patch、发布渠道和 lineage 文字不是本线游戏功能；有价值的机制、诊断和测试条件
被转写到本记录，而不是把另一仓的 PASS 署到 NeoForge 名下。

**验证等级（截至本记录）**：静态源代码/资源 JSON/descriptor 对照完成；本沙箱最初没有
JDK，下载 JDK 的 release-asset 与 apt 源均不可用，因此没有本地 Gradle 或游戏内运行。
Fabric 的 Fix-A 实机结论只是外部旁证，**不是本线 PASS**。提交后 CI 和 §7 的 NeoForge
实机矩阵仍是必经门。

### 标记说明

| 标记 | 含义 |
|---|---|
| **P** | 本次移植的最终语义，已写入本线源码/资源/配置。 |
| **E** | 本线已有等价终态；保留更晚的本线增强，不重复覆盖。 |
| **S** | 上游中间修订已被同一 compare 范围内的终态推翻，不能移植。 |
| **D** | 文档/调查/诊断证据已在本线归档或摘要，不能将 Fabric 环境或结果直接复制。 |
| **N** | Fabric-only CI、上传物、发布物或另分支载体，对本线不适用。 |

## 2. Iris 目标 descriptor 的独立复核

这一步在改 optional mixin 前完成，避免仅依据 Fabric mixin 表面猜 target：

1. 拉取 Iris 官方 `26.2` branch 的 commit
   `48d0c259895487b281651de1bc058bf7d6814daa`；根 `build.gradle.kts` 明确声明
   `MOD_VERSION = "1.11.2"`。
2. Iris 的 NeoForge module 在 `neoforge/build.gradle.kts` 把 `:common` 的 main source
   加入编译；因此 `common/.../pipeline/programs/ShaderCreator.java` 是 NeoForge/Fabric
   共用的权威源码，不是 Fabric-only 类。
3. `ShaderCreator#link(String, String, String, String, String, String, VertexFormat, boolean)`
   内按 vertex / geometry / tess-control / tess-eval / fragment 调用 `createShader`；fragment
   的精确调用是
   `createShader(name, ShaderType.FRAGMENT, fragment)`。私有静态 callee 的 JVM descriptor 是：

   ```text
   Lnet/irisshaders/iris/pipeline/programs/ShaderCreator;
   createShader(Ljava/lang/String;Lnet/irisshaders/iris/gl/shader/ShaderType;Ljava/lang/String;)I
   ```

4. 本线 `IrisShaderCreatorMixin` 使用该 descriptor 的 `@ModifyArgs`，再以运行时
   `ShaderType` enum name 为 `FRAGMENT` 作 guard，**不依赖 ordinal**。这同时把 program
   name 与 fragment source 放在同一调用，消除已失败的跨方法 ThreadLocal 时序桥。

没有把下载到的 release jar 的 hash 伪称为已核；上面是同版本、同 NeoForge common module
的官方源 target 复核。CI/运行期 mixin application 仍在 §7 关闭。

## 3. 已落地的 Fix-A 语义

| 本线文件 | 最终行为 |
|---|---|
| `IrisShaderCreatorMixin` | `link` 中只在 fragment `createShader` 调用改 arg 2。默认 `HAND_ONLY` 用 `Locale.ROOT` 大小写无关的 `contains("hand")` 同时覆盖 `hand_cutout` 与 `gbuffers_hand`；`ALL` 是显式诊断/兼容对照，`OFF` 完全不注入。保留注释感知的 `void main() {` 定位、幂等检查、fragment/HAND/world 计数和完整管线零 HAND 的 WARN。 |
| `IrisScopeMaskState` | 首次 setup 扫描 active sampler，选最高未占用 unit 写入 `tacz_ScopeMaskSampler`；mode=0 也固定 sampler，避免默认 unit 0 留存。无可用 unit 则别名 2D 主贴图并强制该 program mode=0。绑定后恢复原 active texture 并 `glBindSampler(unit, 0)`；pipeline rebuild 清 unit/mode/diagnostic cache；debug 时输出 sampler 表和 `glValidateProgram`。 |
| `RenderConfig` | NeoForge `ModConfigSpec.EnumValue<IrisScopeMaskInjection>`，key 为 `IrisScopeMaskInjection`，默认/异常回退均为 `HAND_ONLY`。 |
| `RenderClothConfig` + `en_us.json` + `zh_cn.json` | Render 页 enum selector 及双语说明；提示改档后重载 shader pack。 |
| `IrisGlCommandEncoderMixin` / `IrisExtendedShaderMixin` | 已经与 Fabric tip 所需的 pass capture / setup write-order 语义对齐，特意不重复改。 |

本仓保留的独立安全小差异：当 `applyToShaderProgram` 尚未观察到 `GlRenderPass` 时，
`resolveMaskTextureId` 先判空再回退 `ScopeMaskTarget`，避免正常 fallback 走一次反射
`NullPointerException`；不改变 Fabric 终态的纹理来源或 mode 语义。

CI 提案并非缺件：比较 `cmp` 结果为逐字相同：

```text
.github/workflows/build.yml          SHA-256 998eb4effd88bec1e4971d7a7ace35909a713a3365dcda18dfea648e1191ad52
.github/workflows/compile-check.yml  SHA-256 2415b3d8b11b7638b7100f69eb386b9925c01666069a16b3abbbb7fae8d2ff5d
```

## 4. PR #86/#87/#94 已有等价功能的逐项核对

| Fabric 终态意图 | 本线等价状态 / 不重复理由 |
|---|---|
| mesh 高模枪身/配件应在**绘制期**读 frame mask snapshot，而非 geometry 已清空后的 submit 判据 | `ScopeMaskRenderer#viewmodelClipMaskThisFrame`、`ScopeBodyRenderTypes#maskReadyForViewmodelAtDraw/clipForViewmodelAtDraw`、`PolyMeshGpuRenderer` 两处 draw path 已在役；本线记录 `BUG_MESHGUNBODY_SCOPE_CLIP_RERENDER_20260902.md` 还含后续实机 PASS。 |
| 收枪旧视模保留至 put-away 窗口；最新一次切枪接管，且只对 initialized state machine 开窗 | `LocalPlayerDraw#doPutAway`、`AnimateGeoItemRenderer#hasInitializedStateMachine`、`ItemInHandRendererMixin#keep` 已是 `32af402` 终态；详见 `REFAB_SYNC_PUTAWAY_KEEP_R6_20260902.md`。 |
| gun-smith table 的 `NOT_PLACEABLE` recipe 不应产生 vanilla finalize warning | `GunSmithTableRecipe#isSpecial()` 已返回 `true`，并说明其不会进入 vanilla recipe book placement。 |
| Glock 17 过渡 sound effects 不应重复触发 | 本线 `glock_17.animation.json` 与 Fabric tip 无 diff。 |
| interact-key whitelist 需覆盖 boat/raft/chest variants | Fabric 使用 `#minecraft:boat` + optional chest entries；本线在固定 MC 26.2 直接列全体 oak/spruce/birch/jungle/acacia/dark_oak/mangrove/cherry/pale_oak boats、bamboo raft 及全部 chest variants。集合语义相同，且该版本 id 均存在。 |
| scope mask 空 geometry warn 只在主手拿带 scope 的枪时触发 | `ScopeMaskRenderer#isMainHandGunWithScope()` 已同时检查 player、main hand、`IGun`、装配/内置 scope 和 empty attachment。 |
| 不要把所有 common/entity pipeline 全局误分配到 Iris HAND | 全源搜索确认本线没有 `assignCommonEntityPipelinesToHandIfNeeded` / `assignCommonEntity` 等遗留路径；仅自定义 scope/HAND render pipeline 使用显式 `IrisCompat.assignScopePipelineToHand`。`MuzzleFlashRender`、`ShellRender`、`PolyMeshGpuRenderer` 均未恢复 Fabric 删除的全局赋值。 |

这组已有件与本次 Iris port 无冲突：scope text 的 `pipeline/scope_text_clipped` 仍映射为
mode 2；现有 `hasMaskThisFrame()` / `hadMaskLastFrame()` 快路径仍保留，确保松开 ADS 的
下一帧会擦掉同一 HAND program 中残留的 mode。

## 5. 58 条最终路径逐项处置

| # | Fabric compare path | 本线处置 |
|---:|---|---|
| 1 | `AGENTS.md` | **D** — Fabric 协作/CI 文字；本线纪律已在本记录说明。 |
| 2 | `LICENSES.md` | **D** — Fabric R3 许可文案；无本次可执行语义。 |
| 3 | `README.md` | **D** — Fabric 发布/PIP 首页文案；不覆盖 NeoForge 自身发布事实。 |
| 4 | `build-reports/compile-java.log` | **N** — Fabric CI artifact；不外推为本线的新源码验证。 |
| 5 | `docs/CHANGELOG_26_2_R2.md` | **D** — Fabric R2/R3 发行记录；本线 CHANGELOG 另行补充本次 port。 |
| 6 | `docs/MESH_LOADER.md` | **E** — mesh/PIP 语义已由本线 MESH_LOADER 与 mesh scope-clip record 覆盖。 |
| 7 | `docs/README.md` | **D** — Fabric 文档索引/版本口径；本线独立维护。 |
| 8 | `docs/ci/INSTALL_MATRIX_20260902.md` | **D** — Fabric 六线安装矩阵，非本线代码。 |
| 9 | `docs/ci/README.md` | **D** — Fabric CI 流程说明。 |
| 10 | `docs/ci/pending/README.md` | **D** — Fabric pending-workflow 说明。 |
| 11 | `docs/ci/pending/TaCZ_Renovated/1.21.11/build.yml` | **N** — 另一 NeoForge 分支的候选 workflow。 |
| 12 | `docs/ci/pending/TaCZ_Renovated/1.21.11/compile-check.yml` | **N** — 另一 NeoForge 分支的候选 workflow。 |
| 13 | `docs/ci/pending/TaCZ_Renovated/26.1.2/build.yml` | **N** — 另一 NeoForge 分支的候选 workflow。 |
| 14 | `docs/ci/pending/TaCZ_Renovated/26.1.2/compile-check.yml` | **N** — 另一 NeoForge 分支的候选 workflow。 |
| 15 | `docs/ci/pending/TaCZ_Renovated/26.2/build.yml` | **E** — 本仓 `.github/workflows/build.yml` 已逐字相同（SHA-256 在 §3）。 |
| 16 | `docs/ci/pending/TaCZ_Renovated/26.2/compile-check.yml` | **E** — 本仓 `.github/workflows/compile-check.yml` 已逐字相同（SHA-256 在 §3）。 |
| 17 | `docs/ci/pending/refab-1.21.11/build-yml-verify-steps.md` | **N** — Fabric 1.21.11 专用 workflow port 指引。 |
| 18 | `docs/ci/pending/refab-1.21.11/verify-mixin-targets-portable.patch` | **N** — Fabric 1.21.11 专用 patch。 |
| 19 | `docs/investigations/BUG_MESHGUNBODY_SCOPE_CLIP_RERENDER_2026_09_02.md` | **E** — 本线同一问题的独立记录：`records/BUG_MESHGUNBODY_SCOPE_CLIP_RERENDER_20260902.md`。 |
| 20 | `docs/investigations/PORT_26_3_FEASIBILITY_2026_09_02.md` | **N** — 26.3 调研，不改变 26.2 交付。 |
| 21 | `docs/investigations/SCOPE_PIP_HANDOFF_2026_08_21.md` | **D** — Fabric handoff 历史；本线 PIP records 是权威回执。 |
| 22 | `docs/lineage/HANDOFF_LEDGER.md` | **D** — Fabric 谱系账本；本仓以 `docs/records/` 管理。 |
| 23 | `docs/lineage/SYNC_GUIDE_PUTAWAY_KEEP_20260902.md` | **E** — 本线等价回执：`records/REFAB_SYNC_PUTAWAY_KEEP_R6_20260902.md`。 |
| 24 | `docs/lineage/SYNC_GUIDE_VISIBLE_BUGS_39JqB2p_20260908.md` | **D** — 可见问题/Iris 调查的 Fabric 原始叙事；关键最终语义和验证门写入本记录。 |
| 25 | `docs/mac-shader-transparency-test.md` | **D** — Mac/Fabric 测试文档；本记录提供不冒充 PASS 的 NeoForge 三档矩阵。 |
| 26 | `docs/patch/2026-09-02-putaway-keep-render-1.21.11.patch` | **N** — 另一分支的补丁载体。 |
| 27 | `docs/patch/2026-09-02-putaway-keep-render-26.1.2.patch` | **N** — 另一分支的补丁载体。 |
| 28 | `docs/patch/2026-09-08-visible-bugs-39JqB2p-refab-1.21.11.patch` | **N** — 另一 Fabric 分支的补丁载体。 |
| 29 | `docs/patch/2026-09-08-visible-bugs-39JqB2p-refab-26.1.2.patch` | **N** — 另一 Fabric 分支的补丁载体。 |
| 30 | `docs/patch/2026-09-08-visible-bugs-39JqB2p-renov-1.21.11.patch` | **N** — 另一 NeoForge 分支的补丁载体。 |
| 31 | `docs/patch/2026-09-08-visible-bugs-39JqB2p-renov-26.1.2.patch` | **N** — 另一 NeoForge 分支的补丁载体。 |
| 32 | `docs/patch/2026-09-08-visible-bugs-39JqB2p-renov-26.2.patch` | **E** — 内容已逐项在 §4 对照；不引入过期 `.patch` 作为本线源码。 |
| 33 | `docs/publish/CurseForge.md` | **N** — Fabric 发布渠道/版本文案。 |
| 34 | `docs/publish/MCMOD.md` | **N** — Fabric 发布渠道/版本文案。 |
| 35 | `docs/publish/Modrinth.md` | **N** — Fabric 发布渠道/版本文案。 |
| 36 | `docs/publish/README.md` | **N** — Fabric 发布目录索引。 |
| 37 | `fix-pip-full-mode-performance.zip` | **N** — Fabric 删除的上传 zip；本仓从未跟踪。 |
| 38 | `latest.log` | **N** — Fabric 删除的上传日志；本仓同名日志仍被当前 docs/源码明确引用，保留。 |
| 39 | `optimize-high-poly-vertex-transformation.zip` | **N** — Fabric 删除的上传 zip；本仓从未跟踪。 |
| 40 | `src/main/java/cn/sh1rocu/tacz/compat/meshloader/render/PolyMeshGpuRenderer.java` | **E** — mesh viewmodel clip 的两处 draw-time 判据已经落地，且本线后续增强仍保留。 |
| 41 | `src/main/java/com/tacz/guns/client/gameplay/LocalPlayerDraw.java` | **E** — 终态 `keep()` 唯一调用点 + initialized guard 已在役。 |
| 42 | `src/main/java/com/tacz/guns/client/model/functional/MuzzleFlashRender.java` | **E** — 已不做 obsolete common Iris pipeline assignment；保留当前本地 scope 行为。 |
| 43 | `src/main/java/com/tacz/guns/client/model/functional/ShellRender.java` | **E** — 已不做 obsolete common Iris pipeline assignment；保留当前本地 scope 行为。 |
| 44 | `src/main/java/com/tacz/guns/client/render/scope/ScopeBodyRenderTypes.java` | **E** — draw-time `clipForViewmodel` 等效机制已在役。 |
| 45 | `src/main/java/com/tacz/guns/client/render/scope/ScopeMaskRenderer.java` | **E** — 主手+带 scope 才告警的 guard、帧掩码快照均在役。 |
| 46 | `src/main/java/com/tacz/guns/client/renderer/item/AnimateGeoItemRenderer.java` | **E** — initialized-state 判定和唯一 keep 调用点注释已在役。 |
| 47 | `src/main/java/com/tacz/guns/client/renderer/item/GunItemRendererWrapper.java` | **E** — 非调用点维持注释/行为，避免重复 keep。 |
| 48 | `src/main/java/com/tacz/guns/compat/cloth/client/RenderClothConfig.java` | **P** — 新增 Iris 策略 enum selector。 |
| 49 | `src/main/java/com/tacz/guns/compat/iris/IrisCompat.java` | **E** — 当前无 Fabric 被删除的 `assignCommonEntityPipelinesToHandIfNeeded` 等全局路径；仅 scope/HAND 显式归类。 |
| 50 | `src/main/java/com/tacz/guns/compat/iris/IrisScopeMaskState.java` | **P** — 最终 per-program sampler safety、cache、debug 和 rebuild invalidation。 |
| 51 | `src/main/java/com/tacz/guns/config/client/RenderConfig.java` | **P** — NeoForge `ModConfigSpec.EnumValue` 的三态策略配置。 |
| 52 | `src/main/java/com/tacz/guns/crafting/GunSmithTableRecipe.java` | **E** — `isSpecial() == true` 已防止 NOT_PLACEABLE 误警告。 |
| 53 | `src/main/java/com/tacz/guns/mixin/client/ItemInHandRendererMixin.java` | **E** — latest-takeover keep guard 已在役。 |
| 54 | `src/main/java/com/tacz/guns/mixin/client/iris/IrisShaderCreatorMixin.java` | **P** — 以 final Fix-A 直拦截取代旧全程序 `@ModifyVariable`。 |
| 55 | `src/main/resources/assets/tacz/custom/tacz_default_gun/assets/tacz/animations/glock_17.animation.json` | **E** — 与 Fabric tip 无 diff，已无过渡 `sound_effects`。 |
| 56 | `src/main/resources/assets/tacz/lang/en_us.json` | **P** — IrisScopeMaskInjection 英文标签/说明。 |
| 57 | `src/main/resources/assets/tacz/lang/zh_cn.json` | **P** — IrisScopeMaskInjection 中文标签/说明。 |
| 58 | `src/main/resources/data/tacz/tags/entity_type/interact_key/whitelist.json` | **E** — 本线显式列出 26.2 全部 boat/raft 与 chest variants；等价于 Fabric tag+optional entries，且该固定版本所有 id 存在。 |

## 6. 57 笔 compare commit 逐笔台账

> merge commit 只表示 PR 合入外壳；其可观察终态仍由同表中对应子提交及 §5 的 tree path
> 逐项覆盖。CI-log 的唯一作用是说明 Fabric 当时的作业状态，不能替代本线编译。

| # | Fabric commit | 标题 | 处置 |
|---:|---|---|---|
| 1 | `a7915e3` | Delete latest.log | **N** — Fabric 根目录 `latest.log` 清理；本仓的同名日志是仍被当前 records/源码引用的不同证据，保留。 |
| 2 | `5bdb57e` | Delete optimize-high-poly-vertex-transformation.zip | **N** — Fabric 专用上传 zip；本仓无该文件，不制造/删除替代品。 |
| 3 | `15ec09e` | Delete fix-pip-full-mode-performance.zip | **N** — Fabric 专用上传 zip；本仓无该文件，不制造/删除替代品。 |
| 4 | `d830c1f` | ci-log: compile result (cancelled) for a7915e3d0da19a41ef5348be922dd94129e406d2 | **N** — Fabric CI 取消回执，不是代码或可移植验证。 |
| 5 | `c81dd50` | ci-log: compile result (success) for 15ec09e57050942707415fa5a72e338ec660a1e0 | **N** — Fabric CI 成功回执，不外推为 NeoForge 本次代码 PASS。 |
| 6 | `997ade1` | docs: 把 PIP/配置说明改回「游戏内界面优先」，补 R3 新内容与许可署名 | **D** — Fabric R3/PIP/许可首页文字；本仓维持自己的发布文档，相关功能状态由本记录和本线 records 承接。 |
| 7 | `a140d5e` | ci-log: compile result (success) for 997ade18459fa0080dcc6dafa642247660756491 | **N** — Fabric CI 回执。 |
| 8 | `ff70118` | docs(pip): 修掉 handoff §3 里两条被实机日志推翻的旧说法 | **D** — Fabric PIP handoff 历史修订；本线有独立 PIP/mesh records，不复制另一仓路线图。 |
| 9 | `eb56685` | ci-log: compile result (success) for ff70118447b4b5731197c701f21c82777edb589c | **N** — Fabric CI 回执。 |
| 10 | `7ca71be` | docs: 修掉我自己刚写错的配置界面层级（不存在「客户端」这一层） | **D** — Fabric 配置界面层级文案；本线配置文档按 NeoForge/Cloth UI 单独维护。 |
| 11 | `c6c6765` | ci-log: compile result (success) for 7ca71be6b7b62f9d641741164bf200f530de2eda | **N** — Fabric CI 回执。 |
| 12 | `169a525` | fix(mesh): 高模枪身镜内裁剪此前从未生效 —— 判据在绘制期恒 false（时序），改问帧快照 | **E** — mesh 枪身绘制期帧快照语义已在本线落地；见 `BUG_MESHGUNBODY_SCOPE_CLIP_RERENDER_20260902.md`。 |
| 13 | `cd94c7c` | ci-log: compile result (success) for 169a525ac867b3d0ded9f2f50908168f13fc0ad2 | **N** — Fabric CI 回执。 |
| 14 | `f2a4204` | Merge pull request #86 from q14433686-arch/arena/01a05e3e-tacz-refabricated-unofficial | **E** — PR #86 merge 外壳；其唯一功能件 `169a525` 已逐项对账。 |
| 15 | `ffe4548` | fix(animation): 收枪时补回 keep()，让旧视模在 put-away 窗口内仍可被提交 | **S** — 收枪 `keep()` 的中间提交；由下一笔终态 `32af402` 覆盖，本线已有终态。 |
| 16 | `fc5f05f` | ci-log: compile result (success) for ffe45485670e1505affcf7abb7e7ee2b1d5693c0 | **N** — Fabric CI 回执。 |
| 17 | `32af402` | fix(animation): keep() 守卫改「最新一次收枪接管」+ 调用点对齐上游 isInitialized 判定 | **E** — 收枪 latest-takeover + initialized guard 已落地；见 `REFAB_SYNC_PUTAWAY_KEEP_R6_20260902.md`。 |
| 18 | `aa0e2af` | ci-log: compile result (success) for 32af402546fd58181b074226c621172154759af1 | **N** — Fabric CI 回执。 |
| 19 | `bd234d0` | docs(lineage): 回填 putaway keep 轮的 CI 结果（compile+build 通过 32af402）与可实测构建链接 | **D** — Fabric 的 put-away CI/下载回填；本线不将其 CI 结果记为本线 PASS。 |
| 20 | `098d73a` | ci-log: compile result (success) for bd234d0b6925ee03757187f5e267af7e88ed7e7a | **N** — Fabric CI 回执。 |
| 21 | `fcd3b4a` | docs(ci): 六线 CI 上线总清单 + renov 三线代拟件 + 1.21.11 verify 脚本可移植化补丁 | **E** — 六线 CI 清单；本线对应的 26.2 `build.yml`/`compile-check.yml` 已存在且与 Fabric pending 提案逐字相同。 |
| 22 | `6c66b38` | ci-log: compile result (success) for fcd3b4a55810a2f8a500f1b517a905db7dfa640f | **N** — Fabric CI 回执。 |
| 23 | `1ff84c1` | docs: 26.3 移植可行性实测评估（现在开工 vs 等 stable）+ 账本 #16 | **D** — Fabric 26.3 可行性调查，不改变目标 26.2 的游戏语义。 |
| 24 | `16ae1f7` | ci-log: compile result (success) for 1ff84c1d7aedc94b3141a343c77c211675248b37 | **N** — Fabric CI 回执。 |
| 25 | `a408eb0` | Merge pull request #87 from q14433686-arch/arena/01a061a4-tacz-refabricated-unofficial | **E** — PR #87 merge 外壳；mesh/put-away 功能已由上述两份本线记录覆盖。 |
| 26 | `1aca7c7` | 26.2: fix visible issues from player log mclo.gs/39JqB2p | **E** — 可见问题集八项均已在本线等价存在；逐文件对照见本记录 §4。 |
| 27 | `391f376` | ci-log: compile result (success) for 1aca7c74f8fd14f64e6a348e235eb87dfdfa8534 | **N** — Fabric CI 回执。 |
| 28 | `bacb5fc` | docs: cross-branch patches + sync guide for the mclo.gs/39JqB2p visible-bug set | **D** — 跨分支 patch/sync guide；本记录给 NeoForge 留下可审计的本地回执，不复制 Fabric patch 文件。 |
| 29 | `4cbcb3b` | ci-log: compile result (success) for bacb5fc5b34703dbc1106b274f5d334ed8abc9e5 | **N** — Fabric CI 回执。 |
| 30 | `c81fab1` | Add files via upload | **N** — 上传的 Fabric 实机日志；仅为当时旁证，随后已删除。 |
| 31 | `2671e93` | ci-log: compile result (success) for c81fab1077ffad001d58fcaea7848745bb4ec32f | **N** — Fabric CI 回执。 |
| 32 | `8182e16` | chore: drop the uploaded real-machine latest.log from the repo root | **N** — 删除 Fabric 上传日志；本仓 `latest.log` 是独立、仍被引用的证据，不能机械删除。 |
| 33 | `bb36ee0` | ci-log: compile result (success) for 8182e16f3fed365c13860702fc5ff5c0f70c9799 | **N** — Fabric CI 回执。 |
| 34 | `457285c` | Merge pull request #94 from q14433686-arch/arena/01a07daa-tacz-refabricated-unofficial | **E** — PR #94 merge 外壳；其 `1aca7c7` 功能终态已对照。 |
| 35 | `ca8a1d9` | Iris scope-mask injection: HAND-only scope (+kill-switch, void-main matcher) | **S** — ThreadLocal/布尔开关的 Iris 中间桥已被 Fix-A `b7fce25` 证明 77/77 失效；不移植。 |
| 36 | `0f7a694` | ci-log: compile result (success) for ca8a1d9e8b32c571611aacd3b457de8c1d6c67c3 | **N** — Fabric CI 回执。 |
| 37 | `e7d5b82` | Align with sampler-conflict analysis: enum policy + per-program unit + diag | **P** — 最终 Iris 状态安全层、三态策略、Cloth/lang wiring 的组成部分，已按 NeoForge 类型适配移植。 |
| 38 | `8fe2afe` | ci-log: compile result (failure) for e7d5b82b9cdcec40f59a366d54c511ad1813dd1f | **D** — Fabric 中间版 compile failure；其 `int[]` 问题由最终 `IntBuffer` 源码处理，不能当 PASS。 |
| 39 | `6bd640a` | Guide 6.5: task-A closed (unit-0 binary-confirmed, relayed); B optional; D remains | **D** — Fabric guide 的机制/待测说明；关键约束与本线待测项已摘要入本记录。 |
| 40 | `11b0032` | Fix compile: glGetActiveUniform takes IntBuffer, not int[] (2 sites) | **P** — LWJGL `glGetActiveUniform` 的 `IntBuffer` 修正已作为最终状态的一部分移植。 |
| 41 | `41d5622` | ci-log: compile result (success) for 11b0032afe036901079f18a671c02372157eed9a | **N** — Fabric CI 回执。 |
| 42 | `8e4c75a` | Add Mac tester-facing protocol for shader transparency verification | **D** — Mac 测试者协议；本线改写为 loader-neutral 三档 Iris 验收，不挪用 Fabric PASS。 |
| 43 | `9ad5b58` | ci-log: compile result (success) for 8e4c75a4c615e85cdd2bd4b4cea40702593f29b5 | **N** — Fabric CI 回执。 |
| 44 | `cf2d5c7` | Test doc: add 2-minute minimum tier (Tier 0) before full protocol | **D** — Fabric Tier-0 文档；本线记录同样保留最低 2 分钟验证。 |
| 45 | `9c63802` | ci-log: compile result (success) for cf2d5c76d6b603f4971ef864119b6aaf1789eaf7 | **N** — Fabric CI 回执。 |
| 46 | `5e90c63` | Guide 6.6: fabric 3-version audit (only 26.2 affected); NeoForge pending | **D** — Fabric 三版本审计；本线只采其 26.2 source contract，且不把用户的 26.1.2/Fabric 观察泛化。 |
| 47 | `72fc6bd` | ci-log: compile result (success) for 5e90c63675ac47238fdbbf65c07f50417a364703 | **N** — Fabric CI 回执。 |
| 48 | `204b83a` | Add files via upload | **N** — 上传的 Fabric 实机日志；仅为当时旁证，随后已删除。 |
| 49 | `0d4ce8c` | ci-log: compile result (success) for 204b83affe986ecde4f35324d8f0bacfdee4b3e1 | **N** — Fabric CI 回执。 |
| 50 | `b7fce25` | Fix HAND filter: drop ThreadLocal bridge, patch at createShader (Fix A) | **P** — Fix-A：link 内 direct `@ModifyArgs`、`contains("hand")`、存活/计数诊断；已移植。 |
| 51 | `66b88d3` | Guide 6.7: A-card field verdict (mechanism wins, bridge fails); Fix A rationale | **D** — Fabric A-card 结论；本记录写明旧桥为何不能移植及本线独立验证门。 |
| 52 | `c4a53cd` | ci-log: compile result (success) for 66b88d39ae8863f0f57aae0d715df0e94648ce5d | **N** — Fabric CI 回执。 |
| 53 | `945090b` | Add files via upload | **N** — 上传的 Fabric 实机日志；仅为当时旁证，随后已删除。 |
| 54 | `bffc0c0` | ci-log: compile result (success) for 945090be0a5f6071638e03f03e12dc0b3f22d148 | **N** — Fabric CI 回执。 |
| 55 | `52715f6` | Release Mac testing: Fix A verified (9/68 split, terrain 6/6 OK); retire 11b0032 | **D** — Fabric Fix-A 的 Windows 验证及 Mac 送测放行/中间修订退休记录；是外部旁证，绝不标为 NeoForge PASS。 |
| 56 | `c29096c` | ci-log: compile result (success) for 52715f6ba9149ca5efafa7304421516f95bd812d | **N** — Fabric CI 回执。 |
| 57 | `1b4af9f` | Merge pull request #95 from q14433686-arch/arena/01a08307-tacz-refabricated-unofficial | **P** — PR #95 merge 外壳；以其中的最终状态（非中间桥）作为本次 Iris port 的落点。 |

## 7. 验证计划（尚未宣称 PASS）

### 7.1 静态检查已完成

- `git diff --check`：通过；无 conflict marker。
- 两份语言 JSON：解析通过，`iris_scope_mask_injection` 与 `.desc` 在中英文均存在。
- Iris target descriptor：按 §2 的官方 26.2 / 1.11.2 common 源码复核。
- 26.2 两份 pending CI workflow：按 §3 逐字 `cmp` 通过。
- `IrisScopeMaskState` 已检查包含 allocator、unit exhaustion fail-closed、cache reset、
  active-texture restore、`glBindSampler(unit, 0)` 与 debug validation 标记。

### 7.2 构建 / mixin gate

1. 在 JDK 25 环境运行 `./gradlew compileJava` 与 `./gradlew build`（或等待本分支 CI）。
2. 检查 optional Iris mixin 只在 Iris loading list 存在时装载；无 Iris 的客户端和专服不得
   解析 Iris target。`IrisCompatMixinPlugin` 的 NeoForge loader gate 不改。
3. 运行 `bash scripts/check_release_consistency.sh --strict`，并保留 CI run URL/日志作为本线
   证据。Fabric 的 success/failure log 不可替代这一步。

### 7.3 Iris 运行时三档矩阵（客户端，单人即可；不涉及“专服专有”归因）

固定 MC 26.2 / NeoForge / Iris 1.11.2 / Sodium / 一个能复现或常用 shader pack；每次改
`IrisScopeMaskInjection` 后重载 shader pack（或退回标题再进），记录截图和完整
`latest.log`。不要把 NeoForge 26.1.2 正常或 Fabric 各线正常的用户观察外推为本线结果。

| 档位 | 预期地形/世界 | 预期 scope | 关键日志判读 |
|---|---|---|---|
| `HAND_ONLY`（默认） | 正常；world program 不带 TACZ sampler branch | 带 scope 枪 ADS 时 body/reticle/text 正常受 mask 约束 | 汇总应有 HAND > 0 和 world > 0；不得有“0 HAND programs” WARN。debug sampler 表中 world 无 `tacz_ScopeMaskSampler`。 |
| `ALL` | 也应正常；若透明则说明 per-program allocator/driver 合法性仍有缺口 | 应仍正常裁剪 | 允许 world 有 TACZ sampler，但应在空闲 unit；`glValidateProgram` 不应报不同 sampler type 共用 unit。 |
| `OFF` | 正常 | shader-pack 下不发生 TACZ GLSL mask clipping（作为因果对照） | config-skipped 增加；无 injected program。 |

额外覆盖：HAND solid/translucent、shadow、水/雾/粒子/云、反复 ADS/松开后的 mode reset、
shader reload、切换 shader pack、`ScopeMaskDebug=true`。保存驱动/GL validation failure、
`no free texture unit` WARN、0-HAND warning 或 crash report；它们是诊断结果，不要静默忽略。

Fabric 的 Fix-A 记录曾在其自身 Windows 环境看到 9 HAND / 68 world / 77 fragment 与地形
validation 正常，另有 Mac 送测记录。这些数字只用来说明本线应收集何种计数闭环；不同
shader pack 绝不能要求 NeoForge 也恰为 9/68/77，更不能将其写成 NeoForge 实机通过。

### 7.4 recipe-viewer 非回退矩阵（原请求必须保持）

本次没有触碰 recipe viewer、枪包同步 payload 或 server lifecycle；但 Iris/config 改动合入
后仍须按 `RECIPE_VIEWER_SYNC_262_20260908.md` 重跑以下最低集，不能用单机成功代替远程：

1. 默认包 24 条 `data/tacz/recipe/ammo/*.json`：工作台、JEI、REI 和 **TaCZ Ammo Query**
   都可见、可打开、无 null/NPE。
2. JEI-only、REI-only、JEI+REI 三种客户端组合；第三方枪包和枪包 reload 后再次检查。
3. **单人**和**远程真实专服**各跑一次；专服不安装 viewer 也必须让客户端 viewer 通过
   native recipe content/lifecycle 刷新，不得把故障误标成专服专有。
4. 保存 client/server log，检查 recipe sync 后没有 `Components not bound yet`、REI
   `existing reload task` 或 display registry 中断；验收结果追加到本线记录，不挪用 Fabric。

## 8. 不适用项与边界再次确认

- 不复制 Fabric `@Environment`、Fabric networking/lifecycle、Loom、access widener、其
  pending patch 或发布物；NeoForge 已有等价 API/配置/optional mixin loading 路线。
- 不删除本仓根 `latest.log`：它不是 Fabric 已删上传物的同一证据，当前本线文档和源码仍
  有明确引用。若将来要清理，必须先归档/改写所有本线引用，作为独立变更。
- 不把“某 loader/某版本正常”或“另一个 loader 分支正常”写成跨平台根因判断。此 port
  只消除本线旧 Iris injection 的已审计风险并提供可诊断的三档对照。
- 本记录是本线 `docs/records/` 的本地回执，替代 Fabric `docs/lineage/` / `docs/patch/` 的
  交接载体；这保证以后可追溯，又不污染本仓的历史叙事。
