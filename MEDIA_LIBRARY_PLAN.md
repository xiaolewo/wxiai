# 媒体库功能方案

## 目标与范围

- 汇总平台内所有自动生成或用户上传的多媒体资产（图片、视频），提供统一、私有的浏览与管理能力。
- 默认策略：普通成员仅能查看和管理“本人”资产；如启用工作组共享，仅该组成员可见组内资产；管理员具备全局可见与管理权限。
- 提供多维筛选（所属主体、媒体类型、生成来源、文件夹、标签等）、重命名、移动、批量下载、预设分类以及侧边栏入口。
- 所有生成流程（图生图、图生视频、对口型、ComfyUI 工作流等）在选择输入素材时可直接访问媒体库，并保留本地上传通道。

## 架构概览

- **持久层**：在现有 `file` 表基础上新增媒体资产与文件夹元数据表，并扩展存储配置/权限表；统一复用 `Storage` 抽象与 `GeneratedFileManager`。
- **服务层**：新增 `media_library` 服务，负责资产落库、权限判定、路径维护、批量下载、预设文件夹初始化、历史数据回填、缩略图生成。
- **接口层**：FastAPI 新增 `/media-library` 路由族及 `/admin/media-library` 管理路由；前者面向普通成员的资产浏览与操作，后者提供全局审计与设置入口。
- **前端**：SvelteKit 新增 `/(app)/media-library` 大屏页面与跨模块的 `MediaLibraryPicker` 选择器；Sidebar 加入“媒体库”入口；管理员控制台增加“媒体库设置”。

## 数据模型与迁移

- 新表设计：
  - `media_asset`：`id`、`file_id`(FK `file.id`)、`visibility_scope`(`user|group`)、`owner_id`、`display_name`、`media_type`(`image|video`)、`mime_type`、尺寸/时长、`source`、`folder_id`、`tags`(JSON)、`metadata`(JSON)、`created_at`、`updated_at`、`created_by_task_id`、`created_by_user_id`、`thumbnail_path`、`checksum`；索引 `owner_id+visibility_scope`、`created_by_user_id`、`media_type`、`created_at`。
  - `media_folder`：`id`、`parent_id`、`visibility_scope`、`owner_id`、`name`、`slug`、`preset_key`、`sort_order`、`is_locked`、`created_at`、`updated_at`。
  - `media_library_settings`：单例或 per-tenant 表，记录默认可见性策略（是否启用工作组共享）、允许的媒体类型、最大容量、是否开放批量下载等，可在管理员面板维护。
  - `media_asset_audit`（可选）：记录重命名/移动/可见性调整等操作，便于审计。
- 现有表扩展：`file` 增加 `storage_backend`、`size`、`duration`、`hash_type` 等字段（兼容 `GeneratedFiles`）；`group.permissions.media_library` 增加 `{ "view": "mine|group", "manage": ["move", "rename", "delete"] }`；如需持久化管理员设置，可复用 `config` 表。
- 迁移脚本：
  - Peewee 迁移 `022_media_library.py` 与 Alembic 迁移 `<ts>_add_media_library_tables.py` 同步创建。
  - 回填脚本遍历 `flux_tasks`、`jimeng_*_tasks`、`kling_lip_sync_tasks` 等生成记录，导入 `media_asset`，默认 `visibility_scope='user'`，若任务绑定工作组则设为 `group`。
  - 针对缺失文件记录打标并写入 `metadata.missing=true`。

## 权限与隐私控制

- 普通成员：只可访问 `visibility_scope='user'` 且 `owner_id=本人 id` 的资产/文件夹，以及管理员在设置中显式开启的所属工作组资产；无法看到其他用户或其他工作组的数据。
- 工作组共享（可选）：若管理员启用，并在组权限中允许 `view=group`，组成员可见并操作组库；共享范围仅限该组，跨组不可见。
- 管理员：通过 `/admin/media-library` 查看全部资产、过滤特定用户/组、回收/恢复资产、调整设置。
- API 访问层在查询条件中强制加入 scope 过滤，避免越权；服务层在所有写操作中校验操作者是否拥有目标资产。
- 资产卡片与详情展示“创建人”“所属主体”，管理员面板可直接定位来源。

## 管理员面板

- 后端：新增 `Backend/open_webui/routers/admin_media_library.py`（或扩展现有 admin 路由），提供：
  - `GET /admin/media-library/settings`、`PATCH /.../settings`：读取/更新可见性策略、容量限制、是否允许组共享、预设文件夹模板。
  - `GET /admin/media-library/assets`：全局列表，支持按用户、组、任务、时间过滤。
  - `POST /admin/media-library/assets/{asset_id}/reassign`：调整 asset 所属组或转为个人。
  - `PATCH/DELETE /admin/media-library/assets/{asset_id}`：管理员级别的重命名、移除、恢复。
- 前端：在 `src/routes/(app)/admin` 下新增媒体库设置页面，包含：
  - 策略切换（启用组共享、允许批量下载、自动创建预设文件夹等）。
  - 审计表格：列出资产、创建者、可见性、大小、来源；支持跳转至对应用户或任务。
  - 统计视图：按用户/组统计占用容量与资源数量。

## 后端接口设计（更新）

