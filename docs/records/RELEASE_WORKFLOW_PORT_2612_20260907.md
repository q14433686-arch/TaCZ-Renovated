# 再次复查 1.21.11：发布自动化适配（26.1.2，2026-09-07）

## 1. 复查边界与逐提交处理

复查开始：2026-09-07 06:41（Asia/Shanghai，UTC 为 09-06 22:41）。
来源为用户本次指定的 **`1.21.11` 正式分支**，固定到
[`03eb457e`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/03eb457ee8ffbcc7c46c329c1cabecc7def4f1c3)。
对照上轮截止 `ccdd9b7c` 后的八个提交，而不是再次将两个 Minecraft 分支整树覆盖。

| 提交 | 内容 | 本线处理 |
|---|---|---|
| [`b7eb7850`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/b7eb7850b8e2f08b5c90883ffd6a6828f3f55ddb) | 1.21.11 string 库实机 PASS 记录 | 不继承本线 PASS，不修改上轮冻结记录 |
| [`77be2043`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/77be20433c7873b0f42d9aa1367f122570a99953) | 1.21.11 bump R3，文档转正 | 不 bump 26.1.2；本线没有对应实机确认 |
| [`240d78cc`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/240d78cce1d686dbf73c4d535788897e44ca13ca) | 来源 CI 日志 | 不复制，不作本线验证依据 |
| [`8ec1b78d`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/8ec1b78dfecfa5fc1d3519415448aced9e0e52ff) | README 填 1.21.11_R3 链接 | 不将本线写成 R3 已发布 |
| [`3f5b4256`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/3f5b42566d89be395a4f123b11230f3fa25a4fca) | PR #44 合并 | 无需重复移植 |
| [`8ab3b6e3`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/8ab3b6e38807374835e3d14db8cfc1ada48a526e) | 发布正文与自动化说明 | 按本线现有发布规范重写为正文草稿/操作说明，保留 MUKSC/TML 来源与未实机边界 |
| [`b68cee6c`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/b68cee6cfa09395ce3f7700e4c1f6d21589ed4b1) | PR #45 合并 | 无独立代码变更 |
| [`03eb457e`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/03eb457ee8ffbcc7c46c329c1cabecc7def4f1c3) | 新建 release.yml | 适配为本线待上线模板，见下文 |

`git diff ccdd9b7c 03eb457e -- src/ build.gradle settings.gradle libs/` **为空**。
本轮没有新的游戏代码要移植。上轮 StringLib 修复继续保留；创造栏搜索树、事件总线接线
在当前 26.1.2 基线本来就有，已重新核对其调用/注册位置，不覆盖为 1.21.11 的实现。
上轮审计见 [`SCRIPT_STRINGLIB_RESTORE_2612_20260906.md`](SCRIPT_STRINGLIB_RESTORE_2612_20260906.md)。

## 2. 必须保留的环境与流程差异

| 项目 | 来源 | 本线 |
|---|---|---|
| 游戏 / NeoForge | 1.21.11 / 21.11.45 | **26.1.2 / 26.1.2.97** |
| Java | 21 | **25** |
| mod_version | 1.1.8+neoforge.1.21.11.R3 | **1.1.8+neoforge.26.1.2.R2（不变）** |
| 最新修复实机状态 | 来源记录 PASS | **未获得本线 PASS，不继承** |
| 发布文档 | 旧的 §2 手动发布清单 | 已有文案分层、LAN 双人冒烟、禁止同名替换与资产世代规则 |
| 资产流程 | 新建 Release + jar | 另有待上线 release-assets 模板；新流程不能绕过其来源/版本纪律 |

本轮不改 Gradle/依赖/mappings/模组 ID，不动渲染、网络 codec 或已有事件接线，
不发布任何 tag/Release，不把 README 的来源线链接变成当前线的发布证明。

## 3. 发布工作流的适配与修正

交付文件：[`docs/publish/ci/release.yml`](../publish/ci/release.yml)。
它是**待维护者复制上线的完整文件**，不在 `.github/workflows/` 中，因此不会自动运行。

1. **Java 21 → 25**；tag 格式限定 `26.1.2_R...`，checkout 明确使用 `refs/tags/`，
   不接受任意分支或 SHA 冒充发布 tag。
