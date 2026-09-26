import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-md px-2.5 py-0.5 text-xs font-mono font-medium transition-colors border select-none",
  {
    variants: {
      variant: {
        default:
          "border-border bg-surface-raised text-foreground",
        secondary:
          "border-border/60 bg-surface text-muted",
        outline:
          "border-border text-foreground bg-transparent",
        // Severity Levels
        critical:
          "border-severity-critical/40 bg-severity-critical/10 text-severity-critical font-semibold",
        high:
          "border-severity-high/40 bg-severity-high/10 text-severity-high font-semibold",
        medium:
          "border-severity-medium/40 bg-severity-medium/10 text-severity-medium font-semibold",
        low:
          "border-severity-low/40 bg-severity-low/10 text-severity-low",
        // Compliance States
        pass:
          "border-compliance-pass/40 bg-compliance-pass/10 text-compliance-pass font-bold tracking-wide",
        warn:
          "border-compliance-warn/40 bg-compliance-warn/10 text-compliance-warn font-bold tracking-wide",
        fail:
          "border-compliance-fail/40 bg-compliance-fail/10 text-compliance-fail font-bold tracking-wide",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
