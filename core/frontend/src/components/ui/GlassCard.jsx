export default function GlassCard({
  children,
  className = ""
}) {
  return (
    <div
      className={`
        rounded-3xl
        border
        border-traceBorder
        bg-tracePanel/70
        backdrop-blur-glass
        shadow-glass
        ${className}
      `}
    >
      {children}
    </div>
  );
}