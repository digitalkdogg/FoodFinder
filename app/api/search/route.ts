import { prisma } from "@/lib/prisma";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q");

  if (!query || query.trim().length === 0) {
    return NextResponse.json({ recipes: [] });
  }

  try {
    const recipes = await prisma.recipe.findMany({
      where: {
        name: {
          contains: query,
        },
      },
      include: {
        category: true,
      },
      take: 50,
      orderBy: { publication_date: "desc" },
    });

    return NextResponse.json({ recipes });
  } catch (error) {
    console.error("Search error:", error);
    return NextResponse.json({ recipes: [] }, { status: 500 });
  }
}
