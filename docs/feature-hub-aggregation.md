# Feature Hub Aggregation Proposal

This document captures the proposed navigation reshuffle that groups related media-generation capabilities under consolidated vendors and brands. The intent is to reduce sidebar clutter, align with how users reason about providers, and prepare the UI for upcoming video features without rewriting the existing feature screens.

## Guiding Principles

- **Provider-first grouping**: Users choose the provider (e.g. 即梦, 可灵, 谷歌, MJ, 海螺) before deciding which concrete capability to launch. The sidebar should reflect that mental model.
- **Shared surface, dedicated modules**: Each provider hub retains the current layout/controls inside the tool views, but navigation becomes a two-step experience (select hub ➜ pick capability).
- **Unified history within a hub**: Every capability surfaced inside the same hub contributes to a shared task history so users can monitor all activity for that vendor in one place.
- **Forward compatibility**: The structure must absorb pending features (e.g. MJ 视频, 海螺生图) with minimal future churn.

## Proposed Sidebar Hubs

| 新分组         | 子功能 (现有 + 规划中)                                                  | 历史记录策略                                       |
| -------------- | ----------------------------------------------------------------------- | -------------------------------------------------- |
| **即梦聚合**   | 图像编辑、智能扩图、即梦视频 (现有)，即梦4 图像生成、DreamWork 图像生成 | 共用「即梦历史」时间线；任务类型标签区分具体功能   |
| **可灵中心**   | 可灵视频、视频口型 (Lip Sync)                                           | 共用「可灵历史」；记录里标识是视频生成还是口型同步 |
| **谷歌媒体**   | Banana 图像生成、Veo 视频                                               | 共用「谷歌历史」；后续若扩展 Gemini 系列亦可纳入   |
| **MJ 合作区**  | MJ 图像生成 (现有)，MJ 视频 (规划)                                      | 共用「MJ 历史」；支持筛选图片/视频                 |
| **海螺工作室** | 海螺视频 (现有)，海螺生图 (规划)                                        | 共用「海螺历史」；允许按媒介过滤                   |

### Sidebar Layout Concept

- 一级节点使用 Provider 中文命名（例如「即梦聚合」「可灵中心」）。
- 展开后显示具体功能的快捷入口，保持原有 UI 布局与交互逻辑。
- 历史记录入口放在二级菜单底部，点击后展示该 Provider 的统一历史视图。

## Unified History Requirements

- **数据聚合**: 后端需要为每个 Provider 定义统一的查询接口，合并原有任务表（例如 DreamWork & Jimeng & Jimeng4 -> 即梦）。
- **类型标识**: 统一历史响应需携带 `service_type` 或类似字段供前端标注任务来源。
- **筛选与分页**: 历史视图应支持按功能类型筛选、按状态查询，与当前分页策略保持一致。
- **未来扩展**: 预留扩展字段（如 `media_type`、`provider_variant`），以便后续新增子功能时无需变更 schema。

## Frontend Considerations

- **导航重组**: 调整 Sidebar 结构，将现有功能节点迁移到新父分组下；保留原有图标/名称以降低认知成本。
- **路由映射**: 一级节点点击默认打开最近使用的子功能或显示概览面板；二级节点链接至现有页面。
- **历史页面**: 基于现有历史组件复用，改造为 Provider 级别入口，支持标签/筛选。
- **状态同步**: 统一历史需要与任务轮询、Socket 更新机制兼容，确保新增结构不会打断实时刷新。

## Backend Touchpoints (for later execution)

1. **Provider 枚举映射**：在任务创建层（例如 `service_type` 或 credit 日志）中确保能够区分即梦/可灵/谷歌/MJ/海螺。
2. **聚合查询接口**：新增例如 `/api/v1/jimeng/history/aggregate` 之类的端点返回跨表数据；或者在现有历史 API 中增加 `provider` 参数以触发聚合逻辑。
3. **统一历史表视图**：可考虑创建数据库视图或在 ORM 层构建 union 查询以保持分页性能。
4. **权限与计费**：调整信用账单展示，按 Provider 显示使用量，确保历史与计费统计一致。

## Rollout Recommendations

- **阶段 1（信息架构）**: 先引入新的 Sidebar 分组与历史入口，不改变功能页面；确保老入口仍可通过重定向访问以减少用户迷失。
- **阶段 2（历史聚合）**: 完成统一历史接口，更新前端历史视图展示；引入类型筛选和标签。
- **阶段 3（体验扩展）**: 为每个 Provider hub 添加概览面板（总任务数、最近产出、余额等），进一步提升导航价值。

## Open Questions

- 总账本如何呈现 Provider 聚合的消耗？需要与 Credit Log 集成的详细设计。
- 是否需要在 sidebar 顶部保留「全部历史」视图以满足跨 Provider 检索需求？
- 子功能的快捷方式是否支持收藏/置顶，避免多级导航增加操作步骤？

---

This proposal keeps the existing operational flows intact while aligning the navigation with provider branding. Once approved, subsequent design docs should detail the UX wiring (mockups, routing table updates, API contract changes) before implementation.
