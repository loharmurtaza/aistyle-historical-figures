import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export default function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center font-sans font-medium tracking-widest uppercase transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: "bg-dark text-cream hover:bg-dark/80",
    secondary:
      "bg-transparent border border-gold text-gold hover:bg-gold hover:text-dark",
    ghost: "bg-transparent text-gold hover:text-gold/70",
  };

  const sizes = {
    sm: "text-xs px-4 py-2",
    md: "text-xs px-6 py-3",
    lg: "text-sm px-8 py-4",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