2. **修正来源 CLI 参数**：`gh release create` 的 tag 是位置参数，来源中的
   `--tag-name` 不存在。改成 `gh release create "$TAG" "$JAR" --verify-tag ...`。
3. **不任取第一个 jar**：精确检查并使用 `build/libs/tacz-<mod_version>.jar`；
   sources jar 或不同版本产物不能混进附件。
4. **版本和正文预检**：MC / NeoForge / modId / SemVer build metadata / tag 逐项核对，
   运行 `--strict`；正文中的唯一 `release-version` 标记必须等于当前版本。
   新正文保留 `UNRELEASED`，明确拒绝把草稿当成已发布 R2/R3。
5. **L0 从 shell 管道改为结构化 ZIP/TOML/JSON 校验**：避免来源 `set -o pipefail`
   下 `unzip -l | grep -q` 提前关管道可能产生的 SIGPIPE 误失败；同时检查 mods.toml 的
  版本和游戏依赖、mixin 的声明/文件/内容、AT 声明/内容、JarJar 登记路径及内嵌库关键类。
6. **保留本线发布安全约束**：已有 Release（含草稿）直接拒绝，不存在 `--clobber`；
   API 失败不能假装“Release 不存在”。新热修用新版本、新 tag，避免二进制与 Source code
   归档不一致。旧 release-assets 模板保持为独立的已有资产维护方案。
7. **资产留痕**：从实际 checkout 的 `git rev-parse HEAD` 取完整 commit，不用 workflow
   分支的 `GITHUB_SHA`；追加 UTC 时间、文件名与实际 SHA-256。发布前再通过 API 确认
   远端 tag 仍指向该构建 commit。
8. **输入隔离与发布边界**：用户输入通过 env 进入 shell，再引用为参数数组，不直接
   插入 `run:` 脚本；默认创建 GitHub 草稿，显式取消 draft 才公开，不触发其他平台发布。

没有移植来源笼统的“较新的 Minecraft 版本”正文，也没有继承其三批修复的实机 PASS。
新正文按本线 §3 模板列准确环境、当前修复范围、未测试项与 MUKSC / TML 来源。

## 4. API / 行为证据

本轮没有新增 Minecraft / NeoForge 游戏 API 调用；新增的是发布工具和文件结构检查。

