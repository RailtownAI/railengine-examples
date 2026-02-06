export type Meal = {
  name: string;
  calories: number;
  carbohydrates: number;
  sugar: number;
  fat: number;
  protein: number;
};

export const MEALS: Meal[] = [
  {
    name: "Chicken Shawarma",
    calories: 350,
    carbohydrates: 25,
    sugar: 2,
    fat: 15,
    protein: 30,
  },
  {
    name: "Grilled Chicken Breast",
    calories: 231,
    carbohydrates: 0,
    sugar: 0,
    fat: 5,
    protein: 43,
  },
  {
    name: "Salmon Fillet",
    calories: 206,
    carbohydrates: 0,
    sugar: 0,
    fat: 12,
    protein: 22,
  },
  {
    name: "Pasta with Marinara",
    calories: 220,
    carbohydrates: 43,
    sugar: 6,
    fat: 1,
    protein: 8,
  },
  {
    name: "Beef Burger",
    calories: 354,
    carbohydrates: 33,
    sugar: 6,
    fat: 15,
    protein: 17,
  },
  {
    name: "Caesar Salad",
    calories: 470,
    carbohydrates: 26,
    sugar: 4,
    fat: 36,
    protein: 17,
  },
  {
    name: "Greek Salad",
    calories: 200,
    carbohydrates: 10,
    sugar: 6,
    fat: 15,
    protein: 8,
  },
  {
    name: "Chicken Wrap",
    calories: 320,
    carbohydrates: 30,
    sugar: 3,
    fat: 12,
    protein: 20,
  },
  {
    name: "Tuna Salad Sandwich",
    calories: 350,
    carbohydrates: 35,
    sugar: 5,
    fat: 12,
    protein: 22,
  },
  {
    name: "Vegetable Stir Fry",
    calories: 150,
    carbohydrates: 20,
    sugar: 8,
    fat: 5,
    protein: 6,
  },
  {
    name: "Oatmeal with Berries",
    calories: 200,
    carbohydrates: 35,
    sugar: 12,
    fat: 4,
    protein: 6,
  },
  {
    name: "Scrambled Eggs",
    calories: 196,
    carbohydrates: 1,
    sugar: 1,
    fat: 15,
    protein: 13,
  },
  {
    name: "Avocado Toast",
    calories: 320,
    carbohydrates: 30,
    sugar: 2,
    fat: 20,
    protein: 10,
  },
  {
    name: "Grilled Salmon",
    calories: 206,
    carbohydrates: 0,
    sugar: 0,
    fat: 12,
    protein: 22,
  },
  {
    name: "Chicken Caesar Wrap",
    calories: 380,
    carbohydrates: 32,
    sugar: 4,
    fat: 18,
    protein: 24,
  },
  {
    name: "Turkey Sandwich",
    calories: 280,
    carbohydrates: 28,
    sugar: 4,
    fat: 8,
    protein: 20,
  },
  { name: "Quinoa Bowl", calories: 222, carbohydrates: 39, sugar: 0, fat: 4, protein: 8 },
  { name: "Sushi Roll", calories: 200, carbohydrates: 28, sugar: 3, fat: 2, protein: 6 },
  {
    name: "Pizza Slice",
    calories: 285,
    carbohydrates: 36,
    sugar: 4,
    fat: 10,
    protein: 12,
  },
  {
    name: "Chicken Teriyaki",
    calories: 300,
    carbohydrates: 35,
    sugar: 15,
    fat: 8,
    protein: 25,
  },
];

export function searchMeals(query: string): Meal[] {
  if (!query || query.trim() === "") {
    return [];
  }

  const lowerQuery = query.toLowerCase().trim();
  return MEALS.filter((meal) => meal.name.toLowerCase().includes(lowerQuery));
}
