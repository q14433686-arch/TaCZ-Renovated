# 发布物料：TaCZ: Renovated（26.2 线）

> 使用说明：§1 是 GitHub Release 正文（整段复制）；§2 是发布操作清单；
> §3 是平台规则分析（为什么首发只上 GitHub）。
> 文案纪律：只声称实测过的（AGENTS §2）；正文只描述较新的 Minecraft 环境，
> 不把具体版本号写死；准确的支持范围以当前上传文件和平台标签为准。

---

## §1 GitHub Release 正文（tag 与标题按当前构建填写，不在正文写死版本号）

（正文即 [`RELEASE_NOTES.md`](RELEASE_NOTES.md)，**每次发版重写**。）

---

## §2 发布操作清单（发起人执行）

> **R3 起第 3/5 步可自动化**：push tag 后
> `gh workflow run release -f tag=<tag> -f title=<标题>`，workflow 会
> checkout 该 tag → `gradlew build` → L0 静态自检（jarjar 内嵌库、
> mods.toml 版本串、mixin json 磁盘清单一一对应、`--strict`）→
> 创建 Release 并挂 jar。正文取 `docs/publish/RELEASE_NOTES.md`
> （**每次发版重写**）。本地/沙箱无法下载 CI 产物时，这是标准路径。

1. 把本线工作分支（如 `arena/01a078b2-...`）合并到 `26.2` 分支（发版 commit
   已含版本 bump + CHANGELOG/README 同步 + 验证状态落档）；
2. `bash scripts/check_release_consistency.sh --strict` 必须通过；
3. 在 `26.2` 分支合并 commit 上打 tag（R3 → `26.2_R3`）并 push：
   `git tag 26.2_R3 && git push origin 26.2_R3`；
4. 触发自动化：`gh workflow run release -f tag=26.2_R3 -f title="TaCZ: Renovated"`
   （需 release workflow 已上线。现成的 workflow 草稿在本仓库
   `docs/publish/release.yml`——沙箱/机器人凭据无 `workflows` 权限，无法直接 push
   `.github/workflows/` 新文件，须由发起人在 GitHub 网页把该文件内容
   Add file 落到 `.github/workflows/release.yml` 后即可 dispatch）；
5. 发布后回填 README「选择你的版本」表 / docs 的 GitHub Release 链接。

---

## §3 平台规则分析（要点）

| 平台 | 判定 | 依据 |
|---|---|---|
| **GitHub Release** | ✅ 首发 | 源码仓库自发布，GPL 义务天然满足 |
| **Modrinth / CurseForge / MCMod** | 可发 | 规则同 1.21.11 线 `docs/publish/RELEASE.md` §3/§4/§5/§5.5（本线如跟进再补对应物料） |

三平台共同红线（每个描述页必须包含）：非官方声明 + 源码仓库链接（GPL）+
"问题报本仓库、勿扰原作者" + 实测覆盖如实分级。
