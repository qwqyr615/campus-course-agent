import request from '@/utils/request'

export function listDocumentsApi() {
  return request({ url: '/api/documents', method: 'get' })
}

export function uploadDocumentsApi(files) {
  const data = new FormData()
  for (const file of files) {
    data.append('files', file)
  }
  return request({ url: '/api/documents', method: 'post', data })
}

export function previewDocumentApi(id) {
  return request({ url: `/api/documents/${id}/preview`, method: 'get' })
}

export function deleteDocumentApi(id) {
  return request({ url: `/api/documents/${id}`, method: 'delete', timeout: 0 })
}

export function reingestDocumentApi(id) {
  return request({ url: `/api/documents/${id}/reingest`, method: 'post', timeout: 0 })
}
