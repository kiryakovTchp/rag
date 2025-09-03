import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  FileText, 
  Upload, 
  Search, 
  Download,
  Eye,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription,
  Button,
  Badge,
  Input,

} from '@/components/ui'
import { AppShell } from '@/components/AppShell'

import apiClient from '@/services/apiClient'
import { Document } from '@/types'

export function Documents() {

  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
              const docs = await apiClient.get('/documents').then(res => res.data)
      setDocuments(docs)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('file', selectedFile)
      
              const result = await apiClient.post('/ingest', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }).then(res => res.data)
      
      // Add new document to list
      setDocuments(prev => [result.document, ...prev])
      setSelectedFile(null)
      
      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'parse_done':
        return <CheckCircle className="h-4 w-4 text-success-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-error-600" />
      default:
        return <Clock className="h-4 w-4 text-warning-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'parse_done':
        return <Badge variant="success">Готов</Badge>
      case 'failed':
        return <Badge variant="error">Ошибка</Badge>
      default:
        return <Badge variant="warning">Обработка</Badge>
    }
  }

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (loading) {
    return (
      <AppShell>
        <div className="space-y-6">
          <div className="h-8 bg-muted-100 rounded-lg animate-pulse" />
          <div className="grid gap-6 md:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-muted-100 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Документы</h1>
            <p className="text-muted-600">
              Управляйте загруженными документами и отслеживайте их обработку
            </p>
          </div>
          <Button size="lg">
            <Upload className="h-4 w-4 mr-2" />
            Загрузить документ
          </Button>
        </div>

        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Загрузка нового документа</CardTitle>
            <CardDescription>
              Поддерживаемые форматы: PDF, DOCX, XLSX, PPTX, TXT, HTML
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <Input
                  id="file-upload"
                  type="file"
                  onChange={handleFileSelect}
                  accept=".pdf,.docx,.xlsx,.pptx,.txt,.html"
                  disabled={uploading}
                />
              </div>
              <Button 
                onClick={handleUpload} 
                disabled={!selectedFile || uploading}
                loading={uploading}
              >
                {uploading ? 'Загрузка...' : 'Загрузить'}
              </Button>
            </div>
            {selectedFile && (
              <div className="mt-3 p-3 bg-muted-50 rounded-lg">
                <p className="text-sm text-muted-600">
                  Выбран файл: <span className="font-medium">{selectedFile.name}</span>
                  {' '}({formatFileSize(selectedFile.size)})
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-500" />
              <Input
                placeholder="Поиск по названию документа..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            >
              <option value="all">Все статусы</option>
              <option value="parse_started">Обработка</option>
              <option value="parse_done">Готов</option>
              <option value="failed">Ошибка</option>
            </select>
          </div>
        </div>

        {/* Documents Grid */}
        {filteredDocuments.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredDocuments.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="h-full hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-muted-100">
                          <FileText className="h-5 w-5 text-muted-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-base truncate">{doc.name}</CardTitle>
                          <CardDescription className="text-xs">
                            {formatFileSize(doc.size)}
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(doc.status)}
                        {getStatusBadge(doc.status)}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-600">Загружен:</span>
                        <span>{new Date(doc.created_at).toLocaleDateString('ru-RU')}</span>
                      </div>
                      
                      {doc.pages && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-600">Страниц:</span>
                          <span>{doc.pages}</span>
                        </div>
                      )}
                      
                      {doc.chunks && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-600">Чанков:</span>
                          <span>{doc.chunks}</span>
                        </div>
                      )}

                      <div className="flex items-center justify-between">
                        <Button variant="outline" size="sm" className="flex-1 mr-2">
                          <Eye className="h-4 w-4 mr-1" />
                          Просмотр
                        </Button>
                        <Button variant="outline" size="sm" className="flex-1">
                          <Download className="h-4 w-4 mr-1" />
                          Скачать
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <FileText className="h-16 w-16 text-muted-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                {searchTerm || statusFilter !== 'all' ? 'Документы не найдены' : 'Нет документов'}
              </h3>
              <p className="text-muted-600 mb-4">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Попробуйте изменить параметры поиска'
                  : 'Загрузите свой первый документ для начала работы'
                }
              </p>
              {!searchTerm && statusFilter === 'all' && (
                <Button>
                  <Upload className="h-4 w-4 mr-2" />
                  Загрузить документ
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  )
}
