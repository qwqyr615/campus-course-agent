"""FastMCP Streamable HTTP 服务。在 backend/ 下执行：python mcp_server.py"""

from typing import Annotated
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from pydantic import Field
from app.config import settings
from app.database import SessionLocal
from app.dependencies.mcp_auth import user_id_from_authorization
from app.services.schedule_service import list_schedules_as_dict

# 创建一个名为 "campus-course-agent" 的 MCP 服务实例。
mcp = FastMCP("campus-course-agent")


def _current_user_id() -> int:
    """从当前的HTTP的请求头拿到authorization 然后解析出 user_id"""

    headers = get_http_headers() or {}
    auth = headers.get("authorization") or headers.get("Authorization")
    return user_id_from_authorization(auth)


@mcp.tool()
def get_my_schedules(
    date: Annotated[
        str | None,
        Field(
            description="可选参数，上课的日期，格式：YYYY-MM-DD，不传则返回全部的列表"
        ),
    ] = None,
) -> dict:
    """查询当前登录用户自己的课表，不能通过参数指定其他用户。
    可查询指定日期或全部课表，不支持日期范围参数。
    查询一周等日期范围时，可省略 date 获取全部课表，再按目标日期范围筛选。
    成功返回 items 和 count；每条记录包含 date、period、course_id、
    course_name 和 location，分别表示上课日期、节次、课程 ID、课程名称和地点。
    失败返回 error 和空 items；含 error 时表示查询失败，不能解释为没有课程。
    """

    try:
        user_id = _current_user_id()
        db = SessionLocal()
        try:
            items = list_schedules_as_dict(db, user_id, date)
            return {"items": items, "count": len(items)}
        finally:
            db.close()
    except Exception as exc:
        return {"error": f"查询课表失败 {exc}", "items": []}


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
        path=settings.MCP_PATH,
        uvicorn_config={"ws": "websockets"},
    )
