import {
  ChangeEvent,
  ReactNode,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import { LifePanel, lifeWorkspaceCopy } from './dashboard/regions/LifePanel'
import {
  SidebarNav,
  sidebarNavItems,
} from './dashboard/regions/SidebarNav'
import { StudyPanel, studyWorkspaceCopy } from './dashboard/regions/StudyPanel'
import {
  TodayPlanPanel,
  todayPlanWorkspaceCopy,
} from './dashboard/regions/TodayPlanPanel'
import { NavigationKey, RefreshPanelKey } from './dashboard/types'

type MessageRole = 'assistant' | 'user'

const API_BASE_URL = (
  import.meta.env.VITE_SECRETARY_API_URL || 'http://127.0.0.1:9826'
).replace(/\/$/, '')
const CHAT_BACKEND_MODE = import.meta.env.VITE_SECRETARY_CHAT_MODE || 'modern'
const USE_MODERN_CHAT_API = CHAT_BACKEND_MODE === 'modern'

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
  is_draft?: boolean
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

interface PanelRefreshResponse {
  status?: string
  panel?: RefreshPanelKey
  message?: string
  thread_id?: string
}

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

function summarizePanelRefreshMessage(message: string, panel: RefreshPanelKey): string {
  const clean = message.trim()
  if (!clean) {
    return `${panel === 'study' ? '学习' : '生活'}界面已触发静默刷新。`
  }
  if (clean.length <= 48) {
    return clean
  }
  return `${clean.slice(0, 48)}...`
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
    isDraft: Boolean(thread.is_draft),
    messages: [],
  }))
}

async function createServerThread(requestedThreadId?: string): Promise<ChatThread> {
  const payload = await requestJson<ThreadListItemResponse>(buildApiUrl('/api/chat/threads'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      thread_id: requestedThreadId,
      title: '草稿会话',
      preview: '当前为草稿会话，发送首条消息后会自动保存。',
      is_draft: true,
    }),
  })

  return {
    threadId: payload.thread_id,
    title: payload.title || '草稿会话',
    preview: payload.preview || '当前为草稿会话，发送首条消息后会自动保存。',
    isDraft: payload.is_draft ?? true,
    messages: defaultAssistantMessages,
  }
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
        attachments: payload.attachments,
      }),
    })

    return {
      thread_id: legacyResponse.thread_id || payload.thread_id,
      reply: legacyResponse.reply || '',
      preview: legacyResponse.reply?.slice(0, 28) || payload.message.slice(0, 28),
    }
  }
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

