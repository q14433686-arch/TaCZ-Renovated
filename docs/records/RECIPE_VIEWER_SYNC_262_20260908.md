# 记录：JEI / REI 枪匠台弹药配方与 Ammo Query 同步修复（26.2，2026-09-08）

- **分支**：`arena/01a07f93-tacz-renovated`（基线 `de0928f0afb770a33dc6a0c8f1a36042d92fb229`）。
- **范围**：默认枪包的 24 条 `data/tacz/recipe/ammo/*.json` 弹药枪匠台配方；JEI / REI 的
  工作台查询以及内置 **TaCZ Ammo Query**。该问题同时影响单人与远程专服客户端，单机成功
  不能替代专服验收。
- **证据级别**：NeoForge 26.2.0-stable 官方源码/patch、JEI 30.24 源码、REI 26.2.820
  源码及 Architectury 21.0.2 源码静态闭环；本沙盒没有 Java/JDK，尚未执行 Gradle 或游戏内
  测试，**不宣称 PASS**。

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

本环境没有 `java`（`JAVA_HOME` 未设置且 PATH 内无 Java），因此
`./gradlew compileJava` 在 Gradle 启动前即失败；不能把上述静态结果写成编译或实机 PASS。

## 5. 待执行的验收

以下须在 Java 25 / NeoForge 26.2.0.64 环境完成，并记录实际 commit、JEI/REI 版本与完整日志：

1. `./gradlew compileJava`（至少）和生产 jar build；确认默认 24 条 ammo JSON 在 server
   datapack reload 后仍无 stream-codec/payload 编码异常。
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
