# TODO：让 save_plan 可被 MCP 直接复用

目标：服务层与 HTTP 解耦——入参只用原始值（`user_id: int`、`content: str`），
空白规范化（strip）下沉到服务层，校验规则只有一份。

## 1. 改 backend/app/services/study_plan_service.py（主要改动）

- [ ] `create_study_plan` 签名改为 `(db, user_id: int, content: str)`，
      去掉 `current_user: User` 和 `data: StudyPlanCreateRequest`
- [ ] 函数开头加 `content = (content or "").strip()`（strip 下沉，
      MCP 不走 Schema 也能挡住纯空白；`or ""` 防 None）
- [ ] 落库改为 `StudyPlan(user_id=user_id, content=content)`
- [ ] 顺手修错别字："请收入学习计划内容" → "请输入学习计划内容"
- [ ] 清理 import：删掉 `from app.models.user import User`；
      schemas 那行只留 `StudyPlanResponse`

```python
def create_study_plan(db: Session, user_id: int, content: str) -> StudyPlanResponse:
    """创建学习计划（HTTP 与 MCP 共用的入口）"""
    content = (content or "").strip()
    if not content:
        raise BusinessException(message="请输入学习计划内容")
    if len(content) > STUDY_PLAN_MAX_LENGTH:
        raise BusinessException(message=f"计划内容不能超过{STUDY_PLAN_MAX_LENGTH}")
    row = StudyPlan(user_id=user_id, content=content)
    db.add(row)
    db.commit()
    db.refresh(row)
    return StudyPlanResponse.model_validate(row)
```

## 2. 改 backend/app/api/study_plan.py（适配新签名）

- [ ] `create_plan` 里的调用改为：
      `study_plan_service.create_study_plan(db, current_user.id, data.content)`
- [ ] 路由参数 `data: StudyPlanCreateRequest` 保留不动
      （Schema 继续做 HTTP 边界：类型校验 + OpenAPI + 进门先 strip 一遍，
      和服务层的 strip 幂等，属于纵深防御）

## 3. 可选：同一模式统一另外两个函数（MCP 若也暴露查询/删除）

- [ ] `list_page_plans(db, user_id: int, page, page_size)`
- [ ] `delete_study_plan(db, user_id: int, plan_id: int)`
- [ ] 对应两个路由的调用改为传 `current_user.id`

## 不需要动

- schemas/study_plan.py、models/study_plan.py、config.py
- 前端全部（URL / 请求体 / 响应结构都没变）
- dependencies/auth.py（鉴权留在 HTTP 层，MCP 有自己的身份解析）

## 验收标准

改完后 MCP 侧调用只需要：

```python
with SessionLocal() as db:
    plan = study_plan_service.create_study_plan(db, user_id, content)
```

不需要 Depends、不需要 pydantic 模型、不需要 User 对象；
空/超长/strip 校验与网页行为完全一致。

## 遗留事项（MCP 接入时再处理）

- MCP 侧传入的 user_id 需自行确认有效（HTTP 路径由 get_current_user 保证；
  无效 user_id 落库会触发外键约束 → 500 兜底）
- 验证方式：改完启动后端，网页保存/删除/分页一遍，行为应与改前完全一致
