# 高模枪光影检视反射异常：Iris setup 的 RenderPass 生命周期（1.21.11 线，2026-09-08）

> **状态：静态修复、待实测。** 本件为 refab 26.1.2 线
> [`MESH_GPU_IRIS_PASS_LIFETIME_2612_20260908.md`](https://github.com/q14433686-arch/TaCZ_Refabricated_Unofficial/blob/9412e08/docs/MESH_GPU_IRIS_PASS_LIFETIME_2612_20260908.md)
> （commit `9412e08`，PR #92）的同形移植；症状与维护者反馈见该记录
> （26.1.2 / 1.21.11 高模枪开光影检视时多数角度枪体偏黑、反射异常，仅少数
> 角度正常；26.2 无此症状；早于 39JqB2p 日志修复轮，独立于 A–D）。

## 1. 根因（本线 Iris 源码直接核验，2026-09-08）

`PolyMeshGpuRenderer#drawList` 原本把全部纹理组/全部骨骼放进**同一个**自建
`RenderPass`，逐骨骼只更新 DynamicTransforms 切片与 MV 栈。Iris 的 setup
是一次性的：

- Iris **1.21.11 分支** `11f566b7fbc8da1f62437eda86ee68fda9cf2ee0`
  （本线 MC 版本对应的 Iris 代码基线；本线 NeoForge Iris 1.10.x 即出自
  该 1.21.11 世代）：
  [`MixinGlCommandEncoder#iris$setupState`](https://github.com/IrisShaders/Iris/blob/11f566b7fbc8da1f62437eda86ee68fda9cf2ee0/common/src/main/java/net/irisshaders/iris/mixin/MixinGlCommandEncoder.java)
  注入 `trySetup` RETURN，**仅当** `program instanceof IrisProgram &&
  !is.iris$isSetUp()` 时执行 `onSetAlbedoTex`（albedo/PBR 贴图通知）+
  `iris$setupState`，并加入 `programsToClear`；`iris$clearState` 注入
  `finishRenderPass` HEAD 才清标志、清空列表。
- 同版 [`ExtendedShader`](https://github.com/IrisShaders/Iris/blob/11f566b7fbc8da1f62437eda86ee68fda9cf2ee0/common/src/main/java/net/irisshaders/iris/pipeline/programs/ExtendedShader.java)：
  `iris$clearState()` 置 `isSetup=false`；`iris$setupState(albedoTex)` 置
  `isSetup=true` 并从 `RenderSystem.getModelViewMatrix()`（**活 MV 栈顶**，
  1.21.11 的 getter 没有 26.2 的 `Copy` 变体）求逆 / 逆转置上传
  `iris_ModelViewMatInverse` / `iris_NormalMat`。
- 每次 draw 都会到 `trySetup`，**但守卫在则 setup 体不执行**——
  「每次绘制都过一遍 trySetup」≠「每次绘制都上传法线矩阵」。

因此共用 pass 时：第一根骨骼完成 setup 后，后续骨骼的位置走自己的
DynamicTransforms 切片（正确），但 `iris_NormalMat` / 逆 MV 停留在第一根
的矩阵上（骨骼旋转不同时失配 ⇒ 平行光/反射按错法线算，检视时明暗/高光
错乱）；后续纹理组换 `Sampler0` 也不会再触发 `onSetAlbedoTex` 的
PBR normal/specular 通知（多材质枪错贴）。26.2 线无此症状，因其光影
路径每根骨骼独立 `RenderType#prepare` + `drawFromBuffer`。

## 2. 本线改动

- 新增 `MeshRenderPassBatches.partition`（纯 Java、无 Minecraft 依赖的
  pass 边界策略，与 refab 同名同形）：**Iris 下每根骨骼一个 pass；无光影
  保持单批次**。
- `drawList` 改为按 partition 逐批开 pass：每批重绑 pipeline / 默认
  UBO / lightmap / scissor / 对应 albedo（`boundTextureView` 去重），
  保留骨骼 MV 的 push/try/finally-pop 与 per-draw DynamicTransforms
  切片；纹理分组顺序、VBO 烘焙与缓存、顶点格式不变。
- 所有 pass 外不变量保持：`writeTransform`、索引缓冲预热、纹理懒加载
  仍在**所有** pass 之前完成（1.21.11 open pass 期间禁止 map 命令的
  同一条规则）；不嵌套 pass、不清屏、不新增 Iris mixin/反射、不手改 GL
  normal uniform、不翻转法线、不改版本/依赖/配置默认值。
- 每批保留 scope mask begin/end 配对与深度纹理绑定（高倍镜/PIP 需回归）。
- 手部/世界 GPU 路径共用 `drawList`；世界 GPU 开关维持原状。

## 3. 回归测试

`tests/mesh-render-pass/MeshRenderPassBatchesTest.java`（无第三方依赖，
独立编译运行，挂入 `check`/`build`，经 `./gradlew meshRenderPassTest`
可单跑）：用状态机模拟上述已审计的 Iris「一次 setup / pass-close 清除」
协议，覆盖旧共享 pass 复现法线/材质错用、仅按纹理分 pass 仍失败、修复后
24 组检视旋转、同纹理不同骨骼、多纹理、空表/单骨骼与 vanilla 单批次。
**这是生命周期模型回归，不是真实 Iris/OpenGL 集成测试。**

## 4. 验证

- [x] 本线 Iris 1.21.11 分支源码两处直接核验（§1 链接，2026-09-08 拉取）。
- [x] 代码与 refab `9412e08` 同形逐段比对（draw 循环、去重绑定、
  pass 外不变量、mask 配对）；本线差异仅注释措辞与既有变量名
  （`mvStack`、预取 `nearestSampler`）。
- [x] `bash scripts/check_release_consistency.sh --strict`。
- [ ] CI `compile-check`（本沙箱无 JDK/外网，推送后由 `compile-check.yml`
  出结论）。
- [ ] CI 全量 `build`（含 `meshRenderPassTest`；`build` 依赖 `check`）。

## 5. 实机待测（未执行）

同一存档/光源/光影配置下（请维护者提供枪包名、枪械名、光影包名与版本，
确认同配置在 26.2 正常，最好附检视短视频与
`[TacZMeshLoader] GPU mesh pass drew ... in Iris hand flush` 日志）：

1. 第一人称腰射与完整检视：枪体、弹匣等旋转不同的部件，明暗、高光与
   反射连续正常（本件主症状）。
2. 多材质枪的 PBR normal/specular 贴图正确；切枪/换包/F3+T 无错贴或
   新异常。
3. `MeshGpuUnderShaders=false` 作 GPU/collector **诊断对照**（非永久修复）。
4. 高倍镜/PIP 下枪身裁剪仍正确；无光影、单骨骼及普通非高模枪无回归。
5. 若开启世界 GPU：回归第三人称、掉落物、展示框；记录帧时间，评估
   每骨骼 setup 的额外开销（**性能未测**）。

所有实机项待测；本记录不宣称已实测解决维护者的反射症状。
