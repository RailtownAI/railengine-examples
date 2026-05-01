"use client";

import * as React from "react";
import { Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ExpenseDetailSheet } from "@/components/expense-detail-sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Expense } from "@/lib/schema";

type Props = {
  expenses: Expense[];
  loading: boolean;
  onDelete: (id: string) => void | Promise<void>;
};

function selectExpenseHandlers(
  e: Expense,
  setSelected: (expense: Expense) => void,
) {
  return {
    onClick: () => {
      setSelected(e);
    },
    onKeyDown: (ev: React.KeyboardEvent) => {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        setSelected(e);
      }
    },
  };
}

export function ExpenseList({ expenses, loading, onDelete }: Props) {
  const [selected, setSelected] = React.useState<Expense | null>(null);
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-14 w-full animate-pulse rounded-lg bg-muted"
          />
        ))}
      </div>
    );
  }

  if (expenses.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-sm text-muted-foreground">
          No expenses yet — drop a receipt above.
        </p>
      </Card>
    );
  }

  const sorted = [...expenses].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
  );

  return (
    <>
      <ExpenseDetailSheet
        expense={selected}
        onClose={() => setSelected(null)}
      />
      <div className="hidden md:block">
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Vendor</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="w-12" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((e) => (
                <TableRow
                  key={e.id}
                  className="cursor-pointer"
                  tabIndex={0}
                  {...selectExpenseHandlers(e, setSelected)}
                >
                  <TableCell className="font-medium">{e.vendor}</TableCell>
                  <TableCell>{formatDate(e.date)}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="capitalize">
                      {e.category}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCurrency(e.amount, e.currency)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Delete ${e.vendor}`}
                      onClick={(ev) => {
                        ev.stopPropagation();
                        void onDelete(e.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </div>

      <div className="space-y-2 md:hidden">
        {sorted.map((e) => (
          <Card
            key={e.id}
            role="button"
            tabIndex={0}
            className="relative cursor-pointer p-4 outline-none transition-colors hover:bg-accent/30 focus-visible:ring-2 focus-visible:ring-ring"
            {...selectExpenseHandlers(e, setSelected)}
          >
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Delete ${e.vendor}`}
              className="absolute right-2 top-2"
              onClick={(ev) => {
                ev.stopPropagation();
                void onDelete(e.id);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <div className="flex items-baseline justify-between gap-2 pr-8">
              <p className="font-medium">{e.vendor}</p>
              <p className="text-sm font-semibold tabular-nums">
                {formatCurrency(e.amount, e.currency)}
              </p>
            </div>
            <div className="mt-1 flex items-center justify-between gap-2">
              <p className="text-xs text-muted-foreground">
                {formatDate(e.date)}
              </p>
              <Badge variant="secondary" className="capitalize">
                {e.category}
              </Badge>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
