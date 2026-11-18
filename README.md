# 北岭 · 键峰结算工坊

北岭边缘计算小组的每小时存活键峰值结算演练：遥测站点的键上线（put/覆盖）与下线（delete）记录乱序到达，站点要知道**每小时最多有多少键同时存活**。本站按发生时间处理乱序记录、整批原子切换迟到修订、按选择的小时结算，并对照展示待结算、已发布与修订前后的峰值。

**这是确定性教学结算模型。MySQL 8.0 仅保存业务元数据，所有峰值由 Python 按统一口径演算。**

## 场景与模块

站点 7 人小组过去在电子表格里手工对齐乱序记录，痛点是：迟到记录不知道影响哪些小时、整批补传 halfway 状态难恢复、并发补传与结算互相覆盖。上游为站点模拟事件流；本站替代补传登记、切换与结算；下游是运营复核与值班交接。

- 修订批次：一组带发生时间的 put/delete 操作，登记为待发布；发布即**整批一次性切换**，中断可恢复，同批重试只生效一次。
- 迟到重算：补传切换后**只重算受影响的小时**（最早影响小时 → 结算水位），起点状态收敛即停止，并留下重算清单与修订前后峰值对照。
- 结算队列：选择结算到哪一小时，worker 异步执行；水位线在提交时快照，**发布期间到达的修订留到下一次结算**。
- 峰值总览：已发布峰值（每小时峰值、起止键集、写入来源）与待结算实时预览（不落库）。
- 管理员审计：记录写操作账号、路由与 HTTP 结果，包含权限拒绝。

| 角色 | 页面与权限 | 典型动作 |
|---|---|---|
| admin 管理员 | 全业务页面与审计 | 登记批次、发布切换、提交结算、查看审计 |
| operator 操作员 | 三业务页面，不可看管理员审计 | 补传修订、恢复中断切换、推进结算水位 |
| viewer 观察员 | 三业务页面只读 | 阅读峰值与修订前后对照，写请求在 API 层 403 |

## 启动与账号

```bash
cp .env.example .env
docker compose config --quiet
docker compose up -d --build
# 默认启动自动执行；手动重跑不覆盖已存在的批次、结算、账号
docker compose exec -T backend python -m scripts.seed_demo
```

