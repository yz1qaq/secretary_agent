/* eslint-disable react-refresh/only-export-components */

import { lifeTodayPlan } from './LifePanel'
import { studyTodayPlan } from './StudyPanel'
import { EmptyStateCard, PlanItemCard, StatCard } from '../ui'
import { StatCardData, WorkspaceCopy } from '../types'

export const todayPlanWorkspaceCopy: WorkspaceCopy = {
  eyebrow: 'Today Snapshot',
  title: '今日计划',
  subtitle: '这里只保留今天必须执行的学习与生活安排，帮助你在一屏里看清当天节奏。',
}

function buildTodayPlanCards(): StatCardData[] {
  return [
    {
      label: '今日学习',
      value: `${studyTodayPlan.items.length} 项`,
      hint: '课程收尾、阅读摘录与明日预热是今天的学习主线。',
    },
    {
      label: '今日生活',
      value: `${lifeTodayPlan.items.length} 项`,
      hint: '保持运动、洗漱和睡前收束，让晚上不被打散。',
    },
    {
      label: '今日关键词',
      value: '稳住节奏',
      hint: '学习区先落地，生活区负责恢复与续航。',
    },
  ]
}

export function TodayPlanPanel() {
  const todayPlanCards = buildTodayPlanCards()

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(238,242,255,0.9))] p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-indigo-700">
          Daily Focus
        </p>
        <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-2xl">
            <h2 className="text-3xl font-semibold tracking-tight text-slate-900">
              今天不追求面面俱到，只把该做的学习和生活安排清晰摆出来。
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              今日计划是学习区和生活区中“今天部分”的聚合视图。明天和长期事项留在各自分区里，不在这里重复堆叠。
            </p>
          </div>
          <div className="rounded-[28px] border border-white/80 bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(15,23,42,0.05)]">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              今日建议
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              先把学习区的收尾完成，再切换到运动和睡前恢复，别让节奏在夜里继续拉长。
            </p>
          </div>
        </div>
      </section>

      <section>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {todayPlanCards.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-[30px] border border-white/70 bg-white/88 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-500" />
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
              今日学习计划
            </p>
          </div>
          <h3 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
            {studyTodayPlan.title}
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            {studyTodayPlan.summary}
          </p>
          <div className="mt-5 grid gap-3">
            {studyTodayPlan.items.map((item) => (
              <PlanItemCard key={`study-today-${item.time}-${item.title}`} item={item} tone="study" />
            ))}
          </div>
        </div>

        <div className="rounded-[30px] border border-white/70 bg-white/88 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
              今日生活计划
            </p>
          </div>
          <h3 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
            {lifeTodayPlan.title}
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            {lifeTodayPlan.summary}
          </p>
          <div className="mt-5 grid gap-3">
            {lifeTodayPlan.items.map((item) => (
              <PlanItemCard key={`life-today-${item.time}-${item.title}`} item={item} tone="life" />
            ))}
          </div>
        </div>
      </section>

      <EmptyStateCard
        title="今日执行原则"
        description="今日计划只负责呈现当下要做的事情。如果需要看明天怎么接、长期目标怎么推进，请切换到学习区或生活区的对应抽屉。"
      />
    </div>
  )
}
