"use client";

import * as React from "react";
import { Loader2, Upload } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { ExpenseConfirmDialog } from "@/components/expense-confirm-dialog";
import type { ExtractedExpense } from "@/lib/schema";

type Props = {
  onIngested: () => void | Promise<void>;
};

const ACCEPTED_MIMES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

const fileToBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("Failed to read file"));
        return;
      }
      const commaIdx = result.indexOf(",");
      resolve(commaIdx >= 0 ? result.slice(commaIdx + 1) : result);
    };
    reader.onerror = () => reject(reader.error ?? new Error("FileReader error"));
    reader.readAsDataURL(file);
  });

export function ReceiptDropzone({ onIngested }: Props) {
  const [dragCount, setDragCount] = React.useState(0);
  const [extracting, setExtracting] = React.useState(false);
  const [extracted, setExtracted] = React.useState<ExtractedExpense | null>(
    null,
  );
  const [confirmOpen, setConfirmOpen] = React.useState(false);
  /** Bumps whenever a new extraction succeeds so ExpenseForm remounts with fresh state. */
  const [confirmFormInstanceKey, setConfirmFormInstanceKey] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleFile = React.useCallback(
    async (file: File) => {
      if (!ACCEPTED_MIMES.includes(file.type)) {
        toast.error(
          `Unsupported file type: ${file.type || "unknown"}. Use JPG, PNG, WebP or GIF.`,
        );
        return;
      }
      setExtracting(true);
      try {
        const imageBase64 = await fileToBase64(file);
        const res = await fetch("/api/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ imageBase64, mimeType: file.type }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.error ?? `Extraction failed (${res.status})`);
        }
        setExtracted(data as ExtractedExpense);
        setConfirmFormInstanceKey((k) => k + 1);
        setConfirmOpen(true);
      } catch (err) {
        toast.error(
          err instanceof Error ? err.message : "Failed to extract receipt",
        );
      } finally {
        setExtracting(false);
      }
    },
    [],
  );

  React.useEffect(() => {
    const onDragEnter = (e: DragEvent) => {
      if (!e.dataTransfer?.types?.includes("Files")) return;
      e.preventDefault();
      setDragCount((c) => c + 1);
    };
    const onDragOver = (e: DragEvent) => {
      if (!e.dataTransfer?.types?.includes("Files")) return;
      e.preventDefault();
    };
    const onDragLeave = (e: DragEvent) => {
      if (!e.dataTransfer?.types?.includes("Files")) return;
      e.preventDefault();
      setDragCount((c) => Math.max(0, c - 1));
    };
    const onDrop = (e: DragEvent) => {
      if (!e.dataTransfer?.types?.includes("Files")) return;
      e.preventDefault();
      setDragCount(0);
      const file = e.dataTransfer?.files?.[0];
      if (file) void handleFile(file);
    };

    window.addEventListener("dragenter", onDragEnter);
    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    window.addEventListener("drop", onDrop);
    return () => {
      window.removeEventListener("dragenter", onDragEnter);
      window.removeEventListener("dragover", onDragOver);
      window.removeEventListener("dragleave", onDragLeave);
      window.removeEventListener("drop", onDrop);
    };
  }, [handleFile]);

  const onPickFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void handleFile(file);
    e.target.value = "";
  };

  return (
    <>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-muted-foreground/30 bg-card p-8 text-center transition-colors hover:border-muted-foreground/60 hover:bg-accent/40",
          extracting && "pointer-events-none opacity-80",
        )}
        aria-label="Upload receipt"
      >
        {extracting ? (
          <>
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <p className="text-sm font-medium">Reading receipt…</p>
            <p className="text-xs text-muted-foreground">
              Claude vision is extracting the fields.
            </p>
          </>
        ) : (
          <>
            <Upload className="h-6 w-6 text-muted-foreground" />
            <p className="text-sm font-medium">
              Drop a receipt or click to upload
            </p>
            <p className="text-xs text-muted-foreground">
              JPG, PNG, WebP or GIF. Image data is sent to Claude for extraction
              only — it is not stored in Railengine.
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_MIMES.join(",")}
          hidden
          onChange={onPickFile}
        />
      </button>

      {dragCount > 0 && !extracting ? (
        <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="rounded-xl border-2 border-dashed border-primary/60 bg-card px-10 py-8 text-center shadow-xl">
            <Upload className="mx-auto h-8 w-8 text-primary" />
            <p className="mt-2 text-base font-semibold">
              Drop receipt to extract
            </p>
          </div>
        </div>
      ) : null}

      <ExpenseConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        initial={extracted}
        formInstanceKey={confirmFormInstanceKey}
        onIngested={onIngested}
      />
    </>
  );
}
