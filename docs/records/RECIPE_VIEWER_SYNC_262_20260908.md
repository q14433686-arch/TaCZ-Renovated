# 记录：JEI / REI 枪匠台弹药配方与 Ammo Query 同步修复（26.2，2026-09-08）

- **分支**：`arena/01a07f93-tacz-renovated`（基线 `de0928f0afb770a33dc6a0c8f1a36042d92fb229`）。
- **范围**：默认枪包的 24 条 `data/tacz/recipe/ammo/*.json` 弹药枪匠台配方；JEI / REI 的
  工作台查询以及内置 **TaCZ Ammo Query**。该问题同时影响单人与远程专服客户端，单机成功
  不能替代专服验收。
- **证据级别**：NeoForge 26.1.2/26.2 stable 官方源码/patch、JEI 29.29/30.24、REI
  26.1.819/26.2.820、Fabric 26.2 对照源码及 Architectury 21.0.2 已作静态闭环；Java 25 CI
  的 `compileJava` 和完整 build 已通过，但尚未执行游戏内验收，**不宣称运行期 PASS**。

## 1. 复现与根因

默认包中该目录共 24 个 JSON；每个都声明
`"type": "tacz:gun_smith_table_crafting"`，`result.type` 为 `ammo`。这些不是原版工作台
配方，必须由 TaCZ 的 JEI / REI 插件登记。

已检查的用户 `latest.log` 给出两条独立、会相互叠加的故障链：

1. 枪包同步后已记录 `guns=458 ammo=71 attachments=233 blocks=12 recipes=758`，但 REI
   在 `GunSmithTableDisplay.<init>` 第 22 行失败。`GunSmithTableIngredient#getIngredient()`
   对尚未按 level `RegistryAccess` 解析的 raw tag 材料允许返回 `null`；旧构造器把这个
   `null` 直接交给 `EntryIngredients.ofIngredients(...)`。一次异常中断
   `REIClientPlugin#registerDisplays`，后面的 attachment 与 Ammo Query display 均未登记。
2. TaCZ 自定义 `ServerMessageSyncGunPack` 会安装 common cache / client indexes，但它本身
   不会重建 JEI 的插件。JEI 30.24 的 NeoForge `StartEventObserver` 用
   `RecipesReceivedEvent` 作为启动屏障，且在已启动且有同步配方时用同一事件 restart。
   因而不能把自定义 cache payload 的到达当作 JEI 已刷新。

此前 bridge 通过反射调用 REI 内部的
`RoughlyEnoughItemsCoreClient#reloadPlugins(MutableLong, ReloadStage)`；日志证明该调用会在
REI 自己由 recipe update 启动的异步重载尚未结束时嵌套，出现 “found 1 existing reload task”。
反射调用返回只表示请求已发出，不表示 REI 重建完成，不能作为完成判据。

### 1.1 反证对照：26.1.2 与 Fabric 不是同一条故障路径（2026-09-09 补记）

用户确认 NeoForge 26.1.2 和 Fabric 各线均未复现。源码对照支持这个观察：这不是“NeoForge
天生不能显示 TaCZ 配方”，也不能把专服当根因。

1. **NeoForge 26.1.2 的同名 viewer 插件和 REI bridge 与 26.2 base 的功能代码几乎相同**；
   两个 NeoForge stable 的 `OnDatapackSyncEvent`、`PlayerList` 发送顺序和
   `RecipeContentPayload` API 也都已存在。因此不存在“26.2 才有该 NeoForge API”的解释。
2. 真正的 26.2 port 差异在 `CommonAssetsManager#onTagsUpdated`：26.1.2 遍历 native
   `GunSmithTableRecipe` 并调用 `recipe.init()`；26.2 的用户日志证明同一调用点已经早到
   item Holder components 绑定之前（`Components not bound yet`）。而
   `GunSmithTableResult#init()` 在 `finally` 中置 `initialized=true`，故第一次失败会把该
   recipe 永久固定为 EMPTY。26.2 base 必须删掉这段过早初始化，不能为“追平 26.1.2”而恢复它。
3. Fabric 26.2 在 `CommonLifecycleEvents.TAGS_LOADED` 回调中以其 `RegistryAccess` 调
   `CommonAssetsManager#onReload(..., false)`，在那里初始化 native recipes；其
   `ServerMessageSyncGunPack#doSync` 还在 cache/index 安装后显式触发 **JEI Fabric** 的
   `JeiLifecycleEvents.AFTER_RECIPES_UPDATED` 和 REI refresh。这个时序与 NeoForge 26.2 的
   `TagsUpdatedEvent.ServerDataLoad` / 原生 REI recipe-update 不同，不能机械搬运反射 bridge。
4. 此次 NeoForge 日志同时真实记录了 REI 的 `existing reload task` 和随后
   `GunSmithTableDisplay` null NPE；后者会中断同一 plugin 的余下 display 注册，故足以让默认
   ammo 和 Ammo Query 一并消失，即使默认 24 条 JSON 本身有效。修复保留 cache 为权威数据，
   仅在安全网络边界补 native content 和正式 viewer lifecycle，而非假定 loader 有缺陷。

