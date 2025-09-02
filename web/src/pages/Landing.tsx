import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  ArrowRight, 
  Check, 
  Crown, 
  Sparkles, 
  Users, 
  Shield, 
  Search
} from 'lucide-react'
import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription,
  Badge,
  IconChip
} from '@/components/ui'

function Container({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-[1140px] px-4 sm:px-6 lg:px-8">{children}</div>
}

function Section({ id, className = "", children }: { id?: string; className?: string; children: React.ReactNode }) {
  return (
    <section id={id} className={`py-16 md:py-20 ${className}`}>
      <Container>{children}</Container>
    </section>
  )
}

function MetricsStrip() {
  const items = [
    { big: "×12", text: "быстрее поиск ответов" },
    { big: "–85%", text: "ручных проверок" },
    { big: "5 мин", text: "до первого ответа с цитатами" },
  ]
  
  return (
    <Card>
      <CardContent className="p-4 sm:p-5">
        <div className="grid grid-cols-3 divide-x rounded-xl">
          {items.map((it, i) => (
            <div key={i} className="flex items-center justify-center px-3 text-center">
              <div>
                <div className="text-3xl font-semibold tracking-tight">{it.big}</div>
                <div className="mt-1 text-sm text-muted-600 leading-snug">{it.text}</div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function ChatMock() {
  const dot = (d = 0) => ({ 
    initial: { opacity: 0.2 }, 
    animate: { opacity: [0.2, 1, 0.2] }, 
    transition: { duration: 1.2, repeat: Infinity as any, delay: d } 
  })
  
  return (
    <Card className="mx-auto w-full max-w-md">
      <CardContent className="p-4">
        <div className="mb-3 flex gap-1">
          <span className="size-2 rounded-full bg-muted-300" />
          <span className="size-2 rounded-full bg-muted-300" />
          <span className="size-2 rounded-full bg-muted-300" />
        </div>
        <div className="space-y-3">
          <div className="ml-auto w-3/4 rounded-xl bg-muted-100 px-3 py-2 text-xs">
            Какие SLA на этапе Контент?
          </div>
          <div className="w-[82%] rounded-xl border bg-white px-3 py-2 text-xs">
            На этапе «Контент» — 3 рабочих дня. Просрочка подсвечивается в списке задач.
            <div className="mt-2 flex gap-2 text-[10px] text-muted-600">
              <span className="rounded-full border px-2 py-0.5">Promo Process</span>
              <span className="rounded-full border px-2 py-0.5">Asana</span>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-1 pr-1">
            <motion.span className="size-1.5 rounded-full bg-primary-500" {...dot(0)} />
            <motion.span className="size-1.5 rounded-full bg-primary-500" {...dot(0.2)} />
            <motion.span className="size-1.5 rounded-full bg-primary-500" {...dot(0.4)} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function FunnelShowcase() {
  const fly = (dx: number, delay: number) => ({ 
    initial: { x: 0, opacity: 0 }, 
    animate: { x: dx, opacity: 1 }, 
    transition: { duration: 2, ease: "easeInOut", delay, repeat: Infinity as any, repeatDelay: 0.6 } 
  })
  const pulse = (delay = 0) => ({ 
    initial: { opacity: 0 }, 
    animate: { opacity: [0, 1, 0] }, 
    transition: { duration: 1.6, repeat: Infinity as any, delay } 
  })
  
  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Как это работает</CardTitle>
        <CardDescription>Загрузил документы → получил проверяемый ответ</CardDescription>
      </CardHeader>
      <CardContent>
        <motion.svg viewBox="0 0 740 220" className="h-56 w-full">
          <g>
            <rect x="24" y="28" width="120" height="38" rx="10" className="fill-background stroke-border" />
            <rect x="24" y="78" width="120" height="38" rx="10" className="fill-background stroke-border" />
            <rect x="24" y="128" width="120" height="38" rx="10" className="fill-background stroke-border" />
            <text x="84" y="52" textAnchor="middle" className="fill-foreground text-[12px]">PDF</text>
            <text x="84" y="102" textAnchor="middle" className="fill-foreground text-[12px]">DOCX</text>
            <text x="84" y="152" textAnchor="middle" className="fill-foreground text-[12px]">XLSX</text>
          </g>
          <g>
            <path d="M180 46 H 330" className="stroke-border" />
            <path d="M180 96 H 330" className="stroke-border" />
            <path d="M180 146 H 330" className="stroke-border" />
            <rect x="330" y="36" width="160" height="132" rx="12" className="fill-muted-50 stroke-border" />
            <text x="410" y="60" textAnchor="middle" className="fill-foreground text-[12px]">Индекс</text>
            <rect x="350" y="76" width="120" height="22" rx="6" className="fill-background stroke-border" />
            <rect x="350" y="106" width="120" height="22" rx="6" className="fill-background stroke-border" />
            <rect x="350" y="136" width="120" height="22" rx="6" className="fill-background stroke-border" />
          </g>
          {[0, 0.25, 0.5].map((d, i) => (
            <motion.rect key={i} x={24} y={36 + i * 50} width={20} height={14} rx={4} className="fill-foreground/10" {...fly(306, d)} />
          ))}
          <path d="M490 102 H 600" className="stroke-border" />
          <g>
            <rect x="600" y="72" width="120" height="70" rx="12" className="fill-background stroke-border" />
            <motion.circle cx="626" cy="107" r="3.5" className="fill-foreground" {...pulse(0)} />
            <motion.circle cx="644" cy="107" r="3.5" className="fill-foreground" {...pulse(0.2)} />
            <motion.circle cx="662" cy="107" r="3.5" className="fill-foreground" {...pulse(0.4)} />
            <text x="660" y="150" textAnchor="middle" className="fill-foreground text-[12px]">Ответ с цитатами</text>
          </g>
        </motion.svg>
      </CardContent>
    </Card>
  )
}

function PersonaCard({ icon, who, pain, gain }: { icon: React.ReactNode; who: string; pain: string; gain: string }) {
  return (
    <Card className="h-full">
      <CardContent className="p-6">
        <div className="mb-3 flex items-center gap-3">
          <IconChip>{icon}</IconChip>
          <h4 className="text-base font-semibold">{who}</h4>
        </div>
        <div className="grid gap-2 text-sm">
          <div><span className="text-muted-600">Боль:</span> {pain}</div>
          <div><span className="text-muted-600">Результат:</span> {gain}</div>
        </div>
      </CardContent>
    </Card>
  )
}

function PriceCard({ title, price, per = "/мес", cta, popular, features }: { title: string; price: string; per?: string; cta: string; popular?: boolean; features: string[] }) {
  const inner = (
    <Card className={`h-full ${popular ? "border-primary-900 shadow-lg" : ""}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{title}</CardTitle>
          {popular && (
            <Badge className="gap-1">
              <Crown className="h-3.5 w-3.5" /> Рекомендуем
            </Badge>
          )}
        </div>
        <CardDescription>Простые и честные лимиты</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-3xl font-semibold tracking-tight">
          {price}<span className="ml-1 text-base font-normal text-muted-600">{per}</span>
        </div>
        <ul className="space-y-2 text-sm">
          {features.map((f, i) => (
            <li key={i} className="flex items-start gap-2">
              <Check className="mt-0.5 h-4 w-4 text-success-600" /> {f}
            </li>
          ))}
        </ul>
        <Button className="w-full">{cta}</Button>
      </CardContent>
    </Card>
  )
  
  return popular ? (
    <div className="rounded-[14px] bg-gradient-to-r from-primary-900/12 to-primary-900/6 p-[1px]">
      {inner}
    </div>
  ) : inner
}

export function Landing() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-50 border-b bg-white/70 backdrop-blur">
        <Container>
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="grid h-8 w-8 place-items-center rounded-xl bg-primary-900 text-white font-bold">
                P
              </div>
              <span className="text-sm font-medium text-muted-600">PromoAI · RAG</span>
            </div>
            <nav className="hidden items-center gap-6 md:flex">
              <a href="#flow" className="text-sm text-muted-600 hover:text-primary-900">Как работает</a>
              <a href="#personas" className="text-sm text-muted-600 hover:text-primary-900">Кому</a>
              <a href="#pricing" className="text-sm text-muted-600 hover:text-primary-900">Цены</a>
              <a href="#faq" className="text-sm text-muted-600 hover:text-primary-900">FAQ</a>
            </nav>
            <div className="flex items-center gap-2">
              <Link to="/login">
                <Button variant="ghost" className="hidden sm:inline-flex">Войти</Button>
              </Link>
              <Link to="/register">
                <Button className="gap-1">Регистрация <ArrowRight className="h-4 w-4" /></Button>
              </Link>
            </div>
          </div>
        </Container>
      </header>

      <Section id="hero" className="pb-10 pt-14 md:pt-20">
        <div className="grid items-start gap-10 md:grid-cols-2">
          <div className="space-y-6">
            <div className="relative">
              <motion.h1 
                initial={{ opacity: 0, y: 8 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.5 }} 
                className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl md:text-6xl"
              >
                Документ‑QA RAG, который приносит ответы, а не фантазии
              </motion.h1>
              <div className="pointer-events-none absolute -bottom-2 left-0 h-[6px] w-40 rounded-full bg-gradient-to-r from-primary-500/35 to-transparent" />
            </div>
            <motion.p 
              initial={{ opacity: 0, y: 8 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.6, delay: 0.05 }} 
              className="max-w-xl text-balance text-sm text-muted-600 sm:text-base"
            >
              Соберите разрозненные PDF и таблицы в один поиск. Ответы подкреплены цитатами из источников.
            </motion.p>
            <div className="flex flex-wrap items-center gap-3">
              <Link to="/register">
                <Button size="lg" className="gap-2">
                  Попробовать бесплатно <Sparkles className="h-4 w-4" />
                </Button>
              </Link>
              <Button 
                size="lg" 
                variant="secondary" 
                onClick={() => document.getElementById("flow")?.scrollIntoView({ behavior: "smooth" })} 
                className="gap-2"
              >
                Как работает <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
            <MetricsStrip />
          </div>
          <ChatMock />
        </div>
      </Section>

      <Section id="flow" className="bg-muted-50/60">
        <div className="grid gap-4 md:grid-cols-2">
          <FunnelShowcase />
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="text-base">Зачем это нужно</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-600">
              <ul className="ml-4 list-disc space-y-2">
                <li>Один чат вместо охоты по папкам и Confluence</li>
                <li>Ответы с цитатами вместо догадок</li>
                <li>Быстрый поиск по тысячам страниц</li>
                <li>Автоматическое обновление при изменении документов</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </Section>

      <Section id="personas">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-semibold mb-4">Кому подходит</h2>
          <p className="text-muted-600 max-w-2xl mx-auto">
            Решаем реальные проблемы команд, которые работают с большими объемами документации
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <PersonaCard 
            icon={<Users className="h-5 w-5" />}
            who="Менеджеры проектов"
            pain="Теряют время на поиск информации в разрозненных документах"
            gain="Быстрые ответы на вопросы по проекту с указанием источников"
          />
          <PersonaCard 
            icon={<Search className="h-5 w-5" />}
            who="Аналитики"
            pain="Не могут быстро найти нужные данные в отчетах и таблицах"
            gain="Мгновенный поиск по всем документам с контекстом"
          />
          <PersonaCard 
            icon={<Shield className="h-5 w-5" />}
            who="Юристы и Compliance"
            pain="Тратят часы на изучение нормативных документов"
            gain="Точные ответы с ссылками на конкретные пункты"
          />
        </div>
      </Section>

      <Section id="pricing" className="bg-muted-50/60">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-semibold mb-4">Простые цены</h2>
          <p className="text-muted-600 max-w-2xl mx-auto">
            Без скрытых комиссий и сложных тарифов. Платите только за то, что используете.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <PriceCard
            title="Старт"
            price="0₽"
            per=""
            cta="Начать бесплатно"
            features={[
              "100 запросов в месяц",
              "5 документов",
              "Базовая поддержка",
              "API доступ"
            ]}
          />
          <PriceCard
            title="Команда"
            price="9,900₽"
            popular
            cta="Попробовать команду"
            features={[
              "10,000 запросов в месяц",
              "100 документов",
              "Приоритетная поддержка",
              "Расширенная аналитика",
              "Командные настройки"
            ]}
          />
          <PriceCard
            title="Корпорация"
            price="29,900₽"
            cta="Связаться с продажами"
            features={[
              "Неограниченные запросы",
              "Неограниченные документы",
              "24/7 поддержка",
              "Индивидуальная настройка",
              "SLA гарантии"
            ]}
          />
        </div>
      </Section>

      <Section id="faq">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-semibold mb-4">Частые вопросы</h2>
          <p className="text-muted-600 max-w-2xl mx-auto">
            Ответы на самые популярные вопросы о нашей платформе
          </p>
        </div>
        <div className="grid gap-6 max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Какие форматы документов поддерживаются?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-600">
                Поддерживаем все популярные форматы: PDF, DOCX, XLSX, PPTX, TXT, HTML. 
                Также работаем с изображениями через OCR.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Как обеспечивается безопасность данных?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-600">
                Все данные шифруются в состоянии покоя и при передаче. 
                Поддерживаем SSO, 2FA и соответствие GDPR.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Можно ли интегрировать с нашими системами?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-600">
                Да, предоставляем REST API, Webhooks и готовые интеграции 
                с популярными платформами: Slack, Teams, Notion.
              </p>
            </CardContent>
          </Card>
        </div>
      </Section>

      <Section className="bg-primary-900 text-white">
        <div className="text-center">
          <h2 className="text-3xl font-semibold mb-4">Готовы начать?</h2>
          <p className="text-primary-100 mb-8 max-w-2xl mx-auto">
            Присоединяйтесь к тысячам команд, которые уже используют PromoAI для быстрого поиска по документам
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/register">
              <Button size="lg" variant="secondary">
                Начать бесплатно
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-primary-900">
                Войти в систему
              </Button>
            </Link>
          </div>
        </div>
      </Section>
    </div>
  )
}
