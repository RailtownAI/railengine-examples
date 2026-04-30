"use client";

import * as React from "react";
import { Plus, Receipt } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ExpenseList } from "@/components/expense-list";
import { ManualEntryDialog } from "@/components/manual-entry-dialog";
import { ReceiptDropzone } from "@/components/receipt-dropzone";
import { SummaryCard } from "@/components/summary-card";
import { ThemeToggle } from "@/components/theme-toggle";
import type { Expense } from "@/lib/schema";

export default function Home() {
  const [expenses, setExpenses] = React.useState<Expense[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [manualOpen, setManualOpen] = React.useState(false);

  const refetch = React.useCallback(async () => {
    try {
      const res = await fetch("/api/retrieve");
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error ?? `Retrieve failed (${res.status})`);
      }
      const data = (await res.json()) as Expense[];
      setExpenses(Array.isArray(data) ? data : []);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to load expenses",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refetch();
  }, [refetch]);

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch("/api/delete", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error ?? `Delete failed (${res.status})`);
      }
      toast.success("Expense deleted");
      await refetch();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to delete expense",
      );
    }
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 md:px-6">
          <div className="flex items-center gap-2.5">
            <Receipt
              className="h-5 w-5 shrink-0 text-emerald-600 drop-shadow-sm dark:text-emerald-400"
              strokeWidth={2.25}
              aria-hidden
            />
            <h1 className="bg-gradient-to-r from-emerald-900 via-emerald-600 to-teal-500 bg-clip-text text-base font-semibold text-transparent sm:text-lg dark:bg-none dark:text-emerald-300">
              Railengine Expensify
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setManualOpen(true)}
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">Add manually</span>
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 p-4 md:p-6">
        <ReceiptDropzone onIngested={refetch} />
        <SummaryCard expenses={expenses} />
        <ExpenseList
          expenses={expenses}
          loading={loading}
          onDelete={handleDelete}
        />
        <ManualEntryDialog
          open={manualOpen}
          onOpenChange={setManualOpen}
          onIngested={refetch}
        />
      </main>
    </div>
  );
}
