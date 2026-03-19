export default function Card({
  children,
  className = '',
  ...props
}: {
  children: React.ReactNode
  className?: string
  [key: string]: any
}) {
  return (
    <div
      className={`bg-slate-800 rounded-lg border border-slate-700 p-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
