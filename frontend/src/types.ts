export type MessageRole = 'assistant' | 'user' | 'system'
export type WorkspacePageId = 'today' | 'life' | 'study'

export interface Message {
  id: string
  role: MessageRole
  roleLabel: string
  content: string
  time: string
}

export interface ChatApiResponse {
  status: string
  reply: string
  thread_id: string
  checkpointer: string
}

export interface WorkspaceHighlight {
  id: string
  title: string
  detail: string
  meta: string
}

export interface WorkspaceTimelineItem {
  id: string
  time: string
  title: string
  note: string
}

export interface WorkspacePage {
  id: WorkspacePageId
  label: string
  eyebrow: string
  title: string
  subtitle: string
  note: string
  highlights: WorkspaceHighlight[]
  timeline: WorkspaceTimelineItem[]
  prompts: string[]
}

export interface ChatConversation {
  id: string
  title: string
  summary: string
  updatedAt: string
  threadId: string
  messages: Message[]
}
