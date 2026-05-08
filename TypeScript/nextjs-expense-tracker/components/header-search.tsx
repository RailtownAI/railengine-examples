"use client";

import * as React from "react";
import { Loader2, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverAnchor,
  PopoverContent,
} from "@/components/ui/popover";
import { ExpenseDetailSheet } from "@/components/expense-detail-sheet";
import type { ExpenseSearchResult } from "@/lib/schema";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

type SearchMode = "index" | "vector";

const matchTooltip: Record<SearchMode, string> = {
  index:
    "Match strength vs. the top result in this list (index rank), not statistical accuracy.",
  vector:
    "Match strength vs. the top result in this list (vector similarity or distance), not statistical accuracy.",
};

export function HeaderSearch() {
  const [mode, setMode] = React.useState<SearchMode>("index");
  const [query, setQuery] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<ExpenseSearchResult[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<ExpenseSearchResult | null>(
    null,
  );

  const runSearch = React.useCallback(async () => {
    const q = query.trim();
    if (!q) return;

    setOpen(true);
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q, mode }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        results?: ExpenseSearchResult[];
        error?: string;
      };

      if (!res.ok) {
        throw new Error(data.error ?? `Search failed (${res.status})`);
      }

      setResults(Array.isArray(data.results) ? data.results : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, mode]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      void runSearch();
    }
  };

  return (
    <>
    <Popover modal={false} open={open} onOpenChange={setOpen}>
      <PopoverAnchor asChild>
        <div
          className={cn(
            "flex w-full min-w-0 max-w-lg items-center gap-2 sm:max-w-xl",
          )}
        >
          <Select
            value={mode}
            onValueChange={(v) => setMode(v as SearchMode)}
          >
            <SelectTrigger
              className="h-9 w-[10.5rem] shrink-0 sm:w-[11rem]"
              aria-label="Search mode"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper" align="start">
              <SelectItem value="index">Index search</SelectItem>
              <SelectItem value="vector">Vector search</SelectItem>
            </SelectContent>
          </Select>

          <Input
            type="search"
            placeholder="Search expenses…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            className="min-w-0 flex-1"
            aria-label="Search expenses"
            autoComplete="off"
          />
          <Button
            type="button"
            size="icon"
            variant="secondary"
            className="shrink-0"
            aria-label="Run search"
            onClick={() => void runSearch()}
            disabled={loading || !query.trim()}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
          </Button>
        </div>
      </PopoverAnchor>

      <PopoverContent
        align="center"
        side="bottom"
        sideOffset={8}
        collisionPadding={16}
        className={cn(
          "flex max-h-[min(70vh,22rem)] w-full min-w-[min(100vw-2rem,28rem)] max-w-lg flex-col overflow-hidden p-0",
        )}
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <div className="border-b px-3 py-2">
          <p className="text-xs font-medium text-muted-foreground">
            {mode === "index" ? "Index" : "Vector"} results
            {!loading && results.length > 0 ? ` · ${results.length}` : null}
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="h-12 animate-pulse rounded-md bg-muted"
                />
              ))}
            </div>
          ) : error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : results.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No matching expenses. Try different keywords, or confirm your
              engine has indexing / VectorStore1 configured.
            </p>
          ) : (
            <ul className="space-y-2">
              {results.map((exp) => (
                <li key={exp.id} className="list-none">
                  <button
                    type="button"
                    className={cn(
                      "w-full rounded-md border border-border bg-card px-3 py-2 text-left text-sm shadow-sm",
                      "transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    )}
                    onClick={() => setSelected(exp)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium leading-tight">
                        {exp.vendor}
                      </span>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        {exp.relevancePercent !== undefined ? (
                          <span
                            className="text-[0.65rem] font-medium tabular-nums leading-none text-emerald-700 dark:text-emerald-400"
                            title={matchTooltip[mode]}
                          >
                            {exp.relevancePercent}% match
                          </span>
                        ) : null}
                        <span className="tabular-nums font-semibold">
                          {formatCurrency(exp.amount, exp.currency)}
                        </span>
                      </div>
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>{formatDate(exp.date)}</span>
                      <Badge variant="secondary" className="capitalize">
                        {exp.category}
                      </Badge>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </PopoverContent>
    </Popover>

    <ExpenseDetailSheet
      expense={selected}
      onClose={() => setSelected(null)}
      relevancePercent={selected?.relevancePercent}
      relevanceTitle={matchTooltip[mode]}
    />
    </>
  );
}
