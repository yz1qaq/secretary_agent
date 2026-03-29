import { ReactNode } from 'react'

import { PriorityLevel, StatCardData, TaskData, TimelineEntry } from './types'

function getPriorityClasses(priority: PriorityLevel): string {
  if (priority === '高') {
    return 'bg-red-50 text-red-600 ring-1 ring-inset ring-red-200'
  }
  if (priority === '中') {
    return 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200'
  }
  return 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200'
}

function getTimelineTagClasses(type: TimelineEntry['type']): string {
  return type === '固定安排'
    ? 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200'
    : 'bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-200'
}

export function StatCard({ label, value, hint }: StatCardData) {
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

export function TimelineItem({ time, title, type }: TimelineEntry) {
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

export function TaskItem({ title, deadline, priority }: TaskData) {
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
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