- 用户接口补充 `visibility_scope` 与 `owner_id` 自动绑定当前用户/组，上传/移动/修改操作需再次校验权限。
- `GET /media-library/assets` 参数中 `scope` 仅允许取值 `mine` 或（管理员开启且用户具备权限时）`group`；管理员可传 `user_id`/`group_id`。
- `POST /media-library/assets` 默认 `visibility_scope='user'`；若传 `group_id`，需校验当前用户是否具备该工作组上传权限。
- 批量下载接口对非管理员进行限流或单次数量上限。
- 软删除记录 `deleted_at` 字段，由管理员决定是否彻底清理。

## 前端设计要点

1. **媒体库页面**：
   - 过滤器仅显示用户有权访问的范围；如未开启组共享，仅呈现“我的”筛选。
   - 卡片角标显示“个人”或“工作组”；管理员模式下增加“创建人”标签。
   - 批量操作区在无权限时禁用对应按钮。
2. **MediaLibraryPicker**：根据调用场景传入 `allowedScope` 与 `mediaType`，自动隐藏无权访问的资源。
3. **管理员设置页**：
   - 表单字段对应后端设置接口。
   - 审计表支持快速搜索用户、组、来源，点击可展开资源详情或一键跳转到媒体库页并定位资源。
4. **导航**：
   - Sidebar“媒体库”项对管理员与普通成员均可见；图标旁可显示拥有资源的数量（懒加载）。
   - 管理员在设置面板中可直接打开媒体库页面的管理视图（附带 query `mode=admin`）。

## 预设分类与标签

- `ensure_presets` 根据设置表的模板生成：如 `项目名称`、`角色`、`道具`、`场景`、`集数` 等；可按个人/组分别创建独立树。
- 预设文件夹 `is_locked=true`，管理员可在设置中调整模板；普通用户仅可重命名自建文件夹。
- `media_asset.tags` 支持多维标签（项目、任务、模型等），前端渲染/tag chips，管理员可设置默认标签集合。

## 生成流程集成

- 所有生成管道调用 `record_asset_from_generation` 时明确 `visibility_scope` 与 `owner_id`：
  - 单人任务：`scope=user`，`owner_id=user_id`。
  - 工作组任务：若组共享开启，则 `scope=group`、`owner_id=group_id`，否则仍写入为个人资源。
  - 记录 `created_by_user_id` 以便管理员追溯。
- 生成完成后异步生成缩略图（图片下采样/视频截帧），存入 `thumbnail_path`；前端优先加载缩略图。
- 历史任务回填脚本遵循同样逻辑并写入 `media_asset_audit`。

## 实施步骤

1. **对齐需求**：与业务确认默认可见性、组共享开关、管理员权限范围，并定义设置项。
2. **数据库迁移**：编写 Peewee + Alembic 脚本，分别在 SQLite/MySQL 环境测试；构建回填脚本。
3. **服务与模型实现**：完成媒体库模型/服务、权限校验、批量下载、预设初始化、管理员设置读取；补充单元测试。
4. **管理员路由**：实现设置接口、全局审计列表、资产重分配等；更新 API 文档。
5. **用户路由**：实现资产 CRUD、过滤、文件夹操作；确保所有查询都包含权限过滤。
6. **生成流水线接入**：逐个模块接入记录服务，确保产生的文件均入库；补充集成测试。
7. **前端开发**：媒体库页面、选择器、Sidebar 入口、管理员设置面板、审计列表；实现缩略图懒加载、权限态指示。
8. **测试矩阵**：
   - 后端 Pytest：资产权限、管理员操作、批量下载、设置项、历史回填。
   - 前端 Vitest/Cypress：筛选与权限显示、批量操作、管理员设置、各业务模块挑选媒体库资源。
   - 性能：大数据量分页、并发下载、缩略图生成。
9. **部署与运维**：准备上线脚本、迁移顺序、历史数据回填步骤、异常回滚方案；管理员指南包含隐私策略说明。

## 风险与注意事项

- 跨权限越权风险：务必在数据库层面和 API 层加双重过滤；增加集成测试覆盖。
- 历史数据缺失：回填脚本需生成“缺失文件”标记，前端避免加载失败。
- 大批量下载压力：对普通用户限流或后台生成临时压缩包，必要时接入对象存储的打包服务。
- 缩略图任务排队：可使用 Celery/Redis 队列，防止阻塞请求；管理员面板显示生成状态。
- 配置一致性：`media_library_settings` 与环境变量/`.env` 的默认值需同步，避免多实例配置漂移。

## 后续展望

- 扩展管理员能力，如设定自动清理策略、配额管理与配额提醒。
- 集成内容审核、标签自动生成或智能检索。
- 支持将媒体资产直接同步到知识库或任务系统，构建全流程数据闭环。
- 引入版本管理（同一资产的不同修订）与评论/标注功能。

## 实施进展

- ✅ 建立媒体资产/文件夹/设置/audit 数据模型，支持 SQLite/MySQL/PostgreSQL 迁移。
- ✅ 引入云存储生成文件自动入库流程，与 `GeneratedFileManager` 深度整合。
- ✅ 提供用户与管理员 REST API（筛选、重命名、移动、软删除、重分配、策略配置）。
- ✅ 新增前端媒体库页面、选择器组件，以及管理员设置与资产审计视图。
- ✅ 更新侧边栏/管理菜单入口，完善 README 描述与基础测试覆盖。
