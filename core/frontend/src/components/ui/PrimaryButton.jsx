export default function PrimaryButton({
  children,
  onClick,
  disabled=false
}) {

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className="
      rounded-xl
      px-8
      py-3
      font-semibold
      text-black
      bg-ai
      transition
      hover:shadow-aiGlow
      disabled:opacity-50
      "
    >
      {children}
    </button>
  );
}