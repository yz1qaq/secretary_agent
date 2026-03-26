import {
  ChangeEvent,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

type NavigationKey =
  | 'dashboard'
  | 'today'
  | 'next7days'
  | 'schedule'
  | 'tasks'
  | 'settings'

type MessageRole = 'assistant' | 'user'
type PriorityLevel = '高' | '中' | '低'
type DayLoad = 'High' | 'Medium' | 'Low'

const CHAT_STORAGE_KEY = 'personal-secretary-dashboard-threads'
const API_BASE_URL = (
  import.meta.env.VITE_SECRETARY_API_URL || 'http://127.0.0.1:9826'
).replace(/\/$/, '')
const CHAT_BACKEND_MODE = import.meta.env.VITE_SECRETARY_CHAT_MODE || 'legacy'
const USE_MODERN_CHAT_API = CHAT_BACKEND_MODE === 'modern'

interface NavItemData {
  key: NavigationKey
  label: string
}

interface StatCardData {
  label: string
  value: string
  hint: string
}

interface TimelineEntry {
  time: string
  title: string
  type: '固定安排' | '建议任务'
}

interface WeekPlan {
  day: string
  focus: string
  load: DayLoad
}

interface TaskData {
  title: string
  deadline: string
  priority: PriorityLevel
}

interface PendingAttachment {
  id: string
  name: string
  type: string
  size: number
  content: string
  previewUrl?: string
  textSummary?: string
}

interface ChatAttachment {
  name: string
  type: string
  size?: number
  content?: string
  previewUrl?: string
  textSummary?: string
}

interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  createdAt: string
  attachments: ChatAttachment[]
  isStreaming?: boolean
}

interface ChatThread {
  threadId: string
  title: string
  preview: string
  isDraft: boolean
  messages: ChatMessage[]
}

interface ThreadListItemResponse {
  thread_id: string
  title?: string
  preview?: string
  updated_at?: string
}

interface ChatThreadsResponse {
  threads?: ThreadListItemResponse[]
}

interface ChatHistoryMessageResponse {
  id?: string
  role?: string
  content?: string
  created_at?: string
  attachments?: ChatAttachmentResponse[]
}

interface ChatHistoryResponse {
  thread_id?: string
  title?: string
  preview?: string
  messages?: ChatHistoryMessageResponse[]
}

interface ChatAttachmentResponse {
  name?: string
  filename?: string
  type?: string
  mime_type?: string
  size?: number
  content?: string
  url?: string
  preview_url?: string
  text_summary?: string
}

interface ChatSendPayload {
  message: string
  thread_id: string
  attachments: Array<{
    name: string
    type: string
    size: number
    content: string
  }>
}

interface ChatSendResponse {
  thread_id?: string
  title?: string
  preview?: string
  reply?: string
  message?: ChatHistoryMessageResponse
}

interface LegacyChatResponse {
  status?: string
  reply?: string
  thread_id?: string
  checkpointer?: string
}

interface StreamChunk {
  delta?: string
  reply?: string
  thread_id?: string
  title?: string
  preview?: string
  message?: ChatHistoryMessageResponse
  error?: string
}

interface CourseScheduleRow {
  academic_year?: string
  year?: string
  term?: string
  semester?: string
  weekday?: number | string
  start_time?: string
  end_time?: string
  course_name?: string
  course?: string
  location?: string
  teacher?: string
  week_text?: string
  week_range?: string
  raw_source?: string
}

interface CourseScheduleResponse {
  data?: CourseScheduleRow[]
}

interface SidebarProps {
  activeKey: NavigationKey
  items: NavItemData[]
  onChange: (key: NavigationKey) => void
}

type StatCardProps = StatCardData
type TimelineItemProps = TimelineEntry
type WeekCardProps = WeekPlan
type TaskItemProps = TaskData

const navigationItems: NavItemData[] = [
  { key: 'dashboard', label: '仪表盘' },
  { key: 'today', label: '今日' },
  { key: 'next7days', label: '未来 7 天' },
  { key: 'schedule', label: '课表' },
  { key: 'tasks', label: '任务' },
  { key: 'settings', label: '设置' },
]

const statCards: StatCardData[] = [
  { label: '今日课程', value: '1', hint: '下午 09:00 有固定课程' },
  { label: '可专注时间', value: '4.5 小时', hint: '适合安排深度工作' },
  { label: '最高优先级', value: '实验总结', hint: '建议今晚前完成初稿' },
  { label: '待处理任务', value: '6', hint: '其中 2 项为高优先级' },
]

