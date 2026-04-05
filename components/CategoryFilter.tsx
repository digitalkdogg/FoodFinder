"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

interface CategoryFilterProps {
  categories: Array<{ id: number; name: string }>;
}

export default function CategoryFilter({ categories }: CategoryFilterProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const activeCategory = searchParams.get("category");

  const handleFilter = (categoryId: string | null) => {
    startTransition(() => {
      if (categoryId) {
        router.push(`/?category=${categoryId}`);
      } else {
        router.push("/");
      }
    });
  };

  return (
    <div className="mb-8">
      <h2 className="text-sm font-semibold text-slate-700 mb-4">Filter by Category</h2>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => handleFilter(null)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition ${
            !activeCategory
              ? "bg-slate-900 text-white"
              : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
          } ${isPending ? "opacity-50" : ""}`}
          disabled={isPending}
        >
          All Recipes
        </button>

        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => handleFilter(cat.id.toString())}
            className={`px-4 py-2 rounded-full text-sm font-medium transition ${
              activeCategory === cat.id.toString()
                ? "bg-slate-900 text-white"
                : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            } ${isPending ? "opacity-50" : ""}`}
            disabled={isPending}
          >
            {cat.name}
          </button>
        ))}
      </div>
    </div>
  );
}
