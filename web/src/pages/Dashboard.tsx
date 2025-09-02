import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  FileText, 
  Search, 
  Clock, 
  TrendingUp, 
  Upload,
  Plus,

  Users
} from 'lucide-react'
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription,
  Button,
  Badge
} from '@/components/ui'
import { AppShell } from '@/components/AppShell'
import { useAuth } from '@/contexts/AuthContext'
import { apiService } from '@/services/api'
import { Document, Job, Usage } from '@/types'

export function Dashboard() {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [usage, setUsage] = useState<Usage | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true)
        
        // Load documents, jobs, and usage in parallel
        const [docsData, jobsData, usageData] = await Promise.allSettled([
          apiService.getDocuments(),
          apiService.getJobs(),
          apiService.getUsage()
        ])

        if (docsData.status === 'fulfilled') {
          setDocuments(docsData.value)
        }

        if (jobsData.status === 'fulfilled') {
          setJobs(jobsData.value)
        }

        if (usageData.status === 'fulfilled') {
          setUsage(usageData.value)
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  const activeJobs = jobs.filter(job => job.status === 'running')
  const recentDocuments = documents.slice(0, 5)
  const completedJobs = jobs.filter(job => job.status === 'done').slice(0, 5)

  const stats = [
    {
      title: 'Всего документов',
      value: documents.length,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Активные задачи',
      value: activeJobs.length,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      title: 'Запросов сегодня',
      value: usage?.queries.total || 0,
      icon: Search,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Использовано места',
      value: usage ? `${Math.round((usage.storage.used / usage.storage.limit) * 100)}%` : '0%',
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ]

  if (loading) {
    return (
      <AppShell>
        <div className="space-y-6">
          <div className="grid gap-6 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-muted-100 rounded-lg animate-pulse" />
            ))}
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-64 bg-muted-100 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Добро пожаловать, {user?.name || 'пользователь'}! 👋
          </h1>
          <p className="text-muted-600">
            Обзор вашей активности и статистика использования
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-600">{stat.title}</p>
                      <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                    </div>
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <stat.icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Recent Documents */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Недавние документы</CardTitle>
                  <CardDescription>Последние загруженные файлы</CardDescription>
                </div>
                <Button variant="outline" size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Загрузить
                </Button>
              </CardHeader>
              <CardContent>
                {recentDocuments.length > 0 ? (
                  <div className="space-y-3">
                    {recentDocuments.map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg border">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 rounded-lg bg-muted-100">
                            <FileText className="h-4 w-4 text-muted-600" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{doc.name}</p>
                            <p className="text-xs text-muted-600">
                              {new Date(doc.created_at).toLocaleDateString('ru-RU')}
                            </p>
                          </div>
                        </div>
                        <Badge 
                          variant={doc.status === 'parse_done' ? 'success' : 
                                  doc.status === 'failed' ? 'error' : 'warning'}
                        >
                          {doc.status === 'parse_done' ? 'Готов' : 
                           doc.status === 'failed' ? 'Ошибка' : 'Обработка'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-muted-400 mx-auto mb-4" />
                    <p className="text-muted-600 mb-4">У вас пока нет документов</p>
                    <Button>
                      <Upload className="h-4 w-4 mr-2" />
                      Загрузить первый документ
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Jobs */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Последние задачи</CardTitle>
                <CardDescription>Статус обработки документов</CardDescription>
              </CardHeader>
              <CardContent>
                {completedJobs.length > 0 ? (
                  <div className="space-y-3">
                    {completedJobs.map((job) => (
                      <div key={job.id} className="flex items-center justify-between p-3 rounded-lg border">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 rounded-lg bg-muted-100">
                            <Clock className="h-4 w-4 text-muted-600" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{job.kind}</p>
                            <p className="text-xs text-muted-600">
                              {new Date(job.created_at).toLocaleDateString('ru-RU')}
                            </p>
                          </div>
                        </div>
                        <Badge variant="success">Завершено</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Clock className="h-12 w-12 text-muted-400 mx-auto mb-4" />
                    <p className="text-muted-600">Нет завершенных задач</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Быстрые действия</CardTitle>
              <CardDescription>Что хотите сделать?</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <Button className="h-20 flex-col space-y-2">
                  <Upload className="h-6 w-6" />
                  <span>Загрузить документ</span>
                </Button>
                <Button variant="outline" className="h-20 flex-col space-y-2">
                  <Search className="h-6 w-6" />
                  <span>Поиск по документам</span>
                </Button>
                <Button variant="outline" className="h-20 flex-col space-y-2">
                  <Users className="h-6 w-6" />
                  <span>Пригласить команду</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </AppShell>
  )
}
