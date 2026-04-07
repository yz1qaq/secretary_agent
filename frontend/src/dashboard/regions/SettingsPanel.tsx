/* eslint-disable react-refresh/only-export-components */

import {
  AssistantProfileFormData,
  SettingsData,
  UserProfileFormData,
  WorkspaceCopy,
} from '../types'

export const settingsWorkspaceCopy: WorkspaceCopy = {
  eyebrow: 'Memory Control Center',
  title: '设置',
  subtitle: '在这里调整模型接入、查看 MemoryOS 的短中期记忆，并维护长期画像的手动设定。',
}

const userProfileFields: Array<{
  key: keyof UserProfileFormData
  label: string
  multiline?: boolean
}> = [
  { key: 'name', label: '姓名' },
  { key: 'alias', label: '称呼偏好' },
  { key: 'role', label: '身份角色' },
  { key: 'school', label: '学校' },
  { key: 'major', label: '专业方向' },
  { key: 'grade_or_stage', label: '年级阶段' },
  { key: 'advisor', label: '导师' },
  { key: 'goals', label: '目标', multiline: true },
  { key: 'preferences', label: '偏好', multiline: true },
  { key: 'constraints', label: '约束', multiline: true },
  { key: 'notes', label: '备注', multiline: true },
]

const assistantProfileFields: Array<{
  key: keyof AssistantProfileFormData
  label: string
  multiline?: boolean
}> = [
  { key: 'name', label: '名称' },
  { key: 'role', label: '角色' },
  { key: 'tone', label: '语气风格' },
  { key: 'core_responsibilities', label: '核心职责', multiline: true },
  { key: 'response_style', label: '回复风格', multiline: true },
  { key: 'tool_usage_style', label: '工具使用方式', multiline: true },
  { key: 'boundaries', label: '边界原则', multiline: true },
  { key: 'notes', label: '备注', multiline: true },
]

function FieldCard({
  label,
  value,
  multiline = false,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  multiline?: boolean
  onChange: (value: string) => void
  placeholder?: string
}) {
  const commonClassName =
    'mt-3 w-full rounded-[18px] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-sky-300 focus:ring-2 focus:ring-sky-100'

  return (
    <label className="block rounded-[22px] border border-white/80 bg-white/80 p-4 shadow-[0_8px_20px_rgba(15,23,42,0.05)]">
      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </span>
      {multiline ? (
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          rows={4}
          className={`${commonClassName} resize-y`}
        />
      ) : (
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          className={commonClassName}
        />
      )}
    </label>
  )
}

function ReadonlyTextCard({
  title,
  content,
}: {
  title: string
  content: string
}) {
  return (
    <div className="rounded-[22px] border border-white/80 bg-white/80 p-4 shadow-[0_8px_20px_rgba(15,23,42,0.05)]">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        {title}
      </p>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-600">
        {content || '当前还没有可展示的内容。'}
      </p>
    </div>
  )
}

function formatTimestamp(value?: string): string {
  if (!value) {
    return '--'
  }
  return value.replace('T', ' ').slice(0, 16)
}

function summarizeText(value?: string, limit = 88): string {
  const clean = (value || '').trim().replace(/\s+/g, ' ')
  if (!clean) {
    return '暂无内容'
  }
  return clean.length <= limit ? clean : `${clean.slice(0, limit)}...`
}

function renderProfilePreview(
  profile: UserProfileFormData | AssistantProfileFormData,
  labels: Record<string, string>,
): string {
  const profileRecord = profile as unknown as Record<string, string>
  const lines = Object.entries(labels)
    .map(([field, label]) => {
      const value = profileRecord[field]
      return value ? `- ${label}：${value}` : ''
    })
    .filter(Boolean)

  return lines.length > 0 ? lines.join('\n') : '当前还没有可展示的内容。'
}

