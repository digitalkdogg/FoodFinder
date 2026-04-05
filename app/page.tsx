import { Suspense } from "react";
import { prisma } from "@/lib/prisma";
import CategoryFilter from "@/components/CategoryFilter";
import RecipeGrid from "@/components/RecipeGrid";

async function getCategories() {
  return prisma.category.findMany({
    orderBy: { name: "asc" },
  });
}

async function getRecipes(categoryId?: number) {
  return prisma.recipe.findMany({
    where: categoryId ? { category_id: categoryId } : undefined,
    include: {
      category: true,
    },
    orderBy: { publication_date: "desc" },
  });
}

export default async function Home({
  searchParams,
}: {
  searchParams: { category?: string };
}) {
  const categories = await getCategories();
  const categoryId = searchParams.category
    ? parseInt(searchParams.category)
    : undefined;
  const recipes = await getRecipes(categoryId);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Discover Delicious Recipes
        </h1>
        <p className="text-lg text-slate-600">
          Find and cook amazing alpha-gal friendly recipes
        </p>
      </div>

      <CategoryFilter categories={categories} />

      <Suspense fallback={<div>Loading recipes...</div>}>
        <RecipeGrid recipes={recipes} />
      </Suspense>
    </div>
  );
}
