"use client";

import { useState, useEffect, useRef } from "react";
import { Search, X, Check, SlidersHorizontal, Plus } from "lucide-react";

interface FigureItem {
  name: string;
  slug: string;
  born_year: number | null;
  died_year: number | null;
  origin: string | null;
  featured: boolean;
}

interface FiguresResponse {
  items: FigureItem[];
  total: number;
  page: number;
  page_size: number;
}

interface FilterMeta {
  eras: string[];
  origins: string[];
  tags: string[];
}

interface ActiveFilters {
  eras: string[];
  origins: string[];
  tags: string[];
  yearMin: string;
  yearMax: string;
}

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

const PAGE_SIZE = 20;

function formatYear(year: number): string {
  return year < 0 ? `${Math.abs(year)} BC` : `${year}`;
}

function formatEra(born: number | null, died: number | null): string {
  if (born == null && died == null) return "Unknown";
  if (born == null) return `d. ${formatYear(died!)}`;
  if (died == null) return `b. ${formatYear(born)}`;
  return `${formatYear(born)}–${formatYear(died)}`;
}

function FigureCard({ name, slug, born_year, died_year, origin }: FigureItem) {
  return (
    <a
      href={`/generate?figure=${encodeURIComponent(name)}&slug=${slug}`}
      className="bg-cream p-6 hover:bg-parchment transition-colors duration-150 group"
    >
      <p className="font-serif text-base font-semibold text-dark group-hover:text-gold transition-colors duration-150">
        {name}
      </p>
      <p className="font-sans text-xs text-dark/50 mt-1">
        {formatEra(born_year, died_year)}
      </p>
      <p className="font-sans text-[10px] tracking-wider text-dark/40 mt-0.5 uppercase">
        {origin ?? ""}
      </p>
    </a>
  );
}

function FilterCheckbox({
  label,
  checked,
  onToggle,
}: {
  label: string;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-2.5 group w-full text-left py-0.5"
    >
      <span
        className={`w-3.5 h-3.5 border shrink-0 flex items-center justify-center transition-colors ${
          checked
            ? "bg-gold border-gold"
            : "border-dark/25 group-hover:border-dark/50"
        }`}
      >
        {checked && <Check size={9} className="text-cream" strokeWidth={3} />}
      </span>
      <span
        className={`font-sans text-xs transition-colors capitalize ${
          checked ? "text-dark/80" : "text-dark/50 group-hover:text-dark/70"
        }`}
      >
        {label}
      </span>
    </button>
  );
}

function FilterSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="px-4 py-4 border-b border-dark/10 last:border-0">
      <p className="text-[9px] font-sans tracking-[0.2em] text-dark/40 uppercase mb-3">
        {title}
      </p>
      {children}
    </div>
  );
}

interface AddFigureForm {
  name: string;
  description: string;
  born_year: string;
  died_year: string;
  era: string;
  origin: string;
  tags: string;
  featured: boolean;
}

const EMPTY_FORM: AddFigureForm = {
  name: "",
  description: "",
  born_year: "",
  died_year: "",
  era: "",
  origin: "",
  tags: "",
  featured: false,
};

