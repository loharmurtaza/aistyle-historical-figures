export default function Footer() {
  return (
    <footer className="bg-cream border-t border-dark/10 py-7">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 flex flex-col sm:flex-row justify-between items-center gap-3">
        <p className="text-xs font-sans text-dark/50">
          Powered by{" "}
          <span className="text-gold font-medium">DALL·E 3 + GPT-4o-mini</span>
        </p>
      </div>
    </footer>
  );
}
