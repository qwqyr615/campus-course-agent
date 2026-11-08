<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">文档管理</div>
      </template>

      <div v-if="isAdmin" style="margin-bottom: 12px">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :disabled="uploadLoading"
          :show-file-list="true"
          multiple
          accept=".txt,.md,.pdf,.docx,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
        >
          <el-button type="primary" :disabled="uploadLoading">选择文件</el-button>
        </el-upload>
        <el-button
          style="margin-top: 8px"
          type="success"
          :loading="uploadLoading"
          :disabled="!pendingFiles.length"
          @click="handleUpload"
        >
          上传资料
        </el-button>
        <div style="margin-top: 6px; color: #909399; font-size: 12px">
          支持 .txt / .md / .pdf / .docx，单个文件不超过 100 MiB。同名不可重复；扫描版 PDF
          可能抽不出文字。 同一批中任一文件上传或入库失败，整批撤销。
        </div>
      </div>
      <div v-else style="margin-bottom: 12px; color: #909399; font-size: 13px">
        仅管理员可管理知识库文档。
      </div>

      <el-table
        v-loading="loading"
        :data="pageData"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
      >
        <el-table-column
          prop="original_name"
          label="文件名"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="ext" label="类型" width="80" />
        <el-table-column prop="ingested" label="已入库" width="90">
          <template #default="{ row }">
            <el-tag :type="row.ingested ? 'success' : 'info'" size="small">
              {{ row.ingested ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column v-if="isAdmin" label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text bg size="small" @click="handlePreview(row)">
              预览
            </el-button>
            <el-button
              type="primary"
              text
              bg
              size="small"
              :loading="reingestLoadingId === row.id"
              @click="handleReingest(row)"
            >
              重新入库
            </el-button>
            <el-button type="danger" text bg size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 10px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          background
          layout="total, prev, pager, next"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      width="720px"
      destroy-on-close
      append-to-body
    >
      <div class="preview-meta" v-if="previewMeta">{{ previewMeta }}</div>
      <div v-loading="previewLoading" class="preview-body">
        <pre v-if="previewText" class="preview-text">{{ previewText }}</pre>
        <div v-else-if="!previewLoading" style="color: #909399">暂无文本</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteDocumentApi,
  listDocumentsApi,
  previewDocumentApi,
  uploadDocumentsApi
} from '@/api/document'
import { useUser } from '@/utils/user'

const { userInfo } = useUser()
const isAdmin = computed(() => userInfo.value?.role === 'admin')
const loading = ref(false)
const allData = ref([])
const page = ref(1)
const pageSize = ref(10)
const pendingFiles = ref([])
const uploadLoading = ref(false)
const uploadRef = ref()
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewTitle = ref('文档预览')
const previewMeta = ref('')
const previewText = ref('')
const reingestLoadingId = ref(null) // 正在重新入库的文档 ID，控制对应按钮的加载状态
let previewRequestId = 0 // 标记最近一次预览，防止旧请求覆盖新资料
const total = computed(() => allData.value.length)
const pageData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return allData.value.slice(start, start + pageSize.value)
})

const load = async () => {
  loading.value = true
  try {
    const res = await listDocumentsApi()
    // 业务错误仍可能 resolve，只在 code=200 时更新列表。
    if (res.code === 200) {
      allData.value = res.data
      const maxPage = Math.max(1, Math.ceil(res.data.length / pageSize.value))
      page.value = Math.min(page.value, maxPage)
    }
  } catch {
    // 网络和 HTTP 错误已由请求拦截器提示。
  } finally {
    loading.value = false
  }
}

const onFileChange = (_file, fileList) => {
  pendingFiles.value = fileList.map((file) => file.raw)
}
const onFileRemove = (_file, fileList) => {
  pendingFiles.value = fileList.map((file) => file.raw)
}

const handleUpload = async () => {
  // 没有文件时不发请求，上传中也不重复提交。
  if (!pendingFiles.value.length || uploadLoading.value) return
  uploadLoading.value = true
  try {
    const res = await uploadDocumentsApi(pendingFiles.value)
    // 整批成功才清空选择；失败时保留，便于移除错误文件后重试。
    if (res.code === 200) {
      ElMessage.success('上传成功')
      pendingFiles.value = []
      uploadRef.value.clearFiles()
      page.value = 1
      await load()
    }
  } catch {
    // 错误已提示，保留待上传文件。
  } finally {
    uploadLoading.value = false
  }
}

const handlePreview = async (row) => {
  const requestId = ++previewRequestId
  previewTitle.value = `预览：${row.original_name}`
  previewMeta.value = ''
  previewText.value = ''
  previewVisible.value = true
  previewLoading.value = true
  try {
    const res = await previewDocumentApi(row.id)
    // 用户已打开另一份资料时，忽略这次较晚返回的旧结果。
    if (requestId !== previewRequestId) return
    // 解析失败时显示当前文件的失败状态，不保留上一份资料的文字。
    if (res.code === 200) {
      previewText.value = res.data.text
      previewMeta.value = `已抽取纯文本，共 ${res.data.char_count} 个字符`
    } else {
      previewMeta.value = '无法预览，请根据错误提示检查文件。'
    }
  } catch {
    if (requestId === previewRequestId) {
      previewMeta.value = '预览请求失败，请稍后重试。'
    }
  } finally {
    if (requestId === previewRequestId) previewLoading.value = false
  }
}

const handleReingest = async (row) => {
  // 已有一份资料在入库时，不重复发起新的入库请求。
  if (reingestLoadingId.value !== null) return
  reingestLoadingId.value = row.id
  try {
    const res = await reingestDocumentApi(row.id)
    if (res.code === 200) {
      ElMessage.success(`「${row.original_name}」已重新入库`)
    }
  } catch {
    // 请求拦截器已提示网络或 HTTP 错误。
  } finally {
    reingestLoadingId.value = null
    // 失败时原文件仍在，但状态可能由“是”变成“否”，因此也刷新列表。
    await load()
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除文档「${row.original_name}」及其原文件和向量片段？`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    // 取消或关闭确认框时，不调用删除接口。
    return
  }
  try {
    const res = await deleteDocumentApi(row.id)
    if (res.code === 200) ElMessage.success('已删除')
  } catch {
    // 错误已由请求拦截器提示。
  } finally {
    await load() // 删除失败也可能已清理向量，需要同步最新入库状态。
  }
}

const formatSize = (n) => {
  // 按文件大小选择显示单位；以 1024 为换算基数。
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}
const formatTime = (value) => String(value).replace('T', ' ').slice(0, 19)

onMounted(() => {
  // 学生直接输入地址时不加载资料，后端仍会检查每个接口的权限。
  if (isAdmin.value) load()
})
</script>

<style scoped>
.preview-meta {
  margin-bottom: 10px;
  color: #909399;
  font-size: 13px;
}
.preview-body {
  min-height: 120px;
}
.preview-text {
  margin: 0;
  max-height: 60vh;
  overflow: auto;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.6;
  color: #303133;
  font-family: ui-monospace, Consolas, 'Courier New', monospace;
}
</style>
