"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const NAV_LINKS = [
  { label: "CREATE", href: "/generate" },
  { label: "GALLERY", href: "/gallery" },
  { label: "FIGURES", href: "/figures" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`sticky top-0 z-50 bg-cream transition-shadow duration-200 ${
        scrolled ? "shadow-sm" : ""
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-5 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="font-serif text-xl leading-none">
          <span className="text-dark font-normal">Chrono</span>
          <span className="text-gold italic font-semibold">Canvas</span>
          <span className="text-dark font-normal">AI</span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-10">
          {NAV_LINKS.map(({ label, href }) => (
            <Link
              key={label}
              href={href}
              className="text-[11px] font-sans font-medium tracking-[0.18em] text-dark/60 hover:text-dark transition-colors duration-150"
            >
              {label}
            </Link>
          ))}
        </div>

        {/* CTA */}
        <Link
          href="/generate"
          className="bg-dark text-cream text-[11px] font-sans font-semibold tracking-[0.18em] px-5 py-2.5 hover:bg-dark/80 transition-colors duration-150"
        >
          TRY FREE
        </Link>
      </div>
    </nav>
  );
}
