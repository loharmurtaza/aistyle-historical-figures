"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
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

  const PAGE_SIZE = 20;
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

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
            <div className="aspect-square overflow-hidden bg-dark/5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${backendUrl}/api/gallery/${item.id}/image`}
                alt={item.figure}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
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