function AddFigureModal({
  onClose,
  onAdded,
}: {
  onClose: () => void;
  onAdded: (figure: FigureItem) => void;
}) {
  const [form, setForm] = useState<AddFigureForm>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set(key: keyof AddFigureForm, value: string | boolean) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/figures`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          description: form.description.trim() || null,
          born_year: form.born_year !== "" ? Number(form.born_year) : null,
          died_year: form.died_year !== "" ? Number(form.died_year) : null,
          era: form.era.trim() || null,
          origin: form.origin.trim() || null,
          tags: form.tags.trim() || null,
          featured: form.featured,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Failed to create figure.");
      }
      const created: FigureItem = await res.json();
      onAdded(created);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-dark/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-cream w-full max-w-lg mx-4 border border-dark/15 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-dark/10">
          <h2 className="font-serif text-lg font-semibold text-dark">
            Add Historical Figure
          </h2>
          <button
            onClick={onClose}
            className="text-dark/40 hover:text-dark/70 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Name — required */}
          <div>
            <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
              Name <span className="text-gold">*</span>
            </label>
            <input
              required
              type="text"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="e.g. Cleopatra VII"
              className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
              Description
            </label>
            <textarea
              rows={2}
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="Brief biography…"
              className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors resize-none"
            />
          </div>

          {/* Born / Died years */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
                Born Year
              </label>
              <input
                type="number"
                value={form.born_year}
                onChange={(e) => set("born_year", e.target.value)}
                placeholder="e.g. −69 for BC"
                className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors"
              />
            </div>
            <div>
              <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
                Died Year
              </label>
              <input
                type="number"
                value={form.died_year}
                onChange={(e) => set("died_year", e.target.value)}
                placeholder="e.g. −30 for BC"
                className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors"
              />
            </div>
          </div>

          {/* Era / Origin */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
                Era
              </label>
              <input
                type="text"
                value={form.era}
                onChange={(e) => set("era", e.target.value)}
                placeholder="e.g. Ancient Egypt"
                className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors"
              />
            </div>
            <div>
              <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
                Origin
              </label>
              <input
                type="text"
                value={form.origin}
                onChange={(e) => set("origin", e.target.value)}
                placeholder="e.g. Egypt"
                className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors"
              />
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-[10px] font-sans tracking-[0.15em] text-dark/50 uppercase mb-1.5">
              Tags
            </label>
            <input
              type="text"
              value={form.tags}
              onChange={(e) => set("tags", e.target.value)}
              placeholder="e.g. ruler, military (comma-separated)"
              className="w-full bg-cream border border-dark/20 px-3 py-2 font-sans text-sm text-dark placeholder:text-dark/30 outline-none focus:border-dark/50 transition-colors"
            />
          </div>

          {/* Featured */}
          <button
            type="button"
            onClick={() => set("featured", !form.featured)}
            className="flex items-center gap-2.5 group"
          >
            <span
              className={`w-3.5 h-3.5 border shrink-0 flex items-center justify-center transition-colors ${
                form.featured
                  ? "bg-gold border-gold"
                  : "border-dark/25 group-hover:border-dark/50"
              }`}
            >
              {form.featured && (
                <Check size={9} className="text-cream" strokeWidth={3} />
              )}
            </span>
            <span className="font-sans text-xs text-dark/60">
              Mark as featured
            </span>
          </button>

          {error && (
            <p className="font-sans text-xs text-red-600">{error}</p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="font-sans text-sm text-dark/50 hover:text-dark transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !form.name.trim()}
              className="font-sans text-sm bg-dark text-cream px-5 py-2 hover:bg-dark/80 transition-colors disabled:opacity-40"
            >
              {submitting ? "Adding…" : "Add Figure"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const EMPTY_FILTERS: ActiveFilters = {
  eras: [],
  origins: [],
  tags: [],
  yearMin: "",
  yearMax: "",
};

export default function FiguresGrid({ featured }: { featured: FigureItem[] }) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [addedFigures, setAddedFigures] = useState<FigureItem[]>([]);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<ActiveFilters>(EMPTY_FILTERS);
  const [filterMeta, setFilterMeta] = useState<FilterMeta | null>(null);

  const [results, setResults] = useState<FigureItem[] | null>(null);
  const [resultsLoading, setResultsLoading] = useState(false);

  const [extra, setExtra] = useState<FigureItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState<number | null>(null);
  const [loadMoreLoading, setLoadMoreLoading] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isFiltered =
    query.trim().length > 0 ||
    filters.eras.length > 0 ||
    filters.origins.length > 0 ||
    filters.tags.length > 0 ||
    filters.yearMin !== "" ||
    filters.yearMax !== "";

  const hasActiveFilters =
    filters.eras.length > 0 ||
    filters.origins.length > 0 ||
    filters.tags.length > 0 ||
    filters.yearMin !== "" ||
    filters.yearMax !== "";

  // Fetch filter options on mount
  useEffect(() => {
    fetch(`${BACKEND_URL}/api/figures/meta`)
      .then((r) => r.json())
      .then((data) => setFilterMeta(data))
      .catch(() => {});
  }, []);

  // Debounced fetch when any filter/search changes
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!isFiltered) {
      setResults(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setResultsLoading(true);
      try {
        const params = new URLSearchParams({ page_size: "50" });
        if (query.trim()) params.set("q", query.trim());
        if (filters.eras.length) params.set("era", filters.eras.join(","));
        if (filters.origins.length)
          params.set("origin", filters.origins.join(","));
        if (filters.tags.length) params.set("tags", filters.tags.join(","));
        if (filters.yearMin) params.set("born_year_min", filters.yearMin);
        if (filters.yearMax) params.set("born_year_max", filters.yearMax);

        const res = await fetch(`${BACKEND_URL}/api/figures?${params}`);
        const data: FiguresResponse = await res.json();
        setResults(data.items);
      } finally {
        setResultsLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, filters, isFiltered]);

  function toggle(key: "eras" | "origins" | "tags", value: string) {
    setFilters((f) => {
      const list = f[key];
      return {
        ...f,
        [key]: list.includes(value)
          ? list.filter((v) => v !== value)
          : [...list, value],
      };
    });
  }

  function clearAll() {
    setQuery("");
    setFilters(EMPTY_FILTERS);
  }

  const allLoaded = total !== null && extra.length >= total;

  async function loadMore() {
    setLoadMoreLoading(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/figures?featured=false&page=${page}&page_size=${PAGE_SIZE}`
      );
      const data: FiguresResponse = await res.json();
      setExtra((prev) => [...prev, ...data.items]);
      setTotal(data.total);
      setPage((prev) => prev + 1);
    } finally {
      setLoadMoreLoading(false);
    }
  }

  const displayItems = isFiltered ? results ?? [] : [...featured, ...extra, ...addedFigures];

  return (
    <div>
      {showAddModal && (
        <AddFigureModal
          onClose={() => setShowAddModal(false)}
          onAdded={(fig) => setAddedFigures((prev) => [...prev, fig])}
        />
      )}

      {/* ── Shared header row: filters label + search bar ── */}
      <div className="flex gap-10 items-center mb-3">
        <div className="w-52 shrink-0 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={12} className="text-dark/40" />
            <span className="text-[9px] font-sans tracking-[0.2em] text-dark/40 uppercase">
              Filters
            </span>
          </div>
          {hasActiveFilters && (
            <button
              onClick={clearAll}
              className="text-[10px] font-sans text-gold hover:text-gold/70 transition-colors"
            >
              Clear all
            </button>
          )}
        </div>

        <div className="flex-1 min-w-0 flex items-center gap-4">
          <div className="relative max-w-sm flex-1">
            <Search
              size={14}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-dark/35 pointer-events-none"
            />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search figures…"
              className="w-full bg-cream border border-dark/20 pl-9 pr-9 py-2.5 font-sans text-sm text-dark placeholder:text-dark/35 outline-none focus:border-dark/50 transition-colors duration-150"
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-dark/35 hover:text-dark/60 transition-colors"
              >
                <X size={13} />
              </button>
            )}
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 font-sans text-sm text-dark/60 border border-dark/20 px-4 py-2.5 hover:border-dark/50 hover:text-dark transition-colors duration-150 shrink-0"
          >
            <Plus size={13} />
            Add Figure
          </button>
        </div>
      </div>

      {/* ── Two-column layout ── */}
      <div className="flex gap-10 items-start">
        {/* Left sidebar */}
        <aside className="w-52 shrink-0 sticky top-6">
          <div className="border border-dark/15 bg-cream">
            {filterMeta && filterMeta.eras.length > 0 && (
              <FilterSection title="Era">
                <div className="space-y-1.5 max-h-52 overflow-y-auto">
                  {filterMeta.eras.map((era) => (
                    <FilterCheckbox
                      key={era}
                      label={era}
                      checked={filters.eras.includes(era)}
                      onToggle={() => toggle("eras", era)}
                    />
                  ))}
                </div>
              </FilterSection>
            )}

            {filterMeta && filterMeta.origins.length > 0 && (
              <FilterSection title="Origin">
                <div className="space-y-1.5 max-h-52 overflow-y-auto">
                  {filterMeta.origins.map((origin) => (
                    <FilterCheckbox
                      key={origin}
                      label={origin}
                      checked={filters.origins.includes(origin)}
                      onToggle={() => toggle("origins", origin)}
                    />
                  ))}
                </div>
              </FilterSection>
            )}

            <FilterSection title="Born Year">
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={filters.yearMin}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, yearMin: e.target.value }))
                  }
                  placeholder="From"
                  className="w-full bg-cream border border-dark/15 px-2 py-1.5 font-sans text-xs text-dark placeholder:text-dark/30 outline-none focus:border-dark/40 transition-colors"
                />
                <span className="text-dark/30 text-xs shrink-0">–</span>
                <input
                  type="number"
                  value={filters.yearMax}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, yearMax: e.target.value }))
                  }
                  placeholder="To"
                  className="w-full bg-cream border border-dark/15 px-2 py-1.5 font-sans text-xs text-dark placeholder:text-dark/30 outline-none focus:border-dark/40 transition-colors"
                />
              </div>
              <p className="mt-1.5 font-sans text-[10px] text-dark/30">
                Use negative values for BC
              </p>
            </FilterSection>

            {filterMeta && filterMeta.tags.length > 0 && (
              <FilterSection title="Category">
                <div className="space-y-1.5 max-h-52 overflow-y-auto">
                  {filterMeta.tags.map((tag) => (
                    <FilterCheckbox
                      key={tag}
                      label={tag}
                      checked={filters.tags.includes(tag)}
                      onToggle={() => toggle("tags", tag)}
                    />
                  ))}
                </div>
              </FilterSection>
            )}
          </div>
        </aside>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {isFiltered && !resultsLoading && results !== null && (
            <p className="mb-4 font-sans text-xs text-dark/40 tracking-wide">
              {results.length} result{results.length !== 1 ? "s" : ""}
              {query.trim() ? ` for "${query.trim()}"` : ""}
            </p>
          )}

          {isFiltered && resultsLoading && (
            <div className="py-20 text-center font-sans text-sm text-dark/40">
              Loading…
            </div>
          )}

          {isFiltered && !resultsLoading && results?.length === 0 && (
            <div className="py-20 text-center">
              <p className="font-serif italic text-dark/40 text-sm">
                No figures match the current filters.
              </p>
              <button
                onClick={clearAll}
                className="mt-4 font-sans text-xs text-gold hover:text-gold/70 transition-colors"
              >
                Clear all filters
              </button>
            </div>
          )}

          {(!isFiltered || (!resultsLoading && (results?.length ?? 0) > 0)) && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-dark/10">
              {displayItems.map((f) => (
                <FigureCard key={f.slug} {...f} />
              ))}
            </div>
          )}

          {!isFiltered && !allLoaded && (
            <div className="mt-10 flex justify-center">
              <button
                onClick={loadMore}
                disabled={loadMoreLoading}
                className="font-sans text-sm text-dark/60 border border-dark/20 px-8 py-3 hover:border-dark/50 hover:text-dark transition-colors duration-150 disabled:opacity-40"
              >
                {loadMoreLoading ? "Loading..." : "Load More"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
