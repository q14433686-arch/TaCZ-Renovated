# 高模枪检视反射异常：Iris setup 的 RenderPass 生命周期（26.1.2 线，2026-09-08）

> 性质：**同步姊妹项目 refab 26.1.2 PR #92 的独立提交 `9412e08`（"fix(mesh): refresh Iris normal
> and material state for each bone pass"），静态修复、待实测**。本线 `PolyMeshGpuRenderer#drawList`
> 与 refab 26.1.2 同构（一个自建 pass 包住全部纹理组 / 全部骨骼 + per-draw MV push/pop），缺口相同。
> 维护者反馈的症状（26.1.2 / 1.21.11 高模枪开光影检视时多数角度偏黑、反射异常；26.2 无）早于
> 日志五件套修复，**不归因于删除 `assignCommonEntityPipelinesToHandIfNeeded`**，也不解释世界全透明。
> 编译门与回归测试走 CI（本地沙箱无 JDK），**运行期未实机验证**。

## 1. 源码确认的缺口（纠正 2026-09-01「仅压栈即等价 26.2」的结论）

本线 2026-09-01 同步 26.2 `83daf16` 时（见 `docs/SYNC_1211_RENDER_20260901.md` 表中 `93178de` 行），
认定「每根骨骼 draw 前压入 MV、画完弹出」与 26.2 等价，漏查了 **Iris setup 的一次性守卫及其清除边界**。
压栈仍然必要，但多骨骼共用 pass 时并不充分。

固定版本源码审计（由 refab 侧完成，本线逐条复核链接可达、行号一致）：

