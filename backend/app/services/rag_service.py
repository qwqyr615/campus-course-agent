import logging
from pathlib import Path
from httpx import get
from pypdf import PdfReader
from docx import Document
from app.common.exceptions import BusinessException
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)


def extract_document_text(path: Path) -> str:
    """从支持的资料文件中提取纯文本，空内容或解析失败时抛出业务异常"""
    # 数据库记录可能存在，但磁盘文件已被手动移走。
    if not path.is_file():
        raise BusinessException(message="资料文件不存在", code=404)
    # 后缀名
    ext = path.suffix.lower()

    try:
        if ext in [".md", ".txt"]:
            return path.read_text(encoding="utf-8-sig")
        elif ext == ".pdf":
            with path.open("rb") as source:
                reader = PdfReader(source)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
        # DOCX 读取正文段落与表格单元格，不保留排版。
        elif ext == ".docx":
            doc = Document(str(path))
            parts = [p.text for p in doc.paragraphs]
            parts.extend(
                "\t".join(cell.text for cell in row.cells)
                for table in doc.tables
                for row in table.rows
            )
            text = "\n".join(parts)
            # 只处理已约定的四种格式，旧版 .doc 也不在范围内。
        else:
            raise BusinessException(message="不支持的文档格式", code=400)
    except BusinessException:
        raise
    except Exception as exc:
        logger.exception("提取文档文字失败：%s", path.name)
        raise BusinessException(
            message="无法读取文档，请确认文件未损坏、未加密，且文本文件采用 UTF-8 编码",
            code=400,
        ) from exc

    text = text.strip()
    # 空白文档或没有文字层的扫描件不能提供文字预览。
    if not text:
        raise BusinessException(
            message="未能抽取到文本，空白文档或扫描件无法预览", code=400
        )
    return text


# Embedding 客户端工厂
def _embeddings() -> OpenAIEmbeddings:
    """创建向量模型客户端；缺少莫要时在调用钱给出明确错误"""
    # 未配置密钥时先停止，避免将配置缺失误判为远程服务故障。
    if not settings.EMBEDDING_API_KEY:
        raise BusinessException(message="请先配置 EMBEDDING_API_KEY", code=500)
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.EMBEDDING_BASE_URL,
        api_key=settings.EMBEDDING_API_KEY,
        # 兼容本节所用的 OpenAI 兼容服务，关闭 OpenAI 的 token 长度预检
        check_embedding_ctx_length=False,
        chunk_size=32,
    )


# 获取 Chroma 客户端
def get_vectorstore() -> Chroma:
    """连接共享的 Chroma 服务并打开课程资料集合。"""
    return Chroma(
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=_embeddings(),
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )


def delete_by_doc_id(doc_id: int) -> None:
    """按文档 ID 删除片段；删除操作不需要调用 Embedding 服务。"""
    store = Chroma(
        collection_name=settings.CHROMA_COLLECTION,
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )
    store.delete(where={"doc_id": str(doc_id)})


# 入库
def ingest_kb_file(path: Path, source: str, doc_id: int) -> int:
    """提取文本并写入向量库，返回实际保存的片段数。"""
    text = extract_document_text(path)
    # 先按段落拆分，再按字符数拆分，避免过长的段落被截断。
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHROMA_CHUNK_SIZE,
        chunk_overlap=settings.CHROMA_CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(text)
    logger.info("文档 %s 拆分为 %d 个片段", path.name, len(chunks))
    if not chunks:
        raise BusinessException(message="资料分块后没有可入库的文字", code=400)

    # 构建元数据和 ID
    # 元数据作用：后续可按 scope 筛选知识库内容，按 doc_id 删除/更新
    metadata = {"source": source, "scope": "kb", "doc_id": str(doc_id)}
    metadatas = [metadata.copy() for _ in chunks]  # 每个片段共享同一份元数据
    ids = [f"doc-{doc_id}-chunk-{index}" for index in range(len(chunks))]  # 唯一ID

    # 片段入库
    try:
        store = get_vectorstore()
        # 长资料分批写入，避免一次把所有片段交给模型或 Chroma。
        for offset in range(0, len(chunks), 32):
            store.add_texts(
                texts=chunks[offset : offset + 32],
                metadatas=metadatas[offset : offset + 32],
                ids=ids[offset : offset + 32],
            )
    except BusinessException:
        raise
    except Exception as exc:
        logger.exception("文档向量入库失败，doc_id=%s", doc_id)
        raise BusinessException(
            message="向量入库失败，请检查 Embedding 配置及后端日志", code=500
        ) from exc


def search_docs(query: str) -> dict:
    """检索最相近的3个片段，区分服务失败与没有可用的片段"""
    question = query.strip()
    if not question:
        return {"ok": False, "error": "检索问题不能为空", "items": []}

    try:
        # 问题向量与资料向量使用同一模型，最多取三个相近片段供模型判断依据。
        documents = get_vectorstore().similarity_search(question, k=3)
    except BusinessException as exc:
        return {"ok": False, "error": exc.message, "items": []}
    except Exception:
        logger.exception("检索课程资料失败")
        return {"ok": False, "error": "资料检索服务异常，请查看后端日志", "items": []}

    items = [
        {
            "content": document.page_content.strip(),
            "source": (document.metadata or {}).get("source", "未知来源"),
        }
        for document in documents
        if document.page_content.strip()
    ]
    # 请求成功但无可用正文，区别于前面捕获的配置或服务故障。
    if not items:
        return {"ok": True, "items": [], "message": "没有检索到资料片段"}
    return {"ok": True, "items": items}