- `gh release create [<tag>] [<files>...]`、`--verify-tag`、`--draft`、`--notes-file`、
  `--title`、`--repo`：本地 **gh 2.23.0 `gh release create --help`** 逐项确认；
  [官方手册](https://cli.github.com/manual/gh_release_create)。无 `--tag-name`。
- `gh workflow run release.yml --ref 26.1.2 -f ...`：本地 CLI help 核对；
  [GitHub 手动运行文档](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
  明确 workflow_dispatch 需要文件先存在于默认分支，`--ref` 选择 workflow 版本。
  已纠正旧 ci/README 仅说“文件在哪条分支就能触发”的表述。
- 远端 tag commit：实际只读调用
  `gh api repos/q14433686-arch/TaCZ_Renovated/commits/refs/tags/26.1.2_R2 --jq .sha`
  返回 `436486c2edf4db2da3afed689935c336e5273b07`，确认该 ref 解析路径可用。
- NeoForge JarJar `metadata.json` 的 `jars[].path`：官方 JarJar 固定提交
  [`fea3df4e`](https://github.com/neoforged/JarJar/commit/fea3df4e4d49c1c9377547390199291bf7992d31) 的
  [`MetadataSerializer#serialize`](https://github.com/neoforged/JarJar/blob/fea3df4e4d49c1c9377547390199291bf7992d31/metadata/src/main/java/net/neoforged/jarjar/metadata/json/MetadataSerializer.java)
  与
  [`ContainedJarMetadataSerializer#serialize`](https://github.com/neoforged/JarJar/blob/fea3df4e4d49c1c9377547390199291bf7992d31/metadata/src/main/java/net/neoforged/jarjar/metadata/json/ContainedJarMetadataSerializer.java)。
  内嵌 LuaJ 与 commons-math3 的类名来自本线实际 vendored jar 清单。
- mods.toml / AT / mixin 的期望值取自本线 `gradle.properties`、实际模板及资源文件，
  不硬抄 1.21.11 的文件数、依赖或版本串。

## 5. 本轮验证与未验证

- **17 项发布门禁 unittest 通过**（含参数化异常用例）：
  `python3 -m unittest discover -s scripts/tests -p 'test_release_*.py' -v`。
  使用临时合成 ZIP，不构建、不执行 Minecraft。
- 正常产物、错误游戏线/tag/版本、草稿/重复正文标记、sources/错误 jar、错误元数据、
  缺/多/变更 mixin、AT、未登记/缺失/损坏内嵌库、缺 StringLib、路径穿越、重复 ZIP
  条目及仅在成功后生成 GitHub outputs 的行为均有拒绝或通过测试。
- YAML 结构与所有 `run:` 的 `bash -n` 通过；确认 Java 25、tag checkout、默认 draft，
  不存在 `run:` 内直接插入 `${{ ... }}` 用户输入的路径。
- 用临时 **gh/git 本地 stub** 执行关键 shell：六种 tag 输入、已有 Release、API 失败、
  tag 移动、draft true/false、含 shell 语法的字面量标题、commit/sha256 记录全部符合预期；
  **没有通过这些测试调用真实的创建/上传 API**。
- `--strict`、文档链接、原有 CI 的 mixin/语言静态检查与 `git diff --check` 通过。
- 当前源码 `python3 scripts/verify_release.py --tag 26.1.2_R2` **按预期退出 1**，
  原因是正文仍为 UNRELEASED。这是防误发布，不是应当绕开的失败。
- actionlint 安装尝试受二进制下载 TLS 失败阻挡，**未执行 actionlint**，不冒充通过。
- **本线 CI 已通过**，代码提交为
  [`27beda5f`](https://github.com/q14433686-arch/TaCZ_Renovated/commit/27beda5fc7559b5fb7597c0a3d1e6b8f5bc3caa9)：
  [完整 build（含 jar 产物上传）](https://github.com/q14433686-arch/TaCZ_Renovated/actions/runs/34065485036)、
  [compile-check](https://github.com/q14433686-arch/TaCZ_Renovated/actions/runs/34065485041)、
  [consistency](https://github.com/q14433686-arch/TaCZ_Renovated/actions/runs/34065485039)
  均为 success；不是借用 1.21.11 的 CI。随后仅补充本轮验证/权限记录，没有修改生产代码。
- CI artifact `9998808775` 对应该代码提交，API 确认已上传；尝试下载供本地真实 jar L0
  复核时，GitHub Actions 的 blob 存储下载发生 EOF。因此 **L0 校验器目前只有合成 ZIP
  回归，没有对该真实产物执行**，不能把完整 build 成功等同于该新门禁的运行成功。
- **尚未上线/运行新的 release workflow，没有真正的发布上传与最终 tag L0 验收**。
  本线游戏实机、Phoenix、LAN 双人和专服复测仍未执行。上轮“沙箱不能完整构建”的记录
  保留为当时快照；本轮通过本工作分支 CI 补验，不倒改历史。

## 6. 权限与交接

普通工作分支的实际 push 已成功。另用独立、仅包含 `.github/workflows/release.yml`
的提交尝试安装正式件，GitHub 明确拒绝：

```text
refusing to allow a GitHub App to create or update workflow
`.github/workflows/release.yml` without `workflows` permission
```

只撤回了这笔**未推送成功**的工作流安装尝试，保留普通源码/文档与 CI 日志提交；
远端没有安装该 workflow，也没有发生强推或其他分支/tag 变更。这是工作流写权限缺失，
不是整个 GitHub 连接失效；不要求维护者提供任何凭据。

维护者需要做的操作只有一个 workflow 文件的复制上线：普通改动合入后，将
[`docs/publish/ci/release.yml`](../publish/ci/release.yml) **全文**复制为默认分支的
`.github/workflows/release.yml`。具体按钮、先决文件、tag/正文准备与失败处理见
[`ci/README.md`](../publish/ci/README.md)。

**复制上线 ≠ 当前 R2 可以直接发版**：新版本/正文仍需维护者确认并完成本线验收；
不能删掉草稿门禁来复用旧 R2 tag。
