import { prisma } from "@/lib/prisma";
import RecipeGrid from "@/components/RecipeGrid";
import Link from "next/link";

export const dynamic = "force-dynamic";

async function getTag(id: number) {
  return prisma.tag.findUnique({
    where: { id },
    include: {
      recipe_tags: {
        include: {
          recipe: {
            include: { category: true },
          },
        },
      },
    },
  });
}

export default async function TagPage({
  params,
}: {
  params: { id: string };
}) {
  const tag = await getTag(parseInt(params.id));

  if (!tag) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">Tag not found</h1>
        <Link href="/" className="text-blue-600 hover:underline">
          Back to recipes
        </Link>
      </div>
    );
  }

  const recipes = tag.recipe_tags.map((rt) => rt.recipe);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <Link
        href="/"
        className="text-blue-600 hover:underline text-sm font-medium mb-4 inline-block"
      >
        ← Back to recipes
      </Link>

      <h1 className="text-4xl font-bold text-slate-900 mb-4">{tag.name}</h1>
      <p className="text-slate-600 mb-12">
        {recipes.length} {recipes.length === 1 ? "recipe" : "recipes"}
      </p>

      <RecipeGrid recipes={recipes} />
    </div>
  );
}