const timelineEntries: TimelineEntry[] = [
  {
    time: '09:00 - 10:30',
    title: '课程：多模态学习',
    type: '固定安排',
  },
  {
    time: '14:00 - 16:00',
    title: '阅读论文并做笔记',
    type: '建议任务',
  },
  {
    time: '19:30 - 21:00',
    title: '整理实验结果',
    type: '建议任务',
  },
]

const weekPlans: WeekPlan[] = [
  { day: '周一', focus: '课程 + 阅读', load: 'High' },
  { day: '周二', focus: '实验推进', load: 'High' },
  { day: '周三', focus: '作业整理', load: 'Medium' },
  { day: '周四', focus: '写作输出', load: 'Medium' },
  { day: '周五', focus: '会议准备', load: 'Medium' },
  { day: '周六', focus: '深度工作', load: 'Low' },
  { day: '周日', focus: '休息 + 周计划', load: 'Low' },
]

const tasks: TaskData[] = [
  { title: '完善实验基线图表', deadline: '今天 22:00', priority: '高' },
  { title: '撰写相关工作初稿', deadline: '周三 18:00', priority: '中' },
  { title: '回复导师邮件', deadline: '今天 17:30', priority: '高' },
  { title: '准备会议讨论要点', deadline: '周五 10:00', priority: '中' },
  { title: '更新阅读清单', deadline: '本周内', priority: '低' },
]

const defaultAssistantMessages: ChatMessage[] = [
  {
    id: 'assistant-welcome',
    role: 'assistant',
    content:
      '你好，我是你的 AI 秘书。你可以直接告诉我今天想优先推进的任务，我会帮你安排。',
    createdAt: formatClock(new Date()),
    attachments: [],
  },
  {
    id: 'assistant-suggestion',
    role: 'assistant',
    content:
      '今天的秘书建议：\n1. 建议将论文阅读调整到明天下午，那里有更完整的空闲时间块。\n2. 今晚安排可以适当减轻，因为你今天已经有一节课程。\n3. 实验总结建议在明晚前完成，以免影响后续安排。',
    createdAt: formatClock(new Date()),
    attachments: [],
  },
]

function formatClock(date: Date): string {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

function formatThreadTitle(thread: ChatThread): string {
  return thread.isDraft ? `${thread.title}（未保存）` : thread.title
}

function getPriorityClasses(priority: PriorityLevel): string {
  if (priority === '高') {
    return 'bg-red-50 text-red-600 ring-1 ring-inset ring-red-200'
  }
  if (priority === '中') {
    return 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200'
  }
  return 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200'
}

function getDayLoadClasses(load: DayLoad): string {
  if (load === 'High') {
    return 'bg-red-50 text-red-600 ring-1 ring-inset ring-red-200'
  }
  if (load === 'Medium') {
    return 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200'
  }
  return 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200'
}

function getTimelineTagClasses(type: TimelineEntry['type']): string {
  return type === '固定安排'
    ? 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200'
    : 'bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-200'
}

function isImageType(type: string): boolean {
  return type.startsWith('image/')
}

function canPreviewText(type: string, name: string): boolean {
  return (
    type.startsWith('text/') ||
    type === 'application/json' ||
    name.endsWith('.md') ||
    name.endsWith('.txt')
  )
}

function createDraftThread(): ChatThread {
  return {
    threadId: crypto.randomUUID(),
    title: '草稿会话',
    preview: '当前为草稿会话，发送首条消息后会自动保存。',
    isDraft: true,
    messages: defaultAssistantMessages,
  }
}

function createInitialThreadState(): {
  threads: ChatThread[]
  activeThreadId: string
} {
  if (typeof window !== 'undefined') {
    try {
      const raw = window.localStorage.getItem(CHAT_STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as ChatThread[]
        const validThreads = parsed.filter(
          (thread) =>
            typeof thread.threadId === 'string' &&
            typeof thread.title === 'string' &&
            typeof thread.preview === 'string' &&
            typeof thread.isDraft === 'boolean' &&
            Array.isArray(thread.messages),
        )
        if (validThreads.length > 0) {
          return {
            threads: validThreads,
            activeThreadId: validThreads[0].threadId,
          }
        }
      }
    } catch {
      // 忽略本地缓存损坏，回退到默认草稿线程
    }
  }

  const draftThread = createDraftThread()
  return {
    threads: [draftThread],
    activeThreadId: draftThread.threadId,
  }
}

function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}

function isNotFoundError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false
  }
  return (
    error.message.includes('404') ||
    error.message.includes('Not Found') ||
    error.message.includes('"detail":"Not Found"')
  )
}

