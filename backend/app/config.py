from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # 后端项目的根路径


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"
    # MCP 服务
    MCP_HOST: str = "127.0.0.1"
    MCP_PORT: int = 8001
    MCP_PATH: str = "/mcp"
    # 大模型（OpenAI 兼容接口）
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL_NAME: str
    # Agent 循环上限：模型 -> 工具 -> 模型 的最大轮数，防止死循环
    AGENT_RECURSION_LIMIT: int = 10
    # 向量模型与对话模型分开配置。
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.siliconflow.cn/v1"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    CHROMA_COLLECTION: str = "course_docs"
    CHROMA_HOST: str = "127.0.0.1"
    CHROMA_PORT: int = 8002
    CHROMA_CHUNK_SIZE: int = 500
    CHROMA_CHUNK_OVERLAP: int = 50

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100M
STUDY_PLAN_MAX_LENGTH = 2000
# 课程资料单独归档，不放进已公开挂载的 uploads 目录。
KB_DIR = BASE_DIR / "data" / "kb"
KB_DIR.mkdir(parents=True, exist_ok=True)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}
