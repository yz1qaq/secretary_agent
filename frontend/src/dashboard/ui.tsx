import { ReactNode, useState } from 'react'

import {
  PlanDrawerData,
  PlanItemData,
  PlanTone,
  PriorityLevel,
  StatCardData,
  TaskData,
  TimelineEntry,
} from './types'

function getPriorityClasses(priority: PriorityLevel): string {
  if (priority === '高') {
    return 'bg-rose-100 text-rose-700 ring-1 ring-inset ring-rose-200'
  }
  if (priority === '中') {
    return 'bg-amber-100 text-amber-700 ring-1 ring-inset ring-amber-200'
  }
  return 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200'
}

function getTimelineTagClasses(type: TimelineEntry['type']): string {
  return type === '固定安排'
    ? 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200'
    : 'bg-indigo-100 text-indigo-700 ring-1 ring-inset ring-indigo-200'
}

function getToneClasses(tone: PlanTone): {
  badge: string
  dot: string
  surface: string
  accent: string
} {
  if (tone === 'study') {
    return {
      badge: 'bg-sky-100 text-sky-700 ring-1 ring-inset ring-sky-200',
      dot: 'bg-sky-500',
      surface: 'bg-sky-50/70',
      accent: 'text-sky-700',
    }
  }
  if (tone === 'life') {
    return {
      badge: 'bg-emerald-100 text-emerald-700 ring-1 ring-inset ring-emerald-200',
      dot: 'bg-emerald-500',
      surface: 'bg-emerald-50/70',
      accent: 'text-emerald-700',
    }
  }
  return {
    badge: 'bg-violet-100 text-violet-700 ring-1 ring-inset ring-violet-200',
    dot: 'bg-violet-500',
    surface: 'bg-violet-50/70',
    accent: 'text-violet-700',
  }
}

export function StatCard({ label, value, hint }: StatCardData) {
  return (
    <div className="rounded-[28px] border border-white/70 bg-white/85 p-5 shadow-[0_12px_32px_rgba(15,23,42,0.06)] backdrop-blur">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
        {label}
      </p>
      <p className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
        {value}
      </p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{hint}</p>
    </div>
  )
}

export function TimelineItem({ time, title, type }: TimelineEntry) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-[24px] border border-slate-200/80 bg-white/85 px-5 py-4 shadow-[0_10px_24px_rgba(15,23,42,0.05)]">
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

export function TaskItem({ title, deadline, priority }: TaskData) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100/90 py-4 last:border-b-0 last:pb-0 first:pt-0">
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

export function EmptyStateCard({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="rounded-[28px] border border-white/70 bg-white/90 p-6 shadow-[0_10px_28px_rgba(15,23,42,0.05)]">
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

export function PlanItemCard({
  item,
  tone,
}: {
  item: PlanItemData
  tone: PlanTone
}) {
  const toneClasses = getToneClasses(tone)

  return (
    <div className="rounded-[24px] border border-white/70 bg-white/90 p-4 shadow-[0_8px_20px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-700">{item.time}</p>
          <p className="mt-2 text-base font-semibold text-slate-900">{item.title}</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${toneClasses.badge}`}
        >
          {item.label}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-500">{item.detail}</p>
    </div>
  )
}

export function PlanDrawer({
  section,
  defaultOpen = false,
}: {
  section: PlanDrawerData
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  const toneClasses = getToneClasses(section.tone)

  return (
    <section className="rounded-[30px] border border-white/70 bg-white/88 shadow-[0_18px_40px_rgba(15,23,42,0.06)] backdrop-blur">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-start justify-between gap-4 px-6 py-5 text-left"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <span className={`h-2.5 w-2.5 rounded-full ${toneClasses.dot}`} />
            <p className={`text-xs font-semibold uppercase tracking-[0.18em] ${toneClasses.accent}`}>
              {section.hint}
            </p>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h3 className="text-xl font-semibold tracking-tight text-slate-900">
              {section.title}
            </h3>
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${toneClasses.badge}`}
            >
              {section.items.length} 项
            </span>
          </div>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
            {section.summary}
          </p>
        </div>
        <span
          className={`mt-1 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-500 transition ${
            open ? 'rotate-180' : ''
          }`}
        >
          ˅
        </span>
      </button>

      {open ? (
        <div className="border-t border-slate-100 px-6 py-5">
          <div className={`rounded-[26px] ${toneClasses.surface} p-4`}>
            <div className="grid gap-3 xl:grid-cols-2">
              {section.items.map((item) => (
                <PlanItemCard key={`${section.id}-${item.time}-${item.title}`} item={item} tone={section.tone} />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
