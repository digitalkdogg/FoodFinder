import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "FoodFinder | Alpha-Gal Recipes",
  description: "Discover and cook delicious alpha-gal friendly recipes",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="min-h-screen bg-slate-50">{children}</main>
      </body>
    </html>
  );
}
