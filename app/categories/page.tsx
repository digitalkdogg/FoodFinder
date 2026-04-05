import { prisma } from "@/lib/prisma";
import Link from "next/link";

async function getCategories() {
  const categories = await prisma.category.findMany({
    include: {
      _count: {
        select: { recipes: true },
      },
    },
    orderBy: { name: "asc" },
  });

  return categories;
}

export default async function CategoriesPage() {
  const categories = await getCategories();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-4xl font-bold text-slate-900 mb-12">Categories</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories.map((cat) => (
          <Link
            key={cat.id}
            href={`/categories/${cat.id}`}
            className="bg-white rounded-lg shadow-sm hover:shadow-md transition border border-slate-200 p-6 cursor-pointer"
          >
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              {cat.name}
            </h3>
            <p className="text-slate-600">
              {cat._count.recipes}{" "}
              {cat._count.recipes === 1 ? "recipe" : "recipes"}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
