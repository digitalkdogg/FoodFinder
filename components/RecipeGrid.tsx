import RecipeCard from "./RecipeCard";

interface Recipe {
  id: number;
  name: string;
  image_url: string | null;
  publication_date: Date | null;
  category: {
    name: string;
  };
}

interface RecipeGridProps {
  recipes: Recipe[];
}

export default function RecipeGrid({ recipes }: RecipeGridProps) {
  if (recipes.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500 text-lg">No recipes found.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {recipes.map((recipe) => (
        <RecipeCard
          key={recipe.id}
          id={recipe.id}
          name={recipe.name}
          image_url={recipe.image_url}
          category_name={recipe.category.name}
          publication_date={recipe.publication_date}
        />
      ))}
    </div>
  );
}
