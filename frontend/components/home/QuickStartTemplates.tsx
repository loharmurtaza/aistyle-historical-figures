"use client";

import { QUICK_START_TEMPLATES } from "@/lib/constants";
import type { Template } from "@/types";

interface QuickStartTemplatesProps {
  onSelect: (template: Template) => void;
}

export default function QuickStartTemplates({
  onSelect,
}: QuickStartTemplatesProps) {
  return (
    <section className="bg-cream px-6 lg:px-10 pb-16">
      <div className="max-w-5xl mx-auto">
        <p className="text-[10px] font-sans tracking-[0.2em] text-dark/50 mb-4">
          QUICK START TEMPLATES
        </p>
        <div className="flex flex-wrap gap-3">
          {QUICK_START_TEMPLATES.map((template) => (
            <button
              key={template.displayLabel}
              onClick={() => onSelect(template)}
              className="border border-dark/25 px-4 py-2.5 text-sm font-sans text-dark/75 hover:border-dark hover:text-dark transition-all duration-150 bg-cream"
            >
              <span className="font-medium">{template.figure}</span>
              <span className="text-dark/45 font-serif italic">
                {" "}
                · {template.style}
              </span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
