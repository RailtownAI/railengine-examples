import { z } from "zod";

export const CATEGORIES = [
  "food",
  "travel",
  "lodging",
  "transportation",
  "office",
  "entertainment",
  "other",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const LineItemSchema = z.object({
  description: z.string(),
  price: z.number(),
});

export const ExpenseSchema = z.object({
  id: z.string(),
  vendor: z.string(),
  amount: z.number(),
  currency: z.string(),
  date: z.string(),
  category: z.enum(CATEGORIES),
  lineItems: z.array(LineItemSchema),
  tax: z.number(),
  tip: z.number(),
});

export type Expense = z.infer<typeof ExpenseSchema>;
export type LineItem = z.infer<typeof LineItemSchema>;

export const ExtractedExpenseSchema = ExpenseSchema.omit({ id: true });
export type ExtractedExpense = z.infer<typeof ExtractedExpenseSchema>;