function normalizeAttachment(
  attachment: ChatAttachmentResponse | PendingAttachment,
): ChatAttachment {
  if ('id' in attachment) {
    return {
      name: attachment.name || '未命名附件',
      type: attachment.type || 'application/octet-stream',
      size: attachment.size,
      content: attachment.content,
      previewUrl: attachment.previewUrl,
      textSummary: attachment.textSummary,
    }
  }

  return {
    name: attachment.filename || attachment.name || '未命名附件',
    type:
      attachment.mime_type || attachment.type || 'application/octet-stream',
    size: attachment.size,
    content: attachment.content,
    previewUrl: attachment.preview_url || attachment.url,
    textSummary: attachment.text_summary,
  }
}

function normalizeMessage(message: ChatHistoryMessageResponse): ChatMessage {
  const role = message.role === 'user' ? 'user' : 'assistant'
  return {
    id: message.id || crypto.randomUUID(),
    role,
    content: message.content || '',
    createdAt: message.created_at || formatClock(new Date()),
    attachments: (message.attachments || []).map(normalizeAttachment),
  }
}

function normalizeThreadsResponse(payload: ChatThreadsResponse): ChatThread[] {
  return (payload.threads || []).map((thread) => ({
    threadId: thread.thread_id,
    title: thread.title || '未命名会话',
    preview: thread.preview || '继续和你的 AI 秘书对话',
    isDraft: false,
    messages: [],
  }))
}

function normalizeCourseScheduleResponse(
  payload: CourseScheduleResponse | CourseScheduleRow[],
): CourseScheduleRow[] {
  return Array.isArray(payload) ? payload : payload.data || []
}

function formatWeekday(weekday?: number | string): string {
  const mapping = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const numeric =
    typeof weekday === 'string' ? Number.parseInt(weekday, 10) : weekday
  if (numeric && numeric >= 1 && numeric <= 7) {
    return mapping[numeric - 1]
  }
  return '--'
}

function formatTimeRange(row: CourseScheduleRow): string {
  if (!row.start_time || !row.end_time) {
    return '--'
  }
  return `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}`
}

function formatWeekText(row: CourseScheduleRow): string {
  return row.week_text || row.week_range || '--'
}

async function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`读取文件失败：${file.name}`))
    reader.readAsDataURL(file)
  })
}

async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`读取文件失败：${file.name}`))
    reader.readAsText(file)
  })
}

async function fileToPendingAttachment(file: File): Promise<PendingAttachment> {
  const content = await readFileAsDataUrl(file)
  const previewUrl = isImageType(file.type) ? URL.createObjectURL(file) : undefined
  const textSummary = canPreviewText(file.type, file.name)
    ? (await readFileAsText(file)).slice(0, 240)
    : undefined

  return {
    id: crypto.randomUUID(),
    name: file.name,
    type: file.type || 'application/octet-stream',
    size: file.size,
    content,
    previewUrl,
    textSummary,
  }
}

function revokeAttachmentUrls(attachments: Array<PendingAttachment | ChatAttachment>) {
  attachments.forEach((attachment) => {
    if (attachment.previewUrl?.startsWith('blob:')) {
      URL.revokeObjectURL(attachment.previewUrl)
    }
  })
}

function parseStreamPayload(line: string): StreamChunk | null {
  const raw = line.startsWith('data:') ? line.slice(5).trim() : line.trim()
  if (!raw || raw === '[DONE]') {
    return null
  }

  try {
    return JSON.parse(raw) as StreamChunk
  } catch {
    return { delta: raw }
  }
}

async function waitForStreamPaint(delay = 32): Promise<void> {
  await new Promise((resolve) => window.setTimeout(resolve, delay))
}

async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `请求失败（${response.status}）`)
  }
  return (await response.json()) as T
}

async function requestStreamChat(
  payload: ChatSendPayload,
  onPartialReply?: (content: string) => void,
): Promise<ChatSendResponse> {
  const streamPath = USE_MODERN_CHAT_API ? '/api/chat/stream' : '/stream'
  const response = await fetch(buildApiUrl(streamPath), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok || !response.body) {
    const errorText = await response.text()
    throw new Error(errorText || '流式请求失败')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let accumulated = ''
  let meta: ChatSendResponse = {}

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const payloadChunk = parseStreamPayload(line)
      if (!payloadChunk) {
        continue
      }

      if (payloadChunk.error) {
        throw new Error(payloadChunk.error)
      }

      if (payloadChunk.delta) {
        accumulated += payloadChunk.delta
        onPartialReply?.(accumulated)
        await waitForStreamPaint()
      }

      if (payloadChunk.reply) {
        accumulated = payloadChunk.reply
        onPartialReply?.(accumulated)
        await waitForStreamPaint()
      }

      if (payloadChunk.message?.content) {
        accumulated = payloadChunk.message.content
        onPartialReply?.(accumulated)
        await waitForStreamPaint()
      }

      meta = {
        ...meta,
        thread_id: payloadChunk.thread_id || meta.thread_id,
        title: payloadChunk.title || meta.title,
        preview: payloadChunk.preview || meta.preview,
      }
    }
  }

  if (buffer.trim()) {
    const payloadChunk = parseStreamPayload(buffer)
    if (payloadChunk?.error) {
      throw new Error(payloadChunk.error)
    }
    if (payloadChunk?.reply) {
      accumulated = payloadChunk.reply
      onPartialReply?.(accumulated)
    } else if (payloadChunk?.delta) {
      accumulated += payloadChunk.delta
      onPartialReply?.(accumulated)
    }
  }

  if (!accumulated.trim()) {
    throw new Error('流式响应未返回有效内容')
  }

  return {
    ...meta,
    reply: accumulated.trim(),
  }
}

