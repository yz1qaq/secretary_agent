/* eslint-disable react-refresh/only-export-components */

import { NavItemData, NavigationKey } from '../types'

export const sidebarNavItems: NavItemData[] = [
  { key: 'dashboard', label: '今日计划', caption: '只看今天要做的事' },
  { key: 'today', label: '学习', caption: '课程、自习与长期研究' },
  { key: 'tasks', label: '生活', caption: '习惯、恢复与日常节奏' },
]

export function SidebarNav({
  activeKey,
  items,
  onChange,
}: {
  activeKey: NavigationKey
  items?: NavItemData[]
  onChange: (key: NavigationKey) => void
}) {
  const navItems = items || sidebarNavItems

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-white/70 bg-[#fbfaf7] px-5 py-6 shadow-[inset_-1px_0_0_rgba(226,232,240,0.8)]">
      <div className="mb-8 rounded-[28px] border border-white/80 bg-white/80 p-5 shadow-[0_10px_24px_rgba(15,23,42,0.05)]">
        <p className="text-xs font-medium tracking-[0.18em] text-slate-400">
          工作区
        </p>
        <h1 className="mt-2 text-xl font-semibold tracking-tight text-slate-900">
          个人秘书 Agent
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          学习、生活与今日计划会在这里被整理成更轻的校园节奏板。
        </p>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = item.key === activeKey
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onChange(item.key)}
              className={`group flex w-full items-start gap-3 rounded-[24px] px-4 py-4 text-left transition ${
                isActive
                  ? 'bg-white text-slate-900 shadow-[0_12px_28px_rgba(15,23,42,0.07)]'
                  : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
              }`}
            >
              <span
                className={`mt-1 h-2.5 w-2.5 rounded-full transition ${
                  isActive ? 'bg-indigo-500' : 'bg-slate-300 group-hover:bg-slate-400'
                }`}
              />
              <span className="min-w-0">
                <span
                  className={`block text-sm font-semibold ${
                    isActive ? 'text-slate-900' : 'text-slate-700'
                  }`}
                >
                  {item.label}
                </span>
                {item.caption ? (
                  <span className="mt-1 block text-xs leading-5 text-slate-500">
                    {item.caption}
                  </span>
                ) : null}
              </span>
            </button>
          )
        })}
      </nav>

      <div className="mt-auto rounded-[28px] border border-dashed border-slate-200 bg-white/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
          Campus Note
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          今日计划只显示今天。想看明天和长期安排，去学习区和生活区的抽屉里展开查看。
        </p>
      </div>
    </aside>
  )
}