**待用真实客户端做的最小 A/B**：同一 mods/枪包配置分别运行 26.2 base（仅含“移除过早
`init()`”）和本修复；若 base 已恢复全部查询，则把 viewer/lifecycle 的额外防护标为回归保险，
不得声称它是唯一根因；若 base 仍失败，则保存两端日志，按第 5 节 JEI-only / REI-only / 双装
矩阵定位剩余链路。

## 2. 26.2 API / 时序证据

| 组件 | 已核类与签名 | 结论 |
|---|---|---|
| NeoForge server | [`OnDatapackSyncEvent#sendRecipes(RecipeType<?>...)`](https://github.com/neoforged/NeoForge/blob/c13ea5b8000ee5333107f2be6416cc860c3f6d39/src/main/java/net/neoforged/neoforge/event/OnDatapackSyncEvent.java) | 公开 API；请求指定 recipe type 的完整内容发送。 |
| NeoForge send order | [`PlayerList.java.patch`](https://github.com/neoforged/NeoForge/blob/c13ea5b8000ee5333107f2be6416cc860c3f6d39/patches/net/minecraft/server/players/PlayerList.java.patch) | `OnDatapackSyncEvent` 在 `ClientboundUpdateRecipesPacket` 与 `CommonHooks.sendRecipes(...)` 之前 post；本模组在 event 内先发送 cache，因此后续原生 recipe 数据包在该 cache 后发出。 |
| NeoForge client | [`ClientPayloadHandler#handle(RecipeContentPayload, IPayloadContext)`](https://github.com/neoforged/NeoForge/blob/c13ea5b8000ee5333107f2be6416cc860c3f6d39/src/client/java/net/neoforged/neoforge/client/network/ClientPayloadHandler.java) | 收到 `RecipeContentPayload` 后 post `new RecipesReceivedEvent(payload.recipeTypes(), recipeMap)`。 |
| Payload main-thread order | [`PayloadRegistrar#register`](https://github.com/neoforged/NeoForge/blob/c13ea5b8000ee5333107f2be6416cc860c3f6d39/src/main/java/net/neoforged/neoforge/network/registration/PayloadRegistrar.java) + [`MainThreadPayloadHandler#handle`](https://github.com/neoforged/NeoForge/blob/c13ea5b8000ee5333107f2be6416cc860c3f6d39/src/main/java/net/neoforged/neoforge/network/handling/MainThreadPayloadHandler.java) | 默认 `HandlerThread.MAIN`；TaCZ 的 play S2C handler 因此在随后原生 recipe 内容前于客户端主线程执行 cache/index 安装。 |
| JEI 30.24 | [`JustEnoughItemsClient#onRecipesReceivedEvent`](https://github.com/mezz/JustEnoughItems/blob/886b3644c62f4c18ffa22a23a0de0e1130e2f507/NeoForge/src/main/java/mezz/jei/neoforge/JustEnoughItemsClient.java) + [`StartEventObserver#register / #onRecipesReceivedEvent`](https://github.com/mezz/JustEnoughItems/blob/886b3644c62f4c18ffa22a23a0de0e1130e2f507/NeoForge/src/main/java/mezz/jei/neoforge/startup/StartEventObserver.java) | 前者仅在 `recipeMap.values()` 非空时写入 `Internal.setClientSyncedRecipes(recipeMap)`；后者 LOWEST priority 监听 event，首次满足 login + recipe sync 时 start，已启动且该 state 已设置时 restart。 |
| REI 26.2.820 | [`RoughlyEnoughItemsCoreClient#registerEvents`](https://github.com/shedaniel/RoughlyEnoughItems/blob/2be20928abd9f1164fd9fd251268041c036b580f/runtime/src/main/java/me/shedaniel/rei/RoughlyEnoughItemsCoreClient.java) | `PRE_UPDATE_RECIPES` 请求 START，`ClientRecipeUpdateEvent.EVENT` 请求 END。 |
| Architectury 21.0.2 | [`MixinClientPacketListener#handleUpdateRecipes`](https://github.com/architectury/architectury-api/blob/22091fe52191fa21eca897ef6f4ae4b3af5171e0/neoforge/src/main/java/dev/architectury/mixin/neoforge/client/MixinClientPacketListener.java) | `ClientboundUpdateRecipesPacket` RETURN 调 `ClientRecipeUpdateEvent.EVENT#update(RecipeAccess)`；该原生包位于 cache payload 之后。 |
| REI entry API | [`EntryIngredients#ofIngredient(Ingredient)`](https://github.com/shedaniel/RoughlyEnoughItems/blob/2be20928abd9f1164fd9fd251268041c036b580f/api/src/main/java/me/shedaniel/rei/api/common/util/EntryIngredients.java) / [`EntryIngredient#empty()`](https://github.com/shedaniel/RoughlyEnoughItems/blob/2be20928abd9f1164fd9fd251268041c036b580f/api/src/main/java/me/shedaniel/rei/api/common/entry/EntryIngredient.java) | REI 转换器要求非 null `Ingredient`；空材料格应建模成空 `EntryIngredient`，而非传 null。 |

`RecipeContentPayload#create(Collection<RecipeType<?>>, RecipeMap)`（同 NeoForge commit 的
[`RecipeContentPayload`](https://github.com/neoforged/NeoForge/blob/c13ea5b8000ee5333107f2be6416cc860c3f6d39/src/main/java/net/neoforged/neoforge/network/payload/RecipeContentPayload.java)）按 type
从 server `RecipeMap` 选取 `RecipeHolder`。因此同步本模组自己的
`ModRecipe.GUN_SMITH_TABLE_CRAFTING` 是语义正确的请求，而不是伪造或 post 一个内部 client
事件。

## 3. 落地修复

1. `CommonAssetsManager#onDatapackSync` 仍在 event 内把 server-authoritative common cache
   发给相关客户端，并调用
   `event.sendRecipes(ModRecipe.GUN_SMITH_TABLE_CRAFTING.get())`。默认包的 24 条有效 native
   recipe 令该 content packet 非空；JEI 的 `JustEnoughItemsClient#onRecipesReceivedEvent` 因而
   写入 client-synced recipe state，随后 observer 可执行正式 startup/restart barrier。JEI
   只装在客户端的场景也不再依赖服务端安装 JEI。
2. `GunSmithTableSerializer#STREAM_CODEC.encode` 在该**已完成资源重载的网络边界**调用
   `recipe.init()`，避免 lazy gun/ammo/attachment result 被编码成 `ItemStack.EMPTY`。
3. JEI 和 REI 的插件都在 `Minecraft.level` 可用后，用
   `recipe.resolveIngredients(level.registryAccess())` 准备每条 recipe 的 raw materials，和
   `GunSmithTableScreen` / `GunSmithTableMenu` 一致。单个损坏 recipe 记录错误并跳过，不能
   连坐整个 viewer registry。
4. `GunSmithTableDisplay` 逐项构造 `EntryIngredient`。任何仍未解析的材料保留为一个空 slot
   (`EntryIngredient.empty()`)，故 REI 不会收到 null，且输入 slot 数不变。
5. REI 的 `displays` 映射在每次 `registerCategories` 前清空，避免服务器 reload 后已移除
   workbench 的旧 id 残留；每个 `registry.add(...)` 独立守卫，确保 Ammo Query 总会继续登记。
6. 删除 `RecipeViewerReloadBridge` 及其 tick/packet/logout 调用。它依赖 REI 内部异步 API，
   会同 REI 本身的 native START/END reload 竞争；现在 JEI / REI 都由各自已核的原生网络
   生命周期触发，无反射完成假设或资源 reload fallback。

## 4. 本次可执行的静态检查

已运行：

```text
python resource inventory: 24 default ammo gun-smith recipes
all 24: type=tacz:gun_smith_table_crafting, result.type=ammo, materials non-empty
git diff --check: clean
git grep RecipeViewerReloadBridge: no remaining reference
```

本地 sandbox 没有 `java`（`JAVA_HOME` 未设置且 PATH 内无 Java），故本地
`./gradlew compileJava` 在 Gradle 启动前即失败；这只是本地环境限制，并非源码编译结果。

**CI 补充验证（2026-09-08）**：源码 commit
[`29e15656b08df6a15f7ae4c18e97665cf691b4cd`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/29e15656b08df6a15f7ae4c18e97665cf691b4cd)
已在 Java 25 GitHub Actions 完成 [`compileJava`](https://github.com/q14433686-arch/TaCZ_Renovated/actions/runs/34193430115)
和完整 [`build`（含 jar artifact）](https://github.com/q14433686-arch/TaCZ_Renovated/actions/runs/34193429970)，均为 success；
版本一致性和文档链接检查也在
[`consistency`](https://github.com/q14433686-arch/TaCZ_Renovated/actions/runs/34193429989) 中通过。
这不替代真实游戏运行期验收。

## 5. 待执行的运行期验收

以下须在 Java 25 / NeoForge 26.2.0.64 环境完成，并记录实际 commit、JEI/REI 版本与完整日志：

1. 确认默认 24 条 ammo JSON 在 server datapack reload 后仍无 stream-codec/payload 编码异常。
2. **JEI only，单人**：以默认 ammo（含 `tacz:9mm`）按配方查询；24 条默认 ammunition
   workbench recipes 可见，材料 tag 有内容；打开 TaCZ Ammo Query，显示非空且相容枪械与
   gun index 一致。
3. **REI only，单人**：同上；日志不得出现
   `GunSmithTableDisplay` / `EntryIngredients` null stack 或 nested reload-task warning。
4. **JEI only，真实专服客户端**：服务端不安装 JEI 也要测试；进入后 cache/index 完成，
   native `RecipesReceivedEvent` 后才登记 viewer。重复 `/tacz reload` 并复查。
5. **REI only，真实专服客户端**：同一进入与 `/tacz reload` 场景；确认原生
   `ClientboundUpdateRecipesPacket` reload 后无内部 reload race，24 条和 Ammo Query 仍在。
6. **JEI + REI**：两者同时装载后分别复查上述查询，确保一个 viewer 的 lifecycle 不影响另一个。
