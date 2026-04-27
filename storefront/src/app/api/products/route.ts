import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const shopId = process.env.PRINTIFY_SHOP_ID;
    const token = process.env.PRINTIFY_API_TOKEN;

    if (!shopId || !token) {
      return NextResponse.json({ error: 'Missing Printify API credentials on the server' }, { status: 500 });
    }

    const response = await fetch(`https://api.printify.com/v1/shops/${shopId}/products.json?limit=50`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      // Cache products for 5 minutes (300 seconds)
      next: { revalidate: 300 }
    });

    if (!response.ok) {
      const text = await response.text();
      return NextResponse.json({ error: `Printify API error: ${response.status}`, details: text }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json({ products: data.data || [] });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch products' }, { status: 500 });
  }
}
