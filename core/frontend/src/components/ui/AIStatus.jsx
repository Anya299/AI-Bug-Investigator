export default function AIStatus() {
  return (
    <div
      className="
      inline-flex
      items-center
      gap-3
      rounded-full
      px-4
      py-2
      bg-aiSoft
      border
      border-ai/20
      text-ai
      font-mono
      text-sm
      "
    >
      <span
        className="
        h-2.5
        w-2.5
        rounded-full
        bg-ai
        animate-pulseAI
        "
      />

      AI ENGINE ONLINE
    </div>
  );
}