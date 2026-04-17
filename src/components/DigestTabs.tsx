interface Props {
  dates: string[]
  activeDate: string
  onSelect: (date: string) => void
}

function formatDate(iso: string) {
  const d = new Date(iso + 'T00:00:00')
  return {
    day: d.toLocaleDateString('en-US', { weekday: 'short' }),
    date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }
}

export default function DigestTabs({ dates, activeDate, onSelect }: Props) {
  return (
    <div className="border-b border-zinc-800 overflow-x-auto">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex gap-1 py-2">
          {dates.map((date, i) => {
            const { day, date: d } = formatDate(date)
            const isActive = date === activeDate
            const isToday = i === 0
            return (
              <button
                key={date}
                onClick={() => onSelect(date)}
                className={`
                  flex flex-col items-center px-4 py-2 rounded text-xs font-mono transition-all whitespace-nowrap
                  ${isActive
                    ? 'bg-brand-500/20 text-brand-400 border border-brand-500/40'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60 border border-transparent'
                  }
                `}
              >
                <span className="text-[10px] uppercase tracking-widest opacity-70">{day}</span>
                <span className="font-semibold">{d}</span>
                {isToday && (
                  <span className="text-[9px] text-brand-500 tracking-wider">TODAY</span>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
