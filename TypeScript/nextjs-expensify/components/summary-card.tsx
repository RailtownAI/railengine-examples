"use client";

import * as React from "react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";
import type { Expense } from "@/lib/schema";

type Props = {
  expenses: Expense[];
};

export function SummaryCard({ expenses }: Props) {
  if (expenses.length === 0) return null;

  const totalsByCurrency = new Map<string, number>();
  const byCategoryByCurrency = new Map<string, Map<string, number>>();

  for (const e of expenses) {
    totalsByCurrency.set(
      e.currency,
      (totalsByCurrency.get(e.currency) ?? 0) + e.amount,
    );
    const inner =
      byCategoryByCurrency.get(e.currency) ?? new Map<string, number>();
    inner.set(e.category, (inner.get(e.category) ?? 0) + e.amount);
    byCategoryByCurrency.set(e.currency, inner);
  }

  const currencies = Array.from(totalsByCurrency.keys()).sort();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {currencies.map((currency) => {
          const total = totalsByCurrency.get(currency) ?? 0;
          const byCategory = Array.from(
            (byCategoryByCurrency.get(currency) ?? new Map()).entries(),
          ).sort(([, a], [, b]) => (b as number) - (a as number));

          return (
            <div key={currency} className="space-y-3">
              <div className="flex items-baseline justify-between">
                <p className="text-sm text-muted-foreground">
                  Total ({currency})
                </p>
                <p className="text-2xl font-semibold tabular-nums">
                  {formatCurrency(total, currency)}
                </p>
              </div>
              <div className="space-y-1.5">
                {byCategory.map(([cat, amount]) => {
                  const pct = total > 0 ? ((amount as number) / total) * 100 : 0;
                  return (
                    <div key={cat as string} className="space-y-1">
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="capitalize">{cat as string}</span>
                        <span className="tabular-nums text-muted-foreground">
                          {formatCurrency(amount as number, currency)}
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-primary"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
