import { prisma } from "@/lib/prisma";
import CookGuide from "@/components/CookGuide";
import Link from "next/link";
import Image from "next/image";

export const dynamic = "force-dynamic";

async function getRecipe(id: number) {
  return prisma.recipe.findUnique({
    where: { id },
    include: {
      category: true,
      recipe_ingredients: {
        include: { ingredient: true },
      },
      recipe_instructions: {
        orderBy: { step_number: "asc" },
      },
      recipe_tags: {
        include: { tag: true },
      },
      recipe_sources: {
        include: { source: true },
      },
    },
  });
}

export default async function RecipePage({
  params,
}: {
  params: { id: string };
}) {
  const recipe = await getRecipe(parseInt(params.id));

  if (!recipe) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">
          Recipe not found
        </h1>
        <Link href="/" className="text-blue-600 hover:underline">
          Back to recipes
        </Link>
      </div>
    );
  }

  const dateStr = recipe.publication_date
    ? new Date(recipe.publication_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="text-blue-600 hover:underline text-sm font-medium mb-4 inline-block"
        >
          ← Back to recipes
        </Link>

        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          {recipe.name}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-slate-600 mb-6">
          <span className="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
            {recipe.category.name}
          </span>
          {dateStr && <span className="text-sm">{dateStr}</span>}
        </div>

        {recipe.recipe_tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {recipe.recipe_tags.map((rt) => (
              <span
                key={rt.tag_id}
                className="inline-block bg-slate-200 text-slate-700 px-3 py-1 rounded text-sm"
              >
                {rt.tag.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Hero Image */}
      {recipe.image_url && (
        <div className="relative w-full h-96 mb-8 rounded-lg overflow-hidden">
          <Image
            src={recipe.image_url}
            alt={recipe.name}
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      )}

      {/* Ingredients */}
      {recipe.recipe_ingredients.length > 0 && (
        <section className="mb-8 bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="text-2xl font-bold text-slate-900 mb-6">
            📝 Ingredients
          </h2>
          <ul className="space-y-3">
            {recipe.recipe_ingredients.map((ri) => (
              <li key={ri.id} className="flex items-start gap-3 text-slate-700">
                <span className="text-blue-500 font-bold mt-0.5">•</span>
                <span>
                  {ri.quantity && <span className="font-semibold">{ri.quantity}</span>}
                  {ri.unit && <span> {ri.unit}</span>}
                  {ri.quantity && <span> </span>}
                  <span>{ri.ingredient.name}</span>
                  {ri.notes && <span className="text-slate-500"> ({ri.notes})</span>}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Instructions */}
      {recipe.instructions && (
        <section className="mb-8 bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="text-2xl font-bold text-slate-900 mb-6">
            📖 Instructions
          </h2>
          <div className="prose prose-sm text-slate-700 whitespace-pre-wrap">
            {recipe.instructions}
          </div>
        </section>
      )}

      {/* Cook Guide - NEW FEATURE */}
      <CookGuide
        rawIngredients={recipe.raw_ingredients}
        steps={recipe.recipe_instructions}
      />

      {/* Source */}
      {recipe.recipe_sources.length > 0 && (
        <section className="mt-8 bg-slate-100 rounded-lg p-6">
          <h3 className="font-semibold text-slate-900 mb-3">Source</h3>
          {recipe.recipe_sources.map((rs) => (
            <div key={rs.source_id} className="text-sm">
              <p className="text-slate-700 mb-1">
                From: <span className="font-medium">{rs.source.site_name}</span>
              </p>
              <a
                href={rs.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline break-all"
              >
                {rs.source_url}
              </a>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