function getWorkspaceCopy(activeNav: NavigationKey): {
  title: string
  subtitle: string
} {
  if (activeNav === 'today') {
    return studyWorkspaceCopy
  }

  if (activeNav === 'tasks') {
    return lifeWorkspaceCopy
  }

  return todayPlanWorkspaceCopy
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
  const [panelRefreshState, setPanelRefreshState] = useState<
    Record<RefreshPanelKey, { refreshing: boolean; message: string; error: string }>
  >({
    study: { refreshing: false, message: '', error: '' },
    life: { refreshing: false, message: '', error: '' },
  })
  const messageBottomRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const pendingAttachmentsRef = useRef<PendingAttachment[]>(pendingAttachments)
  const threadsRef = useRef<ChatThread[]>(threads)

  const activeThread = useMemo(
    () =>
      threads.find((thread) => thread.threadId === activeThreadId) || threads[0],
    [activeThreadId, threads],
  )
  const lastMessage = activeThread?.messages[activeThread.messages.length - 1]
  const lastMessageSignature = useMemo(
    () =>
      lastMessage
        ? `${lastMessage.id}:${lastMessage.content.length}:${lastMessage.isStreaming ? '1' : '0'}`
        : 'empty',
    [lastMessage],
  )

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
          const draftThread = await createServerThread()
          if (!alive) {
            return
          }
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
        const draftThread = createDraftThread()
        setThreads([draftThread])
        setActiveThreadId(draftThread.threadId)
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

  useLayoutEffect(() => {
    const animationFrame = window.requestAnimationFrame(() => {
      messageBottomRef.current?.scrollIntoView({
        behavior: lastMessage?.isStreaming ? 'auto' : 'smooth',
        block: 'end',
      })
    })

    return () => {
      window.cancelAnimationFrame(animationFrame)
    }
  }, [activeThreadId, lastMessageSignature, sending, lastMessage?.isStreaming])

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

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || [])
    if (files.length === 0) {
      return
    }

    if (files.some((file) => !isImageType(file.type))) {
      setChatError('当前仅支持上传图片，请选择 JPG、PNG、WEBP 等图片文件。')
      event.target.value = ''
      return
    }

    if (pendingAttachments.length + files.length > 3) {
      setChatError('图片最多上传 3 张，请先移除后再继续添加。')
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

  async function handleNewThread() {
    try {
      const draftThread = USE_MODERN_CHAT_API
        ? await createServerThread(crypto.randomUUID())
        : createDraftThread()
      setThreads((current) => [draftThread, ...current])
      setActiveThreadId(draftThread.threadId)
      setDraftMessage('')
      setPendingAttachments([])
      setChatError('')
    } catch (error) {
      setChatError(
        error instanceof Error ? error.message : '创建新会话失败，请稍后重试。',
      )
    }
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
    if (!activeThread || sending) {
      return
    }

    const outgoingText = draftMessage.trim()
    const outgoingAttachments = [...pendingAttachments]
    if (!outgoingText && outgoingAttachments.length === 0) {
      return
    }

    const previewText =
      outgoingText || `发送了 ${outgoingAttachments.length} 张图片`
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
              preview: previewText,
              title:
                thread.isDraft && thread.title === '草稿会话'
                  ? previewText.slice(0, 14) || '新会话'
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
                  (thread.title === '草稿会话' ? previewText.slice(0, 14) : thread.title),
                preview:
                  response.preview ||
                  response.reply?.slice(0, 28) ||
                  previewText.slice(0, 28),
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

  async function handlePanelRefresh(panel: RefreshPanelKey) {
    setPanelRefreshState((current) => ({
      ...current,
      [panel]: {
        refreshing: true,
        message: '',
        error: '',
      },
    }))

    try {
      const response = await requestJson<PanelRefreshResponse>(
        buildApiUrl('/api/panel-refresh'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ panel }),
        },
      )

      setPanelRefreshState((current) => ({
        ...current,
        [panel]: {
          refreshing: false,
          message: summarizePanelRefreshMessage(response.message || '', panel),
          error: '',
        },
      }))
    } catch (error) {
      setPanelRefreshState((current) => ({
        ...current,
        [panel]: {
          refreshing: false,
          message: '',
          error:
            error instanceof Error
              ? error.message
              : `${panel === 'study' ? '学习' : '生活'}界面刷新失败，请稍后重试。`,
        },
      }))
    }
  }

  function renderMainContent(): ReactNode {
    if (activeNav === 'dashboard') {
      return <TodayPlanPanel />
    }

    if (activeNav === 'today') {
      return (
        <StudyPanel
          onRefresh={() => handlePanelRefresh('study')}
          refreshing={panelRefreshState.study.refreshing}
          refreshMessage={panelRefreshState.study.message}
          refreshError={panelRefreshState.study.error}
        />
      )
    }

    if (activeNav === 'tasks') {
      return (
        <LifePanel
          onRefresh={() => handlePanelRefresh('life')}
          refreshing={panelRefreshState.life.refreshing}
          refreshMessage={panelRefreshState.life.message}
          refreshError={panelRefreshState.life.error}
        />
      )
    }

    return null
  }

  if (!activeThread) {
    return null
  }

  const workspaceCopy = getWorkspaceCopy(activeNav)

  return (
    <div className="h-screen bg-slate-50 text-slate-900">
      <div className="flex h-full min-w-[1440px]">
        <SidebarNav
          activeKey={activeNav}
          items={sidebarNavItems}
          onChange={setActiveNav}
        />

        <main className="min-w-0 flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
          <div className="mx-auto max-w-6xl">
            <div className="mb-8 flex items-start justify-between gap-6">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                  {workspaceCopy.title}
                </h1>
                <p className="mt-2 text-base text-slate-500">
                  {workspaceCopy.subtitle}
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
                  onClick={() => {
                    void handleNewThread()
                  }}
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
                      待发送图片（最多 3 张）
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
                      accept="image/*"
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
                      disabled={sending || (!draftMessage.trim() && pendingAttachments.length === 0)}
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
