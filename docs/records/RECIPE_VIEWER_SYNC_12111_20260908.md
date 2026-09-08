# 记录：JEI / REI 枪匠台弹药配方与 Ammo Query 同步修复（1.21.11，2026-09-08）

- **分支**：`arena/01a081f0-tacz-renovated`（基线 `ddef53384568da5fc56429f27640826c03ddf59b`）。
- **来源**：回传 [PR #52](https://github.com/q14433686-arch/TaCZ_Renovated/pull/52)
  （`26.2` 线 `29e15656b08df6a15f7ae4c18e97665cf691b4cd` + 文档补记
  `711d3d0099886bd0cbaa322fc1e9e83d4a3eee8a`）的语义，按本线 NeoForge 21.11.45 /
  JEI 27.30.0.76 / REI 21.11.816 重新核 API 后落地。
- **范围**：默认枪包的 24 条 `data/tacz/recipe/ammo/*.json` 弹药枪匠台配方；JEI / REI 的
  工作台查询以及内置 **TaCZ Ammo Query**。该问题同时影响单人与远程专服客户端，单机成功
  不能替代专服验收。
- **证据级别**：NeoForge 21.11 官方源码/patch、JEI 1.21.11 源码、REI 1.21.11 源码静态闭环；
  本沙盒没有 Java/JDK，尚未执行 Gradle 或游戏内测试，**不宣称 PASS**。

## 1. 复现与根因

默认包中该目录共 24 个 JSON；每个都声明
`"type": "tacz:gun_smith_table_crafting"`，`result.type` 为 `ammo`。这些不是原版工作台
配方，必须由 TaCZ 的 JEI / REI 插件登记。

已检查的用户 `latest.log`（26.2 线同源故障）给出两条独立、会相互叠加的故障链：

1. 枪包同步后已记录 `guns=… ammo=… attachments=… blocks=… recipes=…`，但 REI
   在 `GunSmithTableDisplay.<init>` 失败。`GunSmithTableIngredient#getIngredient()`
   对尚未按 level `RegistryAccess` 解析的 raw tag 材料允许返回 `null`；旧构造器把这个
   `null` 直接交给 `EntryIngredients.ofIngredients(...)`。一次异常中断
   `REIClientPlugin#registerDisplays`，后面的 attachment 与 Ammo Query display 均未登记。
2. TaCZ 自定义 `ServerMessageSyncGunPack` 会安装 common cache / client indexes，但它本身
   不会重建 JEI 的插件。JEI 1.21.11 的 NeoForge `StartEventObserver` 用
   `RecipesReceivedEvent` 作为启动屏障，且在已启动且有同步配方时用同一事件 restart。
   因而不能把自定义 cache payload 的到达当作 JEI 已刷新。

此前 bridge 通过反射调用 REI 内部的
`RoughlyEnoughItemsCoreClient#reloadPlugins(MutableLong, ReloadStage)`；该调用会在
REI 自己由 recipe update 启动的异步重载尚未结束时嵌套，出现 “found 1 existing reload task”
或被 1s 抑制。反射调用返回只表示请求已发出，不表示 REI 重建完成，不能作为完成判据。

## 2. 1.21.11 API / 时序证据

| 组件 | 已核类与签名 | 结论 |
|---|---|---|
| NeoForge server | [`OnDatapackSyncEvent#sendRecipes(RecipeType<?>...)`](https://github.com/neoforged/NeoForge/blob/28c765fc63a63336042b8c2ac40ece046a36bc78/src/main/java/net/neoforged/neoforge/event/OnDatapackSyncEvent.java)（`21.11` tip `28c765fc…`） | 公开 API；请求指定 recipe type 的完整内容发送。 |
| NeoForge send order | [`PlayerList.java.patch`](https://github.com/neoforged/NeoForge/blob/28c765fc63a63336042b8c2ac40ece046a36bc78/patches/net/minecraft/server/players/PlayerList.java.patch) | `OnDatapackSyncEvent` 在 `ClientboundUpdateRecipesPacket` 与 `CommonHooks.sendRecipes(...)` 之前 post；本模组在 event 内先发送 cache，因此后续原生 recipe 数据包在该 cache 后发出。 |
| JEI 27.30 / 1.21.11 | [`JustEnoughItemsClient#onRecipesReceivedEvent`](https://github.com/mezz/JustEnoughItems/blob/ff23de785ced1dfed38dd5360b852cbad49adb27/NeoForge/src/main/java/mezz/jei/neoforge/JustEnoughItemsClient.java) + [`StartEventObserver#register / #onRecipesReceivedEvent`](https://github.com/mezz/JustEnoughItems/blob/ff23de785ced1dfed38dd5360b852cbad49adb27/NeoForge/src/main/java/mezz/jei/neoforge/startup/StartEventObserver.java)（branch tip `ff23de78…`） | 前者仅在 `recipeMap.values()` 非空时写入 `Internal.setClientSyncedRecipes(recipeMap)`；后者 LOWEST priority 监听 event，首次满足 login + recipe sync 时 start，已启动且该 state 已设置时 restart。 |
| REI 21.11.816 / 1.21.11 | [`RoughlyEnoughItemsCoreClient#registerEvents`](https://github.com/shedaniel/RoughlyEnoughItems/blob/1a8053d02e2028e641ee2f4f57db2b12404c8303/runtime/src/main/java/me/shedaniel/rei/RoughlyEnoughItemsCoreClient.java)（branch tip `1a8053d0…`） | `PRE_UPDATE_RECIPES` 请求 START，`ClientRecipeUpdateEvent.EVENT` 请求 END。 |
| REI entry API | [`EntryIngredients#ofIngredient(Ingredient)`](https://github.com/shedaniel/RoughlyEnoughItems/blob/1a8053d02e2028e641ee2f4f57db2b12404c8303/api/src/main/java/me/shedaniel/rei/api/common/util/EntryIngredients.java) / [`EntryIngredient#empty()`](https://github.com/shedaniel/RoughlyEnoughItems/blob/1a8053d02e2028e641ee2f4f57db2b12404c8303/api/src/main/java/me/shedaniel/rei/api/common/entry/EntryIngredient.java) | REI 转换器要求非 null `Ingredient`；空材料格应建模成空 `EntryIngredient`，而非传 null。 |

`OnDatapackSyncEvent#sendRecipes` 把 type 加入 `recipeTypesToSend`；随后
`CommonHooks.sendRecipes` 按 type 从 server `RecipeMap` 选取 `RecipeHolder` 并发送
`RecipeContentPayload`。因此同步本模组自己的
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
推送后由 GitHub Actions Java 环境验证编译。

## 5. 待执行的运行期验收

以下须在 Java 21+ / NeoForge 21.11.45 环境完成，并记录实际 commit、JEI/REI 版本与完整日志：

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

完整联机矩阵见 `docs/DEDICATED_SERVER_TEST.md` L3 行 12–14。
