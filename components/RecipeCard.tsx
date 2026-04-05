import Link from "next/link";
import Image from "next/image";

interface RecipeCardProps {
  id: number;
  name: string;
  image_url: string | null;
  category_name: string;
  publication_date: Date | null;
}

export default function RecipeCard({
  id,
  name,
  image_url,
  category_name,
  publication_date,
}: RecipeCardProps) {
  const dateStr = publication_date
    ? new Date(publication_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : null;

  return (
    <Link href={`/recipes/${id}`}>
      <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition border border-slate-200 overflow-hidden cursor-pointer">
        <div className="relative w-full h-48 bg-slate-200">
          {image_url ? (
            <Image
              src={image_url}
              alt={name}
              fill
              className="object-cover"
              unoptimized
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-4xl">
              🥘
            </div>
          )}
        </div>

        <div className="p-4">
          <h3 className="font-semibold text-slate-900 text-lg line-clamp-2">
            {name}
          </h3>

          <div className="mt-3 flex items-center justify-between text-sm">
            <span className="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">
              {category_name}
            </span>
            {dateStr && (
              <span className="text-slate-500 text-xs">{dateStr}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
