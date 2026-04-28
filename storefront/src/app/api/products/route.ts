import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const statePath = path.join(process.cwd(), 'public', 'state.json');
    let stateData: any = { history: [] };

    if (fs.existsSync(statePath)) {
      const fileContents = fs.readFileSync(statePath, 'utf8');
      stateData = JSON.parse(fileContents);
    }

    // Map the internal history to the Product format required by the frontend
    const products = stateData.history.map((entry: any, index: number) => {
      // Support Redbubble URL or fallback to alert
      const rbUrl = entry.results?.redbubble?.status === 'success' 
        ? entry.results.redbubble.url 
        : '#'; // Or a fallback store link

      // 'storefront/public/designs/name.png' becomes '/designs/name.png'
      let publicImgUrl = '';
      if (entry.design_path) {
        const imgName = entry.design_path.split('/').pop();
        publicImgUrl = `/designs/${imgName}`;
      }

      return {
        id: `design-${new Date(entry.timestamp).getTime()}-${index}`,
        title: entry.seo_title || entry.trend,
        description: `Premium graphic design generated automatically. Category: ${entry.category}. Ready for print-on-demand.`,
        tags: [entry.category, 'AI Design', 'Graphic'],
        images: publicImgUrl ? [{ src: publicImgUrl, is_default: true }] : [],
        variants: [
          { id: 1, title: 'Standard Design', price: 2200, is_enabled: true } // Mock $22.00 price display
        ],
        created_at: entry.timestamp,
        url: rbUrl // Custom payload prop for Redbubble redirection
      };
    }).reverse(); // Display newest first

    return NextResponse.json({ products });
  } catch (error) {
    console.error("API Route Error:", error);
    return NextResponse.json({ error: 'Failed to load products from state' }, { status: 500 });
  }
}
