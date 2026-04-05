import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🍽️</span>
            <span className="font-bold text-lg text-slate-900">FoodFinder</span>
          </Link>

          <div className="flex gap-8 items-center">
            <Link
              href="/"
              className="text-slate-600 hover:text-slate-900 transition"
            >
              Home
            </Link>
            <Link
              href="/categories"
              className="text-slate-600 hover:text-slate-900 transition"
            >
              Categories
            </Link>
            <Link
              href="/search"
              className="text-slate-600 hover:text-slate-900 transition"
            >
              Search
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
