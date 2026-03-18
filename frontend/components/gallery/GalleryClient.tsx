"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, Maximize2, X } from "lucide-react";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

interface GalleryItem {
  id: number;
  figure: string;
  style: string;
  image_url: string;
  created_at: string;
}

interface GalleryResponse {
  items: GalleryItem[];
  total: number;
  page: number;
  page_size: number;
}

export default function GalleryClient() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightboxItem, setLightboxItem] = useState<GalleryItem | null>(null);

  const PAGE_SIZE = 20;
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

  async function handleDownload(item: GalleryItem) {
    const url = `${backendUrl}/api/gallery/${item.id}/image`;
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `${item.figure.replace(/\s+/g, "_")}_${item.style || "portrait"}.png`;
      a.click();
      URL.revokeObjectURL(objectUrl);
    } catch {
      window.open(url, "_blank");
    }
  }

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`${backendUrl}/api/gallery?page=${page}&page_size=${PAGE_SIZE}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load gallery");
        return r.json() as Promise<GalleryResponse>;
      })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, backendUrl]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 gap-3">
        <LoadingSpinner size={24} className="text-gold" />
        <span className="font-serif italic text-dark/40 text-sm">
          Loading portraits…
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-200 bg-red-50 text-red-700 text-sm font-sans px-5 py-3">
        {error}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="border border-dashed border-dark/25 py-24 text-center">
        <p className="font-serif italic text-dark/40 text-lg">
          No portraits yet.
        </p>
        <p className="font-sans text-dark/40 text-sm mt-2">
          Be the first to create one.
        </p>
        <a
          href="/generate"
          className="inline-block mt-6 bg-dark text-cream text-[11px] font-sans tracking-[0.18em] px-6 py-3 hover:bg-dark/80 transition-colors"
        >
          CREATE A PORTRAIT
        </a>
      </div>
    );
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {items.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.35 }}
            className="border border-dark/15 bg-cream overflow-hidden group"
          >
            {/* Image */}
            <div className="relative aspect-square overflow-hidden bg-dark/5 group/img">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${backendUrl}/api/gallery/${item.id}/image`}
                alt={item.figure}
                className="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-500"
              />

              {/* Hover overlay */}
              <div className="absolute inset-0 bg-dark/0 group-hover/img:bg-dark/35 transition-colors duration-200 flex items-end justify-end p-2.5 gap-2 opacity-0 group-hover/img:opacity-100">
                <button
                  onClick={() => setLightboxItem(item)}
                  className="flex items-center gap-1.5 bg-cream/90 hover:bg-cream text-dark text-[11px] font-sans px-3 py-2 transition-colors duration-150"
                  title="View full size"
                >
                  <Maximize2 size={12} />
                  <span>Full size</span>
                </button>
                <button
                  onClick={() => handleDownload(item)}
                  className="flex items-center gap-1.5 bg-gold/90 hover:bg-gold text-cream text-[11px] font-sans px-3 py-2 transition-colors duration-150"
                  title="Download image"
                >
                  <Download size={12} />
                  <span>Download</span>
                </button>
              </div>
            </div>

            {/* Meta */}
            <div className="px-4 py-3 border-t border-dark/10">
              <p className="font-serif text-dark text-sm leading-snug truncate">
                {item.figure}
              </p>
              <p className="text-[10px] font-sans tracking-[0.15em] text-dark/45 uppercase mt-0.5">
                {item.style}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Lightbox */}
      <AnimatePresence>
        {lightboxItem && (
          <motion.div
            key="lightbox"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-dark/80 backdrop-blur-sm p-4"
            onClick={() => setLightboxItem(null)}
          >
            <motion.div
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.92, opacity: 0 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="relative max-w-4xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Top bar */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="font-serif text-cream text-lg leading-tight">{lightboxItem.figure}</p>
                  {lightboxItem.style && (
                    <p className="text-[10px] font-sans tracking-[0.18em] text-cream/50 uppercase mt-0.5">{lightboxItem.style}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownload(lightboxItem)}
                    className="flex items-center gap-1.5 bg-gold/90 hover:bg-gold text-cream text-[11px] font-sans px-4 py-2 transition-colors duration-150"
                  >
                    <Download size={13} />
                    <span>Download</span>
                  </button>
                  <button
                    onClick={() => setLightboxItem(null)}
                    className="p-2 text-cream/60 hover:text-cream transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* Full image */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${backendUrl}/api/gallery/${lightboxItem.id}/image`}
                alt={lightboxItem.figure}
                className="w-full max-h-[80vh] object-contain"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-12">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="text-xs font-sans tracking-[0.15em] text-dark/60 hover:text-dark disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ← PREV
          </button>
          <span className="text-[11px] font-sans text-dark/40">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="text-xs font-sans tracking-[0.15em] text-dark/60 hover:text-dark disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            NEXT →
          </button>
        </div>
      )}
    </>
  );
}
