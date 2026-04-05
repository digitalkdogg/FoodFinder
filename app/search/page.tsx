"use client";

import { useState, FormEvent } from "react";
import RecipeGrid from "@/components/RecipeGrid";
import { useRouter } from "next/navigation";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [recipes, setRecipes] = useState<any[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSearch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);

    try {
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(query)}`
      );
      const data = await response.json();
      setRecipes(data.recipes || []);
    } catch (error) {
      console.error("Search failed:", error);
      setRecipes([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-4xl font-bold text-slate-900 mb-8">Search Recipes</h1>

      <form onSubmit={handleSearch} className="mb-12">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by recipe name..."
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-medium"
          >
            Search
          </button>
        </div>
      </form>

      {loading && <p className="text-slate-600">Searching...</p>}

      {searched && !loading && (
        <>
          <p className="text-slate-600 mb-8">
            Found {recipes.length} {recipes.length === 1 ? "recipe" : "recipes"}
          </p>
          <RecipeGrid recipes={recipes} />
        </>
      )}

      {!searched && (
        <p className="text-slate-500 text-center py-12">
          Enter a search term to find recipes
        </p>
      )}
    </div>
  );
}