async function sendChatPayload(
  payload: ChatSendPayload,
  onPartialReply?: (content: string) => void,
): Promise<ChatSendResponse> {
  if (USE_MODERN_CHAT_API) {
    try {
      return await requestStreamChat(payload, onPartialReply)
    } catch {
      return requestJson<ChatSendResponse>(buildApiUrl('/api/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
    }
  }

  try {
    return await requestStreamChat(payload, onPartialReply)
  } catch {
    const legacyResponse = await requestJson<LegacyChatResponse>(buildApiUrl('/'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: payload.message,
        thread_id: payload.thread_id,
      }),
    })

    return {
      thread_id: legacyResponse.thread_id || payload.thread_id,
      reply: legacyResponse.reply || '',
      preview: legacyResponse.reply?.slice(0, 28) || payload.message.slice(0, 28),
    }
  }
}

function Sidebar({ activeKey, items, onChange }: SidebarProps) {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white px-5 py-6">
      <div className="mb-8">
        <p className="text-xs font-medium tracking-[0.16em] text-slate-400">
          工作区
        </p>
        <h1 className="mt-2 text-xl font-semibold text-slate-900">
          个人秘书 Agent
        </h1>
      </div>

      <nav className="space-y-1.5">
        {items.map((item) => {
          const isActive = item.key === activeKey
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onChange(item.key)}
              className={`flex w-full items-center rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              {item.label}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}

function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
        {value}
      </p>
      <p className="mt-2 text-sm text-slate-500">{hint}</p>
    </div>
  )
}

function TimelineItem({ time, title, type }: TimelineItemProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <p className="text-sm font-medium text-slate-500">{time}</p>
        <p className="mt-2 text-base font-semibold text-slate-900">{title}</p>
      </div>
      <span
        className={`rounded-full px-3 py-1 text-xs font-medium ${getTimelineTagClasses(type)}`}
      >
        {type}
      </span>
    </div>
  )
}

function WeekCard({ day, focus, load }: WeekCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{day}</p>
      <p className="mt-3 text-sm font-semibold text-slate-900">{focus}</p>
      <span
        className={`mt-4 inline-flex rounded-full px-3 py-1 text-xs font-medium ${getDayLoadClasses(load)}`}
      >
        {load}
      </span>
    </div>
  )
}

function TaskItem({ title, deadline, priority }: TaskItemProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 py-4 last:border-b-0 last:pb-0 first:pt-0">
      <div>
        <p className="text-sm font-medium text-slate-900">{title}</p>
        <p className="mt-1 text-sm text-slate-500">截止时间：{deadline}</p>
      </div>
      <span
        className={`rounded-full px-3 py-1 text-xs font-medium ${getPriorityClasses(priority)}`}
      >
        {priority}
      </span>
    </div>
  )
}

function CourseScheduleTable({
  loading,
  error,
  rows,
  onRefresh,
}: {
  loading: boolean
  error: string
  rows: CourseScheduleRow[]
  onRefresh: () => void
}) {
  return (
    <section className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
            数据库课表
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            从 MySQL 的 course_schedule 表读取课程安排并展示。
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          刷新课表
        </button>
      </div>

      {loading ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
          正在从数据库加载课表...
        </div>
      ) : null}

      {!loading && error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      ) : null}

      {!loading && !error && rows.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
          当前 course_schedule 表还没有可展示的数据。你可以先让 AI
          秘书记录课表，再回来查看。
        </div>
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-5 py-4">学年</th>
                  <th className="px-5 py-4">学期</th>
                  <th className="px-5 py-4">星期</th>
                  <th className="px-5 py-4">时间</th>
                  <th className="px-5 py-4">课程</th>
                  <th className="px-5 py-4">地点</th>
                  <th className="px-5 py-4">教师</th>
                  <th className="px-5 py-4">周次</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((row, index) => (
                  <tr key={`${row.course_name || row.course || 'course'}-${index}`} className="transition hover:bg-slate-50">
                    <td className="px-5 py-4 text-slate-600">
                      {row.academic_year || row.year || '--'}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {row.term || row.semester || '--'}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {formatWeekday(row.weekday)}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {formatTimeRange(row)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="font-semibold text-slate-900">
                        {row.course_name || row.course || '--'}
                      </div>
                      {row.raw_source ? (
                        <div className="mt-1 truncate text-xs text-slate-400">
                          {row.raw_source}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {row.location || '--'}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {row.teacher || '--'}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {formatWeekText(row)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  )
}

function MessageBubble({
  message,
}: {
  message: ChatMessage
}) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${
            isUser
              ? 'bg-indigo-600 text-white'
              : 'border border-slate-200 bg-white text-slate-700'
          }`}
        >
          <p className="whitespace-pre-wrap">
            {message.content || (message.isStreaming ? '正在生成...' : '')}
          </p>
        </div>

        {message.attachments.length > 0 ? (
          <div className="grid gap-2">
            {message.attachments.map((attachment) => (
              <div
                key={`${message.id}-${attachment.name}`}
                className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">
                      {attachment.name}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      {attachment.type || '未知类型'}
                    </p>
                  </div>
                </div>

                {isImageType(attachment.type) && attachment.previewUrl ? (
                  <img
                    src={attachment.previewUrl}
                    alt={attachment.name}
                    className="mt-3 h-32 w-full rounded-xl object-cover"
                  />
                ) : null}

                {!isImageType(attachment.type) && attachment.textSummary ? (
                  <p className="mt-3 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-500">
                    {attachment.textSummary}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}

        <span className="text-xs text-slate-400">{message.createdAt}</span>
      </div>
    </div>
  )
}

function EmptyStateCard({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

export default function PersonalSecretaryDashboard() {
  const initialThreadState = useMemo(() => createInitialThreadState(), [])
  const [activeNav, setActiveNav] = useState<NavigationKey>('dashboard')
  const [threads, setThreads] = useState<ChatThread[]>(initialThreadState.threads)
  const [activeThreadId, setActiveThreadId] = useState<string>(
    initialThreadState.activeThreadId,
  )
  const [draftMessage, setDraftMessage] = useState('')
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([])
  const [chatError, setChatError] = useState('')
  const [chatLoading, setChatLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [courseRows, setCourseRows] = useState<CourseScheduleRow[]>([])
  const [courseLoading, setCourseLoading] = useState(false)
  const [courseLoaded, setCourseLoaded] = useState(false)
  const [courseError, setCourseError] = useState('')
  const messageBottomRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const pendingAttachmentsRef = useRef<PendingAttachment[]>(pendingAttachments)
  const threadsRef = useRef<ChatThread[]>(threads)

  const activeThread = useMemo(
    () =>
      threads.find((thread) => thread.threadId === activeThreadId) || threads[0],
    [activeThreadId, threads],
  )

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(threads))
    }
  }, [threads])

  useEffect(() => {
    pendingAttachmentsRef.current = pendingAttachments
  }, [pendingAttachments])

  useEffect(() => {
    threadsRef.current = threads
  }, [threads])

  const loadThreadHistory = useCallback(async (threadId: string): Promise<void> => {
    if (!USE_MODERN_CHAT_API) {
      return
    }

    setHistoryLoading(true)
    setChatError('')
    try {
      const payload = await requestJson<ChatHistoryResponse>(
        buildApiUrl(`/api/chat/history?thread_id=${encodeURIComponent(threadId)}`),
      )

      const nextMessages = (payload.messages || []).map(normalizeMessage)
      setThreads((currentThreads) =>
        currentThreads.map((thread) =>
          thread.threadId === threadId
            ? {
                ...thread,
                title: payload.title || thread.title,
                preview: payload.preview || thread.preview,
                isDraft: false,
                messages: nextMessages.length > 0 ? nextMessages : thread.messages,
              }
            : thread,
        ),
      )
    } catch (error) {
      if (!isNotFoundError(error)) {
        setChatError(
          error instanceof Error
            ? error.message
            : '加载聊天记录失败，请检查 /api/chat/history。',
        )
      }
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!USE_MODERN_CHAT_API) {
      setChatLoading(false)
      return
    }

    let alive = true

    const bootstrapThreads = async () => {
      setChatLoading(true)
      setChatError('')

      try {
        const payload = await requestJson<ChatThreadsResponse>(
          buildApiUrl('/api/chat/threads'),
        )
        if (!alive) {
          return
        }

        const normalizedThreads = normalizeThreadsResponse(payload)
        if (normalizedThreads.length === 0) {
          const draftThread = createDraftThread()
          setThreads([draftThread])
          setActiveThreadId(draftThread.threadId)
          return
        }

        setThreads(normalizedThreads)
        setActiveThreadId(normalizedThreads[0].threadId)
        await loadThreadHistory(normalizedThreads[0].threadId)
      } catch (error) {
        if (!alive) {
          return
        }
        if (!isNotFoundError(error)) {
          setChatError(
            error instanceof Error
              ? error.message
              : '加载线程列表失败，请检查 /api/chat/threads。',
          )
        }
      } finally {
        if (alive) {
          setChatLoading(false)
        }
      }
    }

    void bootstrapThreads()

    return () => {
      alive = false
    }
  }, [loadThreadHistory])

  useEffect(() => {
    if (activeNav === 'schedule' && !courseLoaded && !courseLoading) {
      void fetchCourseSchedule()
    }
  }, [activeNav, courseLoaded, courseLoading])

  useEffect(() => {
    messageBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeThread?.messages.length, sending, activeThreadId])

  useEffect(() => {
    return () => {
      revokeAttachmentUrls(pendingAttachmentsRef.current)
      threadsRef.current.forEach((thread) => {
        thread.messages.forEach((message) => revokeAttachmentUrls(message.attachments))
      })
    }
  }, [])

  async function refreshThreadList(preferredThreadId?: string): Promise<void> {
    if (!USE_MODERN_CHAT_API) {
      if (preferredThreadId) {
        setActiveThreadId(preferredThreadId)
      }
      return
    }

    try {
      const payload = await requestJson<ChatThreadsResponse>(
        buildApiUrl('/api/chat/threads'),
      )
      const serverThreads = normalizeThreadsResponse(payload)
      if (serverThreads.length === 0) {
        return
      }

      setThreads((currentThreads) =>
        serverThreads.map((serverThread) => {
          const localThread = currentThreads.find(
            (thread) => thread.threadId === serverThread.threadId,
          )
          return localThread
            ? {
                ...localThread,
                title: serverThread.title,
                preview: serverThread.preview,
                isDraft: false,
              }
            : serverThread
        }),
      )

      if (preferredThreadId) {
        setActiveThreadId(preferredThreadId)
      }
    } catch (error) {
      if (!isNotFoundError(error)) {
        // 刷新线程列表失败时保留本地状态
      }
    }
  }

  async function fetchCourseSchedule() {
    setCourseLoading(true)
    setCourseError('')
    try {
      const payload = await requestJson<CourseScheduleResponse | CourseScheduleRow[]>(
        buildApiUrl('/api/course-schedule'),
      )
      setCourseRows(normalizeCourseScheduleResponse(payload))
      setCourseLoaded(true)
    } catch (error) {
      setCourseError(
        error instanceof Error
          ? error.message
          : '读取课表失败，请检查 /api/course-schedule。',
      )
      setCourseLoaded(true)
    } finally {
      setCourseLoading(false)
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || [])
    if (files.length === 0) {
      return
    }

    if (pendingAttachments.length + files.length > 3) {
      setChatError('附件最多 3 个，请先移除后再继续添加。')
      event.target.value = ''
      return
    }

    try {
      const attachments = await Promise.all(files.map(fileToPendingAttachment))
      setPendingAttachments((current) => [...current, ...attachments])
      setChatError('')
    } catch (error) {
      setChatError(
        error instanceof Error ? error.message : '读取附件失败，请稍后重试。',
      )
    } finally {
      event.target.value = ''
    }
  }

  function handleRemovePendingAttachment(attachmentId: string) {
    setPendingAttachments((current) => {
      const target = current.find((item) => item.id === attachmentId)
      if (target) {
        revokeAttachmentUrls([target])
      }
      return current.filter((item) => item.id !== attachmentId)
    })
  }

  function handleClearPendingAttachments() {
    revokeAttachmentUrls(pendingAttachments)
    setPendingAttachments([])
  }

  function handleNewThread() {
    const draftThread = createDraftThread()
    setThreads((current) => [draftThread, ...current])
    setActiveThreadId(draftThread.threadId)
    setDraftMessage('')
    setPendingAttachments([])
    setChatError('')
  }

  async function handleThreadChange(threadId: string) {
    const target = threads.find((thread) => thread.threadId === threadId)
    if (!target) {
      return
    }

    setActiveThreadId(threadId)
    setDraftMessage('')
    setPendingAttachments([])
    setChatError('')

    if (!target.isDraft && target.messages.length === 0) {
      await loadThreadHistory(threadId)
    }
  }

  async function handleSendMessage() {
    if (!activeThread || sending || !draftMessage.trim()) {
      return
    }

    const outgoingText = draftMessage.trim()
    const outgoingAttachments = [...pendingAttachments]
    const assistantMessageId = crypto.randomUUID()
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: outgoingText,
      createdAt: formatClock(new Date()),
      attachments: outgoingAttachments.map(normalizeAttachment),
    }
    const assistantPlaceholder: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      createdAt: formatClock(new Date()),
      attachments: [],
      isStreaming: true,
    }

    setThreads((current) =>
      current.map((thread) =>
        thread.threadId === activeThread.threadId
          ? {
              ...thread,
              messages: [...thread.messages, userMessage, assistantPlaceholder],
              preview: outgoingText,
              title:
                thread.isDraft && thread.title === '草稿会话'
                  ? outgoingText.slice(0, 14) || '新会话'
                  : thread.title,
            }
          : thread,
      ),
    )
    setDraftMessage('')
    setPendingAttachments([])
    setSending(true)
    setChatError('')

    try {
      const response = await sendChatPayload({
        message: outgoingText,
        thread_id: activeThread.threadId,
        attachments: outgoingAttachments.map((attachment) => ({
          name: attachment.name,
          type: attachment.type,
          size: attachment.size,
          content: attachment.content,
        })),
      }, (partialReply) => {
        setThreads((current) =>
          current.map((thread) =>
            thread.threadId === activeThread.threadId
              ? {
                  ...thread,
                  messages: thread.messages.map((message) =>
                    message.id === assistantMessageId
                      ? {
                          ...message,
                          content: partialReply,
                          isStreaming: true,
                        }
                      : message,
                  ),
                }
              : thread,
          ),
        )
      })

      const assistantMessage = response.message
        ? normalizeMessage(response.message)
        : normalizeMessage({
            role: 'assistant',
            content: response.reply || '',
            created_at: formatClock(new Date()),
          })

      setThreads((current) =>
        current.map((thread) =>
          thread.threadId === activeThread.threadId
            ? {
                ...thread,
                title:
                  response.title ||
                  (thread.title === '草稿会话' ? outgoingText.slice(0, 14) : thread.title),
                preview:
                  response.preview ||
                  response.reply?.slice(0, 28) ||
                  outgoingText.slice(0, 28),
                isDraft: false,
                messages: thread.messages.map((message) =>
                  message.id === assistantMessageId
                    ? {
                        ...assistantMessage,
                        id: assistantMessageId,
                        isStreaming: false,
                      }
                    : message,
                ),
              }
            : thread,
        ),
      )

      await refreshThreadList(response.thread_id || activeThread.threadId)
    } catch (error) {
      setThreads((current) =>
        current.map((thread) =>
          thread.threadId === activeThread.threadId
            ? {
                ...thread,
                messages: thread.messages.filter(
                  (message) => message.id !== assistantMessageId,
                ),
              }
            : thread,
        ),
      )
      setChatError(
        error instanceof Error ? error.message : '发送失败，请检查聊天接口。',
      )
    } finally {
      revokeAttachmentUrls(outgoingAttachments)
      setSending(false)
    }
  }

  function renderMainContent(): ReactNode {
    const dashboardSections = (
      <div className="space-y-8">
        <section>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {statCards.map((stat) => (
              <StatCard key={stat.label} {...stat} />
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">今日时间线</h2>
            <span className="text-sm text-slate-500">固定安排 + 建议任务</span>
          </div>
          <div className="space-y-3">
            {timelineEntries.map((item) => (
              <TimelineItem key={`${item.time}-${item.title}`} {...item} />
            ))}
          </div>
        </section>
      </div>
    )

    if (activeNav === 'dashboard') {
      return (
        <div className="space-y-8">
          {dashboardSections}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-900">未来 7 天计划</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-7">
              {weekPlans.map((plan) => (
                <WeekCard key={plan.day} {...plan} />
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">任务池</h2>
              <button
                type="button"
                className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
              >
                查看全部
              </button>
            </div>
            <div className="mt-4">
              {tasks.map((task) => (
                <TaskItem key={task.title} {...task} />
              ))}
            </div>
          </section>
        </div>
      )
    }

    if (activeNav === 'today') {
      return dashboardSections
    }

    if (activeNav === 'next7days') {
      return (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">未来 7 天计划</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-7">
            {weekPlans.map((plan) => (
              <WeekCard key={plan.day} {...plan} />
            ))}
          </div>
        </section>
      )
    }

    if (activeNav === 'schedule') {
      return (
        <CourseScheduleTable
          loading={courseLoading}
          error={courseError}
          rows={courseRows}
          onRefresh={() => {
            void fetchCourseSchedule()
          }}
        />
      )
    }

    if (activeNav === 'tasks') {
      return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">任务池</h2>
            <button
              type="button"
              className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
            >
              查看全部
            </button>
          </div>
          <div className="mt-4">
            {tasks.map((task) => (
              <TaskItem key={task.title} {...task} />
            ))}
          </div>
        </section>
      )
    }

    return (
      <EmptyStateCard
        title="设置"
        description="这里可以继续扩展模型偏好、工作时段、提醒策略和附件默认处理方式。当前先保留为设置占位卡片。"
      />
    )
  }

  if (!activeThread) {
    return null
  }

  return (
    <div className="h-screen bg-slate-50 text-slate-900">
      <div className="flex h-full min-w-[1440px]">
        <Sidebar
          activeKey={activeNav}
          items={navigationItems}
          onChange={setActiveNav}
        />

        <main className="min-w-0 flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
          <div className="mx-auto max-w-6xl">
            <div className="mb-8 flex items-start justify-between gap-6">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                  个人秘书
                </h1>
                <p className="mt-2 text-base text-slate-500">
                  未来 7 天日程助手
                </p>
              </div>
              <button
                type="button"
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
              >
                重新规划
              </button>
            </div>

            {renderMainContent()}
          </div>
        </main>

        <aside className="w-[500px] shrink-0 border-l border-slate-200 bg-white px-6 py-8">
          <div className="h-[760px] rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex h-full flex-col">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-900">
                    和 AI 秘书对话
                  </p>
                  <select
                    className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none transition focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100"
                    value={activeThread.threadId}
                    onChange={(event) => {
                      void handleThreadChange(event.target.value)
                    }}
                    disabled={chatLoading || sending}
                  >
                    {threads.map((thread) => (
                      <option key={thread.threadId} value={thread.threadId}>
                        {formatThreadTitle(thread)}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="button"
                  onClick={handleNewThread}
                  disabled={sending}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  新建对话
                </button>
              </div>

              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-900">
                  {formatThreadTitle(activeThread)}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {activeThread.isDraft
                    ? '当前为草稿会话，发送首条消息后会自动保存。'
                    : activeThread.preview}
                </p>
              </div>

              <div className="mt-4 min-h-0 flex-1 overflow-hidden rounded-2xl bg-slate-50 p-4">
                <div className="h-full overflow-y-auto pr-1">
                  {historyLoading ? (
                    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-6 text-center text-sm text-slate-500">
                      正在加载聊天记录...
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {activeThread.messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                      ))}
                      <div ref={messageBottomRef} />
                    </div>
                  )}
                </div>
              </div>

              {chatError ? (
                <p className="mt-3 text-sm text-red-600">{chatError}</p>
              ) : null}

              {pendingAttachments.length > 0 ? (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex items-center justify-between gap-4">
                    <p className="text-sm font-medium text-slate-900">
                      待发送附件（最多 3 个）
                    </p>
                    <button
                      type="button"
                      onClick={handleClearPendingAttachments}
                      className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
                    >
                      清空
                    </button>
                  </div>

                  <div className="mt-3 space-y-3">
                    {pendingAttachments.map((attachment) => (
                      <div
                        key={attachment.id}
                        className="rounded-2xl border border-slate-200 bg-slate-50 p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-900">
                              {attachment.name}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {attachment.type}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemovePendingAttachment(attachment.id)}
                            className="text-xs font-medium text-slate-500 transition hover:text-slate-900"
                          >
                            移除
                          </button>
                        </div>

                        {isImageType(attachment.type) && attachment.previewUrl ? (
                          <img
                            src={attachment.previewUrl}
                            alt={attachment.name}
                            className="mt-3 h-32 w-full rounded-xl object-cover"
                          />
                        ) : null}

                        {!isImageType(attachment.type) && attachment.textSummary ? (
                          <p className="mt-3 rounded-xl bg-white p-3 text-xs leading-5 text-slate-500">
                            {attachment.textSummary}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="mt-4">
                <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
                  <div className="flex items-end gap-3">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      附件
                    </button>

                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      className="hidden"
                      onChange={handleFileChange}
                    />

                    <textarea
                      value={draftMessage}
                      onChange={(event) => setDraftMessage(event.target.value)}
                      placeholder="问问你的秘书..."
                      className="min-h-[84px] flex-1 resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700 outline-none transition focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100"
                    />

                    <button
                      type="button"
                      onClick={() => {
                        void handleSendMessage()
                      }}
                      disabled={sending || !draftMessage.trim()}
                      className="rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                    >
                      {sending ? '发送中...' : '发送'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
