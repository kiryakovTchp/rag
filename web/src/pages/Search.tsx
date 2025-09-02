import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Search as SearchIcon, 
  FileText, 
  BookOpen,
  Filter,
  TrendingUp,

  Star
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
import { useAuth } from '@/hooks/useAuth.tsx'
import { apiService } from '@/services/api'
import { SearchQuery, SearchResult } from '@/types'

export function SearchPage() {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searchPerformed, setSearchPerformed] = useState(false)
  
  // Search options
  const [topK, setTopK] = useState(5)
  const [rerank, setRerank] = useState(true)
  const [bm25, setBm25] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return

    try {
      setLoading(true)
      setSearchPerformed(true)
      
      const searchQuery: SearchQuery = {
        question: query.trim(),
        top_k: topK,
        rerank,
        bm25,
        tenant_id: user?.tenant_id
      }

      const response = await apiService.search(searchQuery)
      setResults(response.matches)
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1)
  }

  const getScoreColor = (score: number) => {
    if (score > 0.8) return 'text-success-600'
    if (score > 0.6) return 'text-warning-600'
    return 'text-error-600'
  }

  const getScoreBadge = (score: number) => {
    if (score > 0.8) return <Badge variant="success">Высокое</Badge>
    if (score > 0.6) return <Badge variant="warning">Среднее</Badge>
    return <Badge variant="error">Низкое</Badge>
  }

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Поиск по документам
          </h1>
          <p className="text-muted-600 max-w-2xl mx-auto">
            Задайте вопрос и получите ответы с цитатами из ваших документов. 
            Используйте AI для быстрого поиска нужной информации.
          </p>
        </div>

        {/* Search Interface */}
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle>Поисковый запрос</CardTitle>
            <CardDescription>
              Опишите, что вы ищете, как можно подробнее
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col space-y-4">
              <div className="relative">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-500" />
                <Input
                  placeholder="Например: Какие SLA на этапе Контент? Или: Как происходит процесс согласования документов?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="pl-10 text-lg py-4"
                  disabled={loading}
                />
              </div>
              
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <label className="text-muted-600">Результатов:</label>
                  <select
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="px-2 py-1 border border-border rounded bg-background text-sm"
                  >
                    <option value={3}>3</option>
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                  </select>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="rerank"
                    checked={rerank}
                    onChange={(e) => setRerank(e.target.checked)}
                    className="rounded border-border"
                  />
                  <label htmlFor="rerank" className="text-muted-600">
                    Rerank результаты
                  </label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="bm25"
                    checked={bm25}
                    onChange={(e) => setBm25(e.target.checked)}
                    className="rounded border-border"
                  />
                  <label htmlFor="bm25" className="text-muted-600">
                    BM25 поиск
                  </label>
                </div>
              </div>
              
              <Button 
                onClick={handleSearch} 
                disabled={!query.trim() || loading}
                loading={loading}
                size="lg"
                className="w-full sm:w-auto"
              >
                <SearchIcon className="h-5 w-5 mr-2" />
                {loading ? 'Поиск...' : 'Найти'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Search Results */}
        {searchPerformed && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>
                      Результаты поиска
                      {results.length > 0 && (
                        <span className="ml-2 text-sm font-normal text-muted-600">
                          ({results.length} результатов)
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription>
                      {results.length > 0 
                        ? 'Найденные фрагменты документов с релевантностью'
                        : 'По вашему запросу ничего не найдено'
                      }
                    </CardDescription>
                  </div>
                  
                  {results.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <Button variant="outline" size="sm">
                        <Filter className="h-4 w-4 mr-2" />
                        Фильтры
                      </Button>
                      <Button variant="outline" size="sm">
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Анализ
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                {loading ? (
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="animate-pulse">
                        <div className="h-4 bg-muted-100 rounded w-1/4 mb-2" />
                        <div className="h-20 bg-muted-100 rounded" />
                      </div>
                    ))}
                  </div>
                ) : results.length > 0 ? (
                  <div className="space-y-6">
                    {results.map((result, index) => (
                      <motion.div
                        key={`${result.doc_id}-${result.chunk_id}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                      >
                        <div className="p-4 border border-border rounded-lg hover:bg-muted-50 transition-colors">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className="p-2 rounded-lg bg-primary-50">
                                <FileText className="h-4 w-4 text-primary-600" />
                              </div>
                              <div>
                                <h4 className="font-medium text-foreground">
                                  Документ {result.doc_id}
                                </h4>
                                {result.page && (
                                  <p className="text-sm text-muted-600">
                                    Страница {result.page}
                                  </p>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <div className="text-right">
                                <div className={`text-sm font-medium ${getScoreColor(result.score)}`}>
                                  {formatScore(result.score)}%
                                </div>
                                {getScoreBadge(result.score)}
                              </div>
                            </div>
                          </div>
                          
                          <div className="mb-3">
                            <p className="text-foreground leading-relaxed">
                              {result.snippet}
                            </p>
                          </div>
                          
                          <div className="flex items-center justify-between text-sm text-muted-600">
                            <div className="flex items-center space-x-4">
                              {result.source && (
                                <span className="flex items-center">
                                  <BookOpen className="h-3 w-3 mr-1" />
                                  {result.source}
                                </span>
                              )}
                              {result.breadcrumbs && result.breadcrumbs.length > 0 && (
                                <span className="flex items-center">
                                  <Filter className="h-3 w-3 mr-1" />
                                  {result.breadcrumbs.join(' > ')}
                                </span>
                              )}
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm">
                                <Star className="h-4 w-4 mr-1" />
                                Сохранить
                              </Button>
                              <Button variant="ghost" size="sm">
                                <FileText className="h-4 w-4 mr-1" />
                                Открыть
                              </Button>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <SearchIcon className="h-16 w-16 text-muted-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                      Ничего не найдено
                    </h3>
                    <p className="text-muted-600 mb-4">
                      Попробуйте переформулировать запрос или использовать другие ключевые слова
                    </p>
                    <div className="space-y-2 text-sm text-muted-500">
                      <p>💡 Совет: Используйте конкретные термины из ваших документов</p>
                      <p>💡 Совет: Попробуйте задать вопрос по-другому</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Search Tips */}
        {!searchPerformed && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>💡 Советы по поиску</CardTitle>
                <CardDescription>
                  Как получить лучшие результаты от AI-поиска
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <h4 className="font-medium text-foreground">✅ Что работает хорошо:</h4>
                    <ul className="space-y-2 text-sm text-muted-600">
                      <li>• Конкретные вопросы с контекстом</li>
                      <li>• Использование терминов из документов</li>
                      <li>• Вопросы о процессах и процедурах</li>
                      <li>• Поиск по датам и временным рамкам</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium text-foreground">❌ Что лучше избегать:</h4>
                    <ul className="space-y-2 text-sm text-muted-600">
                      <li>• Слишком общие вопросы</li>
                      <li>• Вопросы без контекста</li>
                      <li>• Поиск по абстрактным понятиям</li>
                      <li>• Очень длинные запросы</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </AppShell>
  )
}
