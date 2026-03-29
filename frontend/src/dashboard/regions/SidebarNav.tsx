/* eslint-disable react-refresh/only-export-components */

import { NavItemData, NavigationKey } from '../types'

export const sidebarNavItems: NavItemData[] = [
  { key: 'dashboard', label: '今日计划' },
  { key: 'today', label: '学习' },
  { key: 'tasks', label: '生活' },
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
        {navItems.map((item) => {
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
