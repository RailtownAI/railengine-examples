import { z } from "zod";

export const FoodDiaryItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  meal: z.string(),
  date: z.string(),
  nutritional_info: z.object({
    calories: z.number(),
    carbohydrates: z.number(),
    sugar: z.number(),
    fat: z.number(),
    protein: z.number(),
  }),
});

export type FoodDiaryItem = z.infer<typeof FoodDiaryItemSchema>;
