"use client";

import * as React from "react";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CATEGORIES,
  type Category,
  type ExtractedExpense,
  type LineItem,
} from "@/lib/schema";

type Props = {
  initial?: ExtractedExpense | null;
  submitLabel?: string;
  submitting?: boolean;
  onSubmit: (data: ExtractedExpense) => Promise<void> | void;
};

const todayLocalDate = () => {
  const d = new Date();
  const tzOffsetMs = d.getTimezoneOffset() * 60_000;
  return new Date(d.getTime() - tzOffsetMs).toISOString().slice(0, 10);
};

const isoDateInputValue = (iso: string): string => {
  if (!iso) return todayLocalDate();
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return todayLocalDate();
    const tzOffsetMs = d.getTimezoneOffset() * 60_000;
    return new Date(d.getTime() - tzOffsetMs).toISOString().slice(0, 10);
  } catch {
    return todayLocalDate();
  }
};

const dateInputToIso = (value: string): string => {
  if (!value) return new Date().toISOString();
  const d = new Date(`${value}T00:00:00`);
  return d.toISOString();
};

export function ExpenseForm({
  initial,
  submitLabel = "Save expense",
  submitting = false,
  onSubmit,
}: Props) {
  const [vendor, setVendor] = React.useState(initial?.vendor ?? "");
  const [amount, setAmount] = React.useState<string>(
    initial?.amount != null ? String(initial.amount) : "",
  );
  const [currency, setCurrency] = React.useState(initial?.currency ?? "USD");
  const [date, setDate] = React.useState<string>(
    isoDateInputValue(initial?.date ?? ""),
  );
  const [category, setCategory] = React.useState<Category>(
    (initial?.category as Category) ?? "other",
  );
  const [tax, setTax] = React.useState<string>(
    initial?.tax != null ? String(initial.tax) : "0",
  );
  const [tip, setTip] = React.useState<string>(
    initial?.tip != null ? String(initial.tip) : "0",
  );
  const [lineItems, setLineItems] = React.useState<LineItem[]>(
    initial?.lineItems ?? [],
  );

  const updateLineItem = (idx: number, patch: Partial<LineItem>) => {
    setLineItems((prev) =>
      prev.map((li, i) => (i === idx ? { ...li, ...patch } : li)),
    );
  };

  const addLineItem = () =>
    setLineItems((prev) => [...prev, { description: "", price: 0 }]);

  const removeLineItem = (idx: number) =>
    setLineItems((prev) => prev.filter((_, i) => i !== idx));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      vendor: vendor.trim() || "Unknown",
      amount: Number(amount) || 0,
      currency: currency.trim().toUpperCase() || "USD",
      date: dateInputToIso(date),
      category,
      tax: Number(tax) || 0,
      tip: Number(tip) || 0,
      lineItems: lineItems.map((li) => ({
        description: li.description,
        price: Number(li.price) || 0,
      })),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="vendor">Vendor</Label>
          <Input
            id="vendor"
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            placeholder="Blue Bottle Coffee"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="date">Date</Label>
          <Input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="amount">Amount (total)</Label>
          <Input
            id="amount"
            type="number"
            inputMode="decimal"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="currency">Currency</Label>
          <Input
            id="currency"
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            placeholder="USD"
            maxLength={3}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="category">Category</Label>
          <Select
            value={category}
            onValueChange={(v) => setCategory(v as Category)}
          >
            <SelectTrigger id="category">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((c) => (
                <SelectItem key={c} value={c} className="capitalize">
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="tax">Tax</Label>
            <Input
              id="tax"
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              value={tax}
              onChange={(e) => setTax(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tip">Tip</Label>
            <Input
              id="tip"
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              value={tip}
              onChange={(e) => setTip(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Line items</Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={addLineItem}
          >
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </div>
        {lineItems.length === 0 ? (
          <p className="text-sm text-muted-foreground">No line items.</p>
        ) : (
          <div className="space-y-2">
            {lineItems.map((li, idx) => (
              <div key={idx} className="flex items-end gap-2">
                <div className="flex-1 space-y-1.5">
                  <Label htmlFor={`li-desc-${idx}`} className="sr-only">
                    Description
                  </Label>
                  <Input
                    id={`li-desc-${idx}`}
                    value={li.description}
                    onChange={(e) =>
                      updateLineItem(idx, { description: e.target.value })
                    }
                    placeholder="Description"
                  />
                </div>
                <div className="w-28 space-y-1.5">
                  <Label htmlFor={`li-price-${idx}`} className="sr-only">
                    Price
                  </Label>
                  <Input
                    id={`li-price-${idx}`}
                    type="number"
                    inputMode="decimal"
                    step="0.01"
                    min="0"
                    value={li.price}
                    onChange={(e) =>
                      updateLineItem(idx, { price: Number(e.target.value) })
                    }
                    placeholder="0.00"
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeLineItem(idx)}
                  aria-label="Remove line item"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
