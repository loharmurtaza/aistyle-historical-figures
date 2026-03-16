interface StyleButtonProps {
  label: string;
  isActive: boolean;
  onClick: () => void;
}

export default function StyleButton({
  label,
  isActive,
  onClick,
}: StyleButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-xs font-sans font-medium tracking-wider border transition-all duration-200 ${
        isActive
          ? "bg-dark text-cream border-dark"
          : "bg-transparent text-dark/70 border-dark/30 hover:border-dark/60 hover:text-dark"
      }`}
    >
      {label}
    </button>
  );
}
