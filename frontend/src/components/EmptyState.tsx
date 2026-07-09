import type { LucideIcon } from 'lucide-react'

interface Props {
  icon: LucideIcon
  title: string
  description: string
  phaseNote: string
}

export default function EmptyState({ icon: Icon, title, description, phaseNote }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-12 text-center">
        <Icon className="size-8 text-muted-foreground" />
        <p className="max-w-md text-sm text-muted-foreground">{description}</p>
        <p className="max-w-md text-xs text-muted-foreground">{phaseNote}</p>
      </div>
    </div>
  )
}
