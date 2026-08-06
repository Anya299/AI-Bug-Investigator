import { useEffect, useState } from "react";

/**
 * Fixed dot-nav on the right edge, one dot per slide. Uses an
 * IntersectionObserver scoped to the snap-scroll container (not the
 * window) to track which slide is currently active, and highlights it.
 * Clicking a dot scrolls that slide into view.
 */
export default function SectionNav({ sections, refs, containerRef }) {
  const [active, setActive] = useState(sections[0]?.id);

  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { root, threshold: 0.6 }
    );

    sections.forEach(({ id }) => {
      const node = refs[id]?.current;
      if (node) observer.observe(node);
    });

    return () => observer.disconnect();
  }, [sections, refs, containerRef]);

  return (
    <nav
      aria-label="Page sections"
      className="fixed right-6 top-1/2 z-50 hidden -translate-y-1/2 flex-col gap-4 sm:flex"
    >
      {sections.map((s) => (
        <button
          key={s.id}
          onClick={() =>
            refs[s.id]?.current?.scrollIntoView({ behavior: "smooth", block: "start" })
          }
          aria-label={s.label}
          className="group relative flex items-center justify-end"
        >
          <span
            className="
              mr-3 whitespace-nowrap rounded-md border border-line bg-tracePanel/90
              px-2 py-1 font-mono text-[10px] text-textSecondary opacity-0 backdrop-blur
              transition-opacity group-hover:opacity-100
            "
          >
            {s.label}
          </span>
          <span
            className={`
              h-2 w-2 rounded-full border transition-all duration-300
              ${active === s.id ? "scale-125 border-cyan bg-cyan" : "border-line bg-transparent"}
            `}
          />
        </button>
      ))}
    </nav>
  );
}