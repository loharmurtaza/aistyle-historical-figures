"use client";

import { useState } from "react";
import Image from "next/image";
import { ArrowRight, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { STYLES } from "@/lib/constants";
import StyleButton from "@/components/ui/StyleButton";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import type { GenerateResponse } from "@/types";

interface PortraitComposerProps {
  initialPrompt?: string;
  initialStyle?: string;
}

export default function PortraitComposer({
  initialPrompt = "",
  initialStyle = "",
}: PortraitComposerProps) {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [selectedStyle, setSelectedStyle] = useState(initialStyle);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [aiEnhance, setAiEnhance] = useState(true);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);
    setShowPrompt(false);

    try {
      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";
      const res = await fetch(`${backendUrl}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          figure: prompt,
          style: selectedStyle,
          enhance: aiEnhance,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || data.detail || "Generation failed");
      }

      const data: GenerateResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="bg-cream py-16 px-6 lg:px-10">
      {/* Section divider */}
      <div className="max-w-5xl mx-auto flex items-center gap-6 mb-12">
        <span className="flex-1 h-px bg-dark/15" />
        <span className="text-[10px] font-sans tracking-[0.22em] text-dark/50">
          COMPOSE YOUR PORTRAIT
        </span>
        <span className="flex-1 h-px bg-dark/15" />
      </div>

      {/* Composer card */}
      <div className="max-w-5xl mx-auto border border-dark/20 bg-cream">
        {/* Card header */}
        <div className="flex items-center justify-between px-7 py-4 border-b border-dark/15">
          <span className="text-[10px] font-sans tracking-[0.18em] text-dark/55">
            YOUR PROMPT
          </span>
          {/* AI Enhance toggle */}
          <button
            onClick={() => setAiEnhance((v) => !v)}
            className="flex items-center gap-2 group"
            title={
              aiEnhance
                ? "AI adds creative details — click to switch to format-only"
                : "AI formats without adding new ideas — click to enable enhancement"
            }
          >
            {/* pill track */}
            <span
              className={`relative inline-flex w-8 h-4 rounded-full transition-colors duration-200 ${
                aiEnhance ? "bg-gold" : "bg-dark/20"
              }`}
            >
              <motion.span
                animate={{ x: aiEnhance ? 16 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 35 }}
                className="absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-cream shadow-sm"
              />
            </span>
            <span
              className={`text-[11px] font-sans transition-colors duration-150 ${
                aiEnhance ? "text-gold" : "text-dark/40"
              }`}
            >
              {aiEnhance ? "AI Enhanced prompt" : "Format only"}
            </span>
          </button>
        </div>

        {/* Textarea */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. Napoleon Bonaparte standing on a misty battlefield, oil painting..."
          rows={5}
          className="w-full bg-transparent px-7 py-6 font-serif italic text-dark/70 placeholder:text-dark/35 text-base resize-none outline-none"
        />

        {/* Card footer */}
        <div className="flex items-center justify-between px-7 py-4 border-t border-dark/15">
          {/* Style buttons */}
          <div className="flex flex-wrap gap-2">
            {STYLES.map((style) => (
              <StyleButton
                key={style.id}
                label={style.label}
                isActive={selectedStyle === style.id}
                onClick={() =>
                  setSelectedStyle(
                    selectedStyle === style.id && style.id !== "" ? "" : style.id
                  )
                }
              />
            ))}
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={isLoading || !prompt.trim()}
            className="flex items-center gap-2 bg-dark text-cream text-xs font-sans font-semibold tracking-[0.18em] px-7 py-3 hover:bg-dark/80 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ml-4"
          >
            {isLoading ? (
              <>
                <LoadingSpinner size={14} className="text-gold" />
                <span>GENERATING</span>
              </>
            ) : (
              <>
                <span>GENERATE</span>
                <ArrowRight size={14} />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loading shimmer */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            key="shimmer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="max-w-5xl mx-auto mt-8"
          >
            <div className="w-full max-w-lg mx-auto aspect-square border border-dark/10 overflow-hidden relative">
              <motion.div
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 bg-gradient-to-r from-transparent via-dark/5 to-transparent skew-x-12"
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                <LoadingSpinner size={32} className="text-gold" />
                <p className="font-serif italic text-dark/40 text-sm">
                  Rendering your portrait…
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="max-w-5xl mx-auto mt-4 px-5 py-3 border border-red-200 bg-red-50 text-red-700 text-sm font-sans"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result — Framer Motion reveal */}
      <AnimatePresence>
        {result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.96, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-5xl mx-auto mt-8 border border-dark/15 p-6"
          >
            {/* Portrait title */}
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="max-w-lg mx-auto mb-4 flex items-center justify-between"
            >
              <h3 className="font-serif text-dark text-lg leading-tight">
                {result.figure_title}
              </h3>
              <span className="text-[10px] font-sans tracking-[0.18em] text-dark/45 uppercase">
                {result.style}
              </span>
            </motion.div>

            <div className="relative aspect-square w-full max-w-lg mx-auto overflow-hidden">
              {/* Image slides up into view */}
              <motion.div
                className="relative w-full h-full"
                initial={{ y: "4%", opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                <Image
                  src={result.image_url}
                  alt={result.figure_title}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, 512px"
                />
              </motion.div>
            </div>

            {/* Collapsible revised prompt */}
            {result.revised_prompt && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="max-w-lg mx-auto mt-3"
              >
                <button
                  onClick={() => setShowPrompt((v) => !v)}
                  className="flex items-center gap-1.5 text-[11px] font-sans text-dark/40 hover:text-dark/60 transition-colors duration-150 mx-auto"
                >
                  <span>{showPrompt ? "Hide prompt" : "Show prompt"}</span>
                  <motion.span
                    animate={{ rotate: showPrompt ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex items-center"
                  >
                    <ChevronDown size={12} />
                  </motion.span>
                </button>
                <AnimatePresence>
                  {showPrompt && (
                    <motion.p
                      key="prompt-text"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: "easeInOut" }}
                      className="overflow-hidden mt-2 text-xs font-sans text-dark/45 text-center leading-relaxed"
                    >
                      {result.revised_prompt}
                    </motion.p>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
