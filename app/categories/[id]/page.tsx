import { prisma } from "@/lib/prisma";
import RecipeGrid from "@/components/RecipeGrid";
import Link from "next/link";

export const dynamic = "force-dynamic";

async function getCategory(id: number) {
  return prisma.category.findUnique({
    where: { id },
    include: {
      recipes: {
        include: { category: true },
        orderBy: { publication_date: "desc" },
      },
    },
  });
}

export default async function CategoryPage({
  params,
}: {
  params: { id: string };
}) {
  const category = await getCategory(parseInt(params.id));

  if (!category) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">
          Category not found
        </h1>
        <Link href="/categories" className="text-blue-600 hover:underline">
          Back to categories
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <Link
        href="/categories"
        className="text-blue-600 hover:underline text-sm font-medium mb-4 inline-block"
      >
        ← Back to categories
      </Link>

      <h1 className="text-4xl font-bold text-slate-900 mb-4">
        {category.name}
      </h1>
      <p className="text-slate-600 mb-12">
        {category.recipes.length}{" "}
        {category.recipes.length === 1 ? "recipe" : "recipes"}
      </p>

      <RecipeGrid recipes={category.recipes} />
    </div>
  );
}