- Iris **26.1** `f4c06978f3a1c64869e40cd5cc7c8ed383085cc0`：
  [`MixinGlCommandEncoder.java` L162–178](https://github.com/IrisShaders/Iris/blob/f4c06978f3a1c64869e40cd5cc7c8ed383085cc0/common/src/main/java/net/irisshaders/iris/mixin/MixinGlCommandEncoder.java#L162-L178)
  在 `trySetup` RETURN 仅当 `program instanceof IrisProgram && !iris$isSetUp()` 时调用
  `onSetAlbedoTex` 与 `iris$setupState`，并加入 `programsToClear`；
  **到 `finishRenderPass` 才 `iris$clearState()` 并清空列表**。
- 同版 [`ExtendedShader.java` L161–190](https://github.com/IrisShaders/Iris/blob/f4c06978f3a1c64869e40cd5cc7c8ed383085cc0/common/src/main/java/net/irisshaders/iris/pipeline/programs/ExtendedShader.java#L161-L190)：
  `clearState` 置 `isSetup=false`，`setupState` 置 `isSetup=true`；
  `iris_ModelViewMatInverse` / `iris_NormalMat` 在 setup 时由 `RenderSystem.getModelViewMatrix()`
  求逆 / 逆转置上传。**26.1 的方法名是 `getModelViewMatrix()`，不是 26.2 的 `getModelViewMatrixCopy()`**
  （与本线 `docs/SCOPE_FINAL_OVERLAY_BACKPORT_26_1_2_2026_08_30.md` 第 4 行核对结论一致；
  `PolyMeshGpuRenderer` 旧注释照搬 26.2 方法名，本次一并更正）。
- 同版 [`IrisRenderingPipeline.java` L849–869](https://github.com/IrisShaders/Iris/blob/f4c06978f3a1c64869e40cd5cc7c8ed383085cc0/common/src/main/java/net/irisshaders/iris/pipeline/IrisRenderingPipeline.java#L849-L869)：
  `onSetAlbedoTex` 在适用条件下更新对应 albedo 的 normal/specular PBR 贴图。

本线原实现：一个 RenderPass 包住全部纹理组 / 全部骨骼，逐骨骼只更新 `DynamicTransforms` 和 MV 栈。
因此第一根骨骼完成 setup 后：

1. 后续骨骼的位置使用自己的 transform 切片（正确）；
2. 法线 / 逆 MV uniform 却仍是第一次 setup 的值，骨骼旋转不同时两者失配；
3. 后续纹理组仅 `bindTexture("Sampler0", …)`，不会重新经过 albedo/PBR 通知。

这能解释为什么检视等骨骼相对旋转时明暗 / 高光更容易异常，也可能影响多材质枪。
**源码证明的是上述状态错用，尚未用维护者的枪包 / 光影包复现并确认全部外观症状。**
如果玩家实际走的是 collector 而非 GPU 路径，这个缺口不能直接解释该次复现。

## 2. 本线改动与边界

| 文件 | 改动 |
|---|---|
| `compat/meshloader/render/MeshRenderPassBatches.java`（新增） | 无 Minecraft / GL 依赖的分批策略：**Iris 每根骨骼一个 pass；无光影仍为一个批次** |
| `compat/meshloader/render/PolyMeshGpuRenderer.java` | `drawList` 改为 `for (batch : partition(orderedDraws, irisFlush))` 外层循环，每个 pass 重绑 pipeline / 默认 UBO / lightmap / scissor / 对应 albedo；保留骨骼 MV 的 push/try/finally-pop；首帧日志移到全部 pass 之后 |
| `build.gradle` | 新增 `compileMeshRenderPassTest` / `meshRenderPassTest`（JavaExec，Java 25 toolchain），挂入 `check`（CI `./gradlew build` 会跑） |
| `tests/mesh-render-pass/MeshRenderPassBatchesTest.java`（新增） | 与 refab 同源，仅改包名 `com.tacz.guns.compat.meshloader.render` |

边界：

- 保留纹理分组顺序；无光影时相邻同纹理不重复 bind。VBO 烘焙、缓存与顶点格式不变。
- 所有 `writeTransform`、索引缓冲预热、纹理懒加载仍在所有 pass **之前**完成，不引入 open-pass 内
  map/upload，不嵌套 pass，不清空颜色 / 深度（每个 pass 仍 `OptionalInt.empty()` / `OptionalDouble.empty()`）。
- 每个 pass 保留 scope mask `beginExternalMaskOutsideDraw` / `end()` 配对与深度纹理绑定；需回归高倍镜 / PIP。
- 手部 / 世界 GPU 路径共用 `drawList`；不启用原本关闭的世界 GPU 开关，不影响 collector。
- 不新增 Iris 内部 mixin / 反射，不手改 GL normal uniform，不改光影包，不翻转法线，
  不改版本、依赖版本或配置默认值。
- 性能代价：光影下 pass / setup 次数增加到骨骼数，draw 数及 VBO 数不增加。**性能未测**；
  不能把多个同纹理、不同骨骼矩阵的 draw 重新合并而不处理 Iris setup。

与 refab 侧的差异仅为包名（`cn.sh1rocu.tacz` → `com.tacz.guns`）、lightmap 采样器变量名
（本线已有 `nearestSampler` 局部变量）与 `build.gradle` 的 toolchain 写法（本线直接 `JavaLanguageVersion.of(25)`）。

## 3. 验证

| 项 | 状态 |
|---|---|
| 与 refab `9412e08` diff 逐块对照（pass 体、mask 配对、MV push/pop、日志时序） | ✅ |
| 本地 `check_release_consistency.sh --strict` / mixin 注册检查 | ✅ |
| CI compile-check（推 `arena/**` 触发） | 见 `build-reports/compile-java.log` 回推结果 |
| CI 全量 build（`check` → `meshRenderPassTest`：旧共享 pass 重现 2 处法线错用 + 1 处材质错用；仅按纹理分 pass 仍失败；修复后 24 组检视旋转 / 同纹理不同骨骼 / 多材质 / 空表 / 单骨骼 / vanilla 单批次通过） | 见 Actions `build` 工作流 |
| 实机（§4） | ❌ **未实测** |

回归测试是**生命周期模型回归**（用小型状态机模拟上面审计的 Iris 一次 setup / pass-close 清除协议），
不是真实 Iris / OpenGL 集成测试。

## 4. 实机待测 / 请维护者提供

请提供枪包名、枪械名、光影包名和版本，确认同一枪包 / 光影配置在 26.2 正常；最好附检视短视频和
日志中的 `[TacZMeshLoader] GPU mesh pass drew … in Iris hand flush`（确认实际命中 GPU 路径）。

同一存档 / 光源 / 光影配置下：

1. 第一人称腰射与完整检视：枪体、弹匣等旋转不同的部件，明暗、高光与反射连续正常。
2. 多材质枪的 PBR normal/specular 贴图正确，切枪 / 换包 / F3+T 无错贴或新异常。
3. 同一把枪把 `MeshGpuUnderShaders=false` 作为 GPU / collector **诊断对照**，不是永久修复。
4. 高倍镜 / PIP 下枪身裁剪仍正确；无光影、单骨骼及普通非高模枪无回归。
5. 若开启世界 GPU，回归第三人称、掉落物、展示框；记录帧时间，评估额外 setup 开销。

所有实机项仍待测。本次不声称已实测解决维护者的反射症状。

## 5. 同源

- refab 26.1.2 PR [#92](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial/pull/92)，
  代码提交 `9412e08`，记录 `docs/MESH_GPU_IRIS_PASS_LIFETIME_2612_20260908.md`；
  该提交 CI compile-check / 全量 build（含回归）均 success。
- 1.21.11 线（renov / refab）同形缺口已由 refab 侧核对，**本会话未修改该线**。