[前端入口](http://localhost:18245) · [后端接口文档](http://localhost:19245/docs)，数据库映射端口 17745。

三个本地演示账号是 `admin@beiling.test` / `operator@beiling.test` / `viewer@beiling.test`，统一密码 `EdgeStore!17`。`.env.example` 提供固定本地数据库与 JWT 演示凭据，上线前替换。

```bash
# 只清理本项目与其演示卷
docker compose down -v --remove-orphans
```

## 09:00—10:00 的工作剧本

1. 09:00 operator 登录，打开“峰值总览”：结算水位停在 10 点，已发布 9 点峰值 3、10 点峰值 4，待结算预览 11 点峰值 4。
2. 09:05 打开“修订批次”：两条已发布基线，两条待发布演练批次。
3. 09:10 **迟到删键跨小时**：发布 `late-delete-sensor04`（sensor-04 实际 10:10 离线）。10 点峰值 4→3，重算清单只有 10 点；待结算预览 11 点峰值随承接降为 3。
4. 09:20 打开“结算队列”，提交“结算到 `2026-11-18T11:00:00Z`”，刷新至已发布，11 点峰值 3 落库。
5. 09:30 **切换前中断**：发布 `noon-backfill-12` 时勾选“演练：切换前中断”→ 500，批次停在 `switching`；不勾选再点一次 → 恢复并完成；再点 → 序号、差集、时间全不变（幂等）。
6. 09:40 **发布时并发补传**：提交带 3 秒演练延迟、结算到 12 点的任务；窗口内登记并发布新批次——本次结算水位线不含它，它自己的切换把已结算小时修补到最新，下一次结算才把它纳入水位线。
7. 09:50 viewer 复核只读页面；10:00 admin 打开“操作审计”核对写操作记录。

Seed 含两条已发布基线批次（09–11 点事件）、两条待发布演练批次（迟到删键、正午补传）和一个已执行到 10 点的结算。账户、批次、结算以自然键查缺插入，重复 seed 不改变已存在数据。

## 核心算法与口径

- 事件为 `{op, key, value?, event_time}`；op ∈ `put`（覆盖写入）/ `delete`（删键）。接收时分配单调 `recv_seq`。
- **规范序**：按（发生时间, recv_seq）处理——乱序到达按发生时间，同一时刻按接收顺序。
- 存活集合：put 加入键（重复覆盖不重复计数），delete 移除键（删除不存在的键是无操作）。整点事件归属以该整点开始的小时。
- **小时峰值**：起点承接上一小时末状态，逐事件应用，取该小时内同时存活键数的最大值；空小时峰值等于承接数。
- **结算**：`meta.horizon` 及之前的小时为已发布。结算把 (horizon, 目标] 逐小时写入 `hour_states` 并推进水位；水位线（max publish_seq）在持锁提交时快照，快照之后发布的修订不进入本次结算，留到下一次。
- **修订切换**：`staged → switching → published`。`switching` 是崩溃恢复检查点；切换在同一事务内完成状态翻转与受影响小时重算（整批一次性）。只重算 [最早影响小时, 结算水位]，起点状态收敛即停止；`published` 批次重试直接返回原结果（同批只生效一次）。
- **恢复**：进程中断后，`switching` 批次在下一次发布请求中继续；`queued/running` 结算由 worker 按提交顺序幂等重放。
- **序列化**：进程内切换锁 + `meta` 行 `SELECT ... FOR UPDATE` 双重序列化修订切换与结算提交；登记新批次（摄入）不加锁，发布期间始终可接收新操作。
- 每批 1–500 条操作；键 1–64 字；put 的 value 为不超过 200 字的字符串（允许空串）；时间一律 UTC，结算目标必须整点对齐；单次结算跨度 ≤744 小时。重名 409，引用不存在 404，非法输入 422，观察员写操作 403。
- 演练参数（仅本地演练用）：发布支持 `simulate_crash`（切换在生效前中断）与 `delay_seconds`（拉长切换窗口）；结算支持 `delay_seconds`（拉长发布窗口，观察并发补传被留到下一次结算）。

## 技术栈与代码组织

| 服务 | 实现与作用 |
|---|---|
| frontend | 原生 HTML/CSS/JS ES 模块，Nginx 1.27，土橙材料样本册视觉 |
| backend | Python 3.11、FastAPI、SQLAlchemy、PyMySQL、JWT 与 PBKDF2 密码 |
| worker | 独立 Python 进程，Redis BLPOP，执行结算、崩溃恢复重放、心跳健康检查 |
| db | MySQL 8.0，持久化修订/事件/小时峰值/结算/用户与审计 |
| redis | Redis 7，异步队列与持久卷 |

`backend/src/` 分为 config/models/schemas/services/controllers/routes/middlewares/utils/constants。核心演算在 `services/engine.py`（纯函数：规范序、承接、逐小时峰值）；`services/revisions.py` 负责整批切换与受影响小时重算；`services/settlements.py` 负责水位线结算与幂等重放；`services/peaks.py` 负责已发布/待结算视图。`backend/scripts/seed_demo.py` 种子与初始化；`backend/migrations/README.md` 为 schema v1 说明。修订/结算两实体各自贯穿 model/schema/service/route 与前端 api/store/page。

`frontend/src/` 包含 api/stores/types/components/common/hooks/pages/router/utils/constants，表格/状态徽章/页头跨页共享，HTML 转义与反馈工具复用。角色/批次状态/结算状态枚举在 `backend/src/constants/enums.py` 和 `frontend/src/constants/enums.js`。

Docker 恰好 5 服务，全部 healthcheck；backend 依赖 db/redis healthy，worker 还等待 backend 完成 seed；frontend 等待 backend healthy。命名卷保存 MySQL、Redis 及 worker 证据（`settlement-<id>.json` 与心跳）。Nginx `/api/` 剥前缀转发后端。

环境变量：COMPOSE_PROJECT_NAME、FRONTEND_PORT、BACKEND_PORT、DB_PORT、MYSQL_PASSWORD、MYSQL_ROOT_PASSWORD、JWT_SECRET、SEED_DEMO；容器连接还配置 DATABASE_URL/REDIS_URL；演练证据目录 ARTIFACTS_DIR。端口可在 .env 整体调整避免冲突。

本地开发推荐修改代码后 `docker compose up -d --build`。也可用虚拟环境安装 backend/requirements.txt，启动 Compose db/redis，设置可达 DATABASE_URL/REDIS_URL/JWT_SECRET，进入 backend 执行 `uvicorn src.main:app --reload`；worker 须有可写 `/artifacts`（或设置 ARTIFACTS_DIR）并执行 `python -m src.worker`。

## 已知边界

- 教学结算模型：单 worker 与按钮刷新；不提供多 worker 分布式锁、SSE。
- 峰值按小时分组重放事件演算，未做增量索引；教学规模（≤744 小时/次、≤500 操作/批）下足够快。
- 恢复语义覆盖进程中断与重试幂等；不模拟多副本、时钟回拨与网络分区。
- 切换锁为进程内锁 + MySQL 行锁；跨进程（backend/worker）由行锁保证互斥，演练延迟会阻塞其他切换与结算。
- 时间一律按 UTC 整点对齐，页面不做时区换算。
- Web 双字体来自 Google Fonts，离线回退到 serif/monospace。

MIT License，见 LICENSE。
