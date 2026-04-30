"use client";

import * as React from "react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ExpenseForm } from "@/components/expense-form";
import type { ExtractedExpense } from "@/lib/schema";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIngested: () => void | Promise<void>;
};

export function ManualEntryDialog({ open, onOpenChange, onIngested }: Props) {
  const [submitting, setSubmitting] = React.useState(false);

  const handleSubmit = async (data: ExtractedExpense) => {
    setSubmitting(true);
    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error ?? `Ingest failed (${res.status})`);
      }
      toast.success("Expense added");
      onOpenChange(false);
      await onIngested();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add expense");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add expense</DialogTitle>
          <DialogDescription>
            Enter expense details manually.
          </DialogDescription>
        </DialogHeader>
        <ExpenseForm
          submitLabel="Save expense"
          submitting={submitting}
          onSubmit={handleSubmit}
        />
      </DialogContent>
    </Dialog>
  );
}
