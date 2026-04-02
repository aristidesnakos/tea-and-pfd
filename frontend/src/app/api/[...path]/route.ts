import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

async function handler(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const target = `${BACKEND}/api/${path.join("/")}${req.nextUrl.search}`;

  const res = await fetch(target, {
    method: req.method,
    headers: req.headers,
    body: req.method !== "GET" && req.method !== "HEAD" ? await req.blob() : undefined,
  });

  const contentType = res.headers.get("content-type") || "";
  if (
    contentType.includes("json") ||
    contentType.includes("text")
  ) {
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { "content-type": contentType },
    });
  }

  // Binary (XLSX, SVG, etc.)
  return new NextResponse(await res.arrayBuffer(), {
    status: res.status,
    headers: {
      "content-type": contentType,
      ...(res.headers.get("content-disposition")
        ? { "content-disposition": res.headers.get("content-disposition")! }
        : {}),
    },
  });
}

export const GET = handler;
export const POST = handler;
export const DELETE = handler;
export const PUT = handler;
