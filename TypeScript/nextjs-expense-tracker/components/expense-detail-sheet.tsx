"use client";

import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { Expense } from "@/lib/schema";
import { formatCurrency, formatDate } from "@/lib/utils";

type Props = {
  expense: Expense | null;
  onClose: () => void;
  /** When set, shows match % badge (e.g. search results). */
  relevancePercent?: number;
  relevanceTitle?: string;
};

export function ExpenseDetailSheet({
  expense,
  onClose,
  relevancePercent,
  relevanceTitle,
}: Props) {
  return (
    <Sheet open={!!expense} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-md">
        {expense ? (
          <>
            <SheetHeader className="space-y-1 border-b border-border pb-4 text-left">
              <SheetTitle className="pr-8">{expense.vendor}</SheetTitle>
              <SheetDescription asChild>
                <div className="flex flex-wrap items-center gap-2 text-left">
                  <span className="text-base font-semibold tabular-nums text-foreground">
                    {formatCurrency(expense.amount, expense.currency)}
                  </span>
                  <span className="text-muted-foreground">·</span>
                  <span>{formatDate(expense.date)}</span>
                  <Badge variant="secondary" className="capitalize">
                    {expense.category}
                  </Badge>
                  {relevancePercent !== undefined ? (
                    <Badge
                      variant="outline"
                      className="tabular-nums"
                      title={relevanceTitle}
                    >
                      {relevancePercent}% match
                    </Badge>
                  ) : null}
                </div>
              </SheetDescription>
            </SheetHeader>

            <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto py-4">
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Line items
                </p>
                <ul className="space-y-2 rounded-md border border-border bg-muted/30 p-3">
                  {expense.lineItems.map((line, i) => (
                    <li
                      key={`${expense.id}-line-${i}`}
                      className="flex justify-between gap-2 text-sm"
                    >
                      <span className="text-muted-foreground">
                        {line.description}
                      </span>
                      <span className="shrink-0 tabular-nums">
                        {formatCurrency(line.price, expense.currency)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Tax</p>
                  <p className="font-medium tabular-nums">
                    {formatCurrency(expense.tax, expense.currency)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Tip</p>
                  <p className="font-medium tabular-nums">
                    {formatCurrency(expense.tip, expense.currency)}
                  </p>
                </div>
              </div>

              <p className="text-xs text-muted-foreground">
                ID:{" "}
                <code className="rounded bg-muted px-1 py-0.5 text-[0.7rem]">
                  {expense.id}
                </code>
              </p>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
