export default function GlowOrb({
  className=""
}) {

  return (
    <div
      className={`
      absolute
      rounded-full
      blur-3xl
      bg-ai/20
      animate-float
      ${className}
      `}
    />
  );
}