export function SettingsPanel({
  settings,
  loading,
  error,
  modelForm,
  modelSaving,
  modelSuccess,
  onModelFieldChange,
  onSaveModel,
  longTermForm,
  longTermSaving,
  longTermSuccess,
  onLongTermFieldChange,
  onSaveLongTerm,
}: {
  settings: SettingsData | null
  loading: boolean
  error: string
  modelForm: {
    baseUrl: string
    apiKey: string
    modelName: string
  }
  modelSaving: boolean
  modelSuccess: string
  onModelFieldChange: (field: 'baseUrl' | 'apiKey' | 'modelName', value: string) => void
  onSaveModel: () => void | Promise<void>
  longTermForm: {
    user: UserProfileFormData
    assistant: AssistantProfileFormData
  }
  longTermSaving: boolean
  longTermSuccess: string
  onLongTermFieldChange: (
    kind: 'user' | 'assistant',
    field: string,
    value: string,
  ) => void
  onSaveLongTerm: () => void | Promise<void>
}) {
  const shortTerm = settings?.memory.short_term || []
  const midTerm = settings?.memory.mid_term || []
  const longTerm = settings?.memory.long_term

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(241,245,249,0.94))] p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Settings & Memory
        </p>
        <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-2xl">
            <h2 className="text-3xl font-semibold tracking-tight text-slate-900">
              把模型接入、短中期记忆和长期画像放在一个可管理的控制台里。
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              模型配置会在保存后直接热更新。长期记忆则同时保留用户手工设定与 MemoryOS 自动归纳的结果，最终供对话时一起使用。
            </p>
          </div>
          <div className="rounded-[28px] border border-white/80 bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(15,23,42,0.05)] xl:max-w-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              当前状态
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {loading
                ? '正在读取设置与记忆中心...'
                : '你可以在这里调整模型接入，并查看 MemoryOS 的分层记忆快照。'}
            </p>
          </div>
        </div>

        {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
      </section>

      <section className="rounded-[32px] border border-white/70 bg-white/88 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
              模型配置
            </p>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
              动态切换当前生效模型
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              `api_key` 已配置时会以掩码显示；如果这次不打算修改密钥，可以留空直接保存其他字段。
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              void onSaveModel()
            }}
            disabled={loading || modelSaving}
            className="rounded-full border border-slate-200 bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {modelSaving ? '保存中...' : '保存模型配置'}
          </button>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-3">
          <FieldCard
            label="Base URL"
            value={modelForm.baseUrl}
            onChange={(value) => onModelFieldChange('baseUrl', value)}
            placeholder="https://example.com/v1"
          />
          <FieldCard
            label="API Key"
            value={modelForm.apiKey}
            onChange={(value) => onModelFieldChange('apiKey', value)}
            placeholder={
              settings?.model.api_key_configured
                ? `已配置：${settings.model.api_key_masked}，留空表示保持不变`
                : '输入新的 API Key'
            }
          />
          <FieldCard
            label="Model Name"
            value={modelForm.modelName}
            onChange={(value) => onModelFieldChange('modelName', value)}
            placeholder="qwen3.5-plus"
          />
        </div>

        {modelSuccess ? (
          <p className="mt-4 text-sm text-emerald-600">{modelSuccess}</p>
        ) : null}
      </section>

      <section className="rounded-[32px] border border-white/70 bg-white/88 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
              短期记忆
            </p>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
              最近进入 MemoryOS 的对话片段
            </h3>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-200">
            {shortTerm.length} 条
          </span>
        </div>

        <div className="mt-5 space-y-3">
          {shortTerm.length > 0 ? (
            [...shortTerm].reverse().map((item) => (
              <div
                key={item.id || `${item.thread_id}-${item.timestamp}`}
                className="rounded-[24px] border border-white/80 bg-white/80 p-4 shadow-[0_8px_20px_rgba(15,23,42,0.05)]"
              >
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                  <span>{formatTimestamp(item.timestamp)}</span>
                  <span>thread: {item.thread_id || '--'}</span>
                </div>
                <p className="mt-3 text-sm font-medium text-slate-900">
                  用户：{summarizeText(item.user_input)}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  助手：{summarizeText(item.agent_response, 120)}
                </p>
              </div>
            ))
          ) : (
            <ReadonlyTextCard title="状态" content="当前短期记忆为空，新的问答会先进入这里。" />
          )}
        </div>
      </section>

      <section className="rounded-[32px] border border-white/70 bg-white/88 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
              中期记忆
            </p>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
              已经聚合成片段的主题记忆
            </h3>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-200">
            {midTerm.length} 段
          </span>
        </div>

        <div className="mt-5 space-y-3">
          {midTerm.length > 0 ? (
            [...midTerm]
              .sort((a, b) => (Number(b.heat || 0) - Number(a.heat || 0)))
              .map((segment) => (
                <div
                  key={segment.id || segment.title}
                  className="rounded-[24px] border border-white/80 bg-white/80 p-4 shadow-[0_8px_20px_rgba(15,23,42,0.05)]"
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <h4 className="text-base font-semibold text-slate-900">
                      {segment.title || '未命名片段'}
                    </h4>
                    <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-200">
                      heat {Number(segment.heat || 0).toFixed(2)}
                    </span>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-200">
                      检索 {segment.retrieval_count || 0} 次
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-500">
                    {segment.summary || '暂无摘要'}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <span>更新时间：{formatTimestamp(segment.updated_at)}</span>
                    <span>{segment.analyzed ? '已分析' : '待分析'}</span>
                    {(segment.keywords || []).slice(0, 5).map((keyword) => (
                      <span
                        key={`${segment.id}-${keyword}`}
                        className="rounded-full bg-amber-50 px-3 py-1 text-amber-700 ring-1 ring-inset ring-amber-200"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              ))
          ) : (
            <ReadonlyTextCard title="状态" content="当前还没有进入中期记忆的片段，短期记忆达到阈值后会自动聚合。" />
          )}
        </div>
      </section>

      <section className="rounded-[32px] border border-white/70 bg-white/88 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
              长期记忆
            </p>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
              手动画像 + 自动归纳画像的合并结果
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              手动填写的字段优先级更高；MemoryOS 的自动归纳会补足空缺字段，最终合并摘要会作为长期画像注入模型。
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              void onSaveLongTerm()
            }}
            disabled={loading || longTermSaving}
            className="rounded-full border border-slate-200 bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {longTermSaving ? '保存中...' : '保存长期画像'}
          </button>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <div className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
                用户画像
              </p>
              <h4 className="mt-2 text-xl font-semibold text-slate-900">
                手动维护用户侧的稳定偏好与背景
              </h4>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {userProfileFields.map((field) => (
                <div
                  key={field.key}
                  className={field.multiline ? 'md:col-span-2' : undefined}
                >
                  <FieldCard
                    label={field.label}
                    value={longTermForm.user[field.key]}
                    multiline={field.multiline}
                    onChange={(value) => onLongTermFieldChange('user', field.key, value)}
                  />
                </div>
              ))}
            </div>
            <ReadonlyTextCard
              title="自动归纳画像"
              content={
                longTerm
                  ? renderProfilePreview(longTerm.user.inferred_profile, {
                      name: '姓名',
                      alias: '称呼偏好',
                      role: '身份角色',
                      school: '学校',
                      major: '专业方向',
                      grade_or_stage: '年级阶段',
                      advisor: '导师',
                      goals: '目标',
                      preferences: '偏好',
                      constraints: '约束',
                      notes: '备注',
                    })
                  : ''
              }
            />
            <ReadonlyTextCard
              title="合并后画像摘要"
              content={longTerm?.user.merged_profile_text || ''}
            />
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                Agent 画像
              </p>
              <h4 className="mt-2 text-xl font-semibold text-slate-900">
                维护秘书的角色边界、语气和工具使用方式
              </h4>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {assistantProfileFields.map((field) => (
                <div
                  key={field.key}
                  className={field.multiline ? 'md:col-span-2' : undefined}
                >
                  <FieldCard
                    label={field.label}
                    value={longTermForm.assistant[field.key]}
                    multiline={field.multiline}
                    onChange={(value) =>
                      onLongTermFieldChange('assistant', field.key, value)
                    }
                  />
                </div>
              ))}
            </div>
            <ReadonlyTextCard
              title="自动归纳画像"
              content={
                longTerm
                  ? renderProfilePreview(longTerm.assistant.inferred_profile, {
                      name: '名称',
                      role: '角色',
                      tone: '语气风格',
                      core_responsibilities: '核心职责',
                      response_style: '回复风格',
                      tool_usage_style: '工具使用方式',
                      boundaries: '边界原则',
                      notes: '备注',
                    })
                  : ''
              }
            />
            <ReadonlyTextCard
              title="合并后画像摘要"
              content={longTerm?.assistant.merged_profile_text || ''}
            />
          </div>
        </div>

        {longTermSuccess ? (
          <p className="mt-4 text-sm text-emerald-600">{longTermSuccess}</p>
        ) : null}
      </section>
    </div>
  )
}
