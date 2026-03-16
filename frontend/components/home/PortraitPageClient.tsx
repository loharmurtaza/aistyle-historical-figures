"use client";

import { useState } from "react";
import PortraitComposer from "./PortraitComposer";
import QuickStartTemplates from "./QuickStartTemplates";
import type { Template } from "@/types";

export default function PortraitPageClient() {
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
    // Scroll to composer
    document
      .getElementById("composer")
      ?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      <div id="composer">
        <PortraitComposer
          initialPrompt={
            selectedTemplate
              ? `${selectedTemplate.figure} in ${selectedTemplate.style} style`
              : ""
          }
          initialStyle={selectedTemplate?.style ?? "renaissance"}
          key={selectedTemplate?.displayLabel ?? "default"}
        />
      </div>
      <QuickStartTemplates onSelect={handleTemplateSelect} />
    </>
  );
}
