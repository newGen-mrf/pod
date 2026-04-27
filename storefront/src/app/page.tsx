'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

/* ──────────────────────────────────────────────
   Types
   ────────────────────────────────────────────── */
interface ProductImage {
  src: string;
  variant_ids?: number[];
  is_default?: boolean;
}

interface ProductVariant {
  id: number;
  title: string;
  price: number;
  is_enabled: boolean;
}

interface Product {
  id: string;
  title: string;
  description: string;
  tags: string[];
  images: ProductImage[];
  variants: ProductVariant[];
  created_at?: string;
}

/* ──────────────────────────────────────────────
   Constants
   ────────────────────────────────────────────── */
const SHOP_URL = 'https://thedailyprint-shop.printify.me/products';

const PRODUCT_TYPES = ['All', 'T-Shirts', 'Hoodies', 'Mugs'];

/* ──────────────────────────────────────────────
   SVG Icons (inline to avoid dependencies)
   ────────────────────────────────────────────── */
const Icons = {
  cart: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="21" r="1" /><circle cx="20" cy="21" r="1" />
      <path d="m1 1 4 2 2 12h13l3-8H6" />
    </svg>
  ),
  search: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
    </svg>
  ),
  eye: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" />
    </svg>
  ),
  external: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  ),
  close: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  truck: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1" y="3" width="15" height="13" /><polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
      <circle cx="5.5" cy="18.5" r="2.5" /><circle cx="18.5" cy="18.5" r="2.5" />
    </svg>
  ),
  shield: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  sparkle: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
    </svg>
  ),
  refresh: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" />
      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" /><path d="M8 16H3v5" />
    </svg>
  ),
  menu: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="6" x2="20" y2="6" /><line x1="4" y1="18" x2="20" y2="18" />
    </svg>
  ),
};

/* ──────────────────────────────────────────────
   Main Page Component
   ────────────────────────────────────────────── */
export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('All');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [navScrolled, setNavScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const productsRef = useRef<HTMLDivElement>(null);

  /* ── Fetch products ── */
  useEffect(() => {
    async function fetchProducts() {
      try {
        const res = await fetch('/api/products');
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setProducts(data.products || []);
      } catch (err) {
        console.error('Error loading products:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchProducts();
  }, []);

  /* ── Scroll listener for nav ── */
  useEffect(() => {
    const onScroll = () => setNavScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* ── Close modal on Escape ── */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedProduct(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  /* ── Helpers ── */
  const formatPrice = (cents: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100);

  const getProductType = useCallback((product: Product): string => {
    const title = product.title.toLowerCase();
    if (title.includes('hoodie') || title.includes('sweatshirt')) return 'Hoodies';
    if (title.includes('mug') || title.includes('cup')) return 'Mugs';
    return 'T-Shirts';
  }, []);

  const filteredProducts = products.filter((p) => {
    const matchesFilter = activeFilter === 'All' || getProductType(p) === activeFilter;
    const matchesSearch =
      !searchQuery ||
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.tags?.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const getDefaultImage = (product: Product) => {
    const defaultImg = product.images?.find((img) => img.is_default);
    return (defaultImg || product.images?.[0])?.src || '';
  };

  const getLowestPrice = (product: Product) => {
    const enabled = product.variants?.filter((v) => v.is_enabled) || [];
    if (!enabled.length) return product.variants?.[0]?.price || 0;
    return Math.min(...enabled.map((v) => v.price));
  };

  const isNewProduct = (product: Product) => {
    if (!product.created_at) return false;
    const created = new Date(product.created_at);
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000);
    return created > threeDaysAgo;
  };

  /* ── Scroll into view ── */
  const scrollToProducts = () => {
    productsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  /* ──────────────────────────────────────────
     Render
     ────────────────────────────────────────── */
  return (
    <>
      {/* ═══════ NAVIGATION ═══════ */}
      <nav className={`nav ${navScrolled ? 'nav-scrolled' : ''}`} id="top-nav">
        <div className="nav-inner">
          <a href="#" className="nav-logo">
            <span className="nav-logo-dot" />
            The Daily Print
          </a>

          <ul className={`nav-links ${mobileMenuOpen ? 'open' : ''}`}>
            <li><a href="#" className="nav-link" onClick={() => setMobileMenuOpen(false)}>Home</a></li>
            <li><a href="#products" className="nav-link" onClick={() => setMobileMenuOpen(false)}>Shop</a></li>
            <li><a href="#features" className="nav-link" onClick={() => setMobileMenuOpen(false)}>Why Us</a></li>
            <li><a href="#newsletter" className="nav-link" onClick={() => setMobileMenuOpen(false)}>Updates</a></li>
          </ul>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <a href={SHOP_URL} target="_blank" rel="noopener noreferrer" className="nav-cta">
              {Icons.cart}
              <span>Shop</span>
            </a>
            <button
              className="nav-toggle"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? Icons.close : Icons.menu}
            </button>
          </div>
        </div>
      </nav>

      <main>
        {/* ═══════ HERO ═══════ */}
        <section className="hero" id="hero">
          <div className="hero-bg" aria-hidden="true">
            <div className="hero-orb hero-orb-1" />
            <div className="hero-orb hero-orb-2" />
            <div className="hero-orb hero-orb-3" />
          </div>

          <div className="hero-content">
            <div className="hero-badge animate-fade-in-up">
              <span className="hero-badge-dot" />
              Fresh designs added daily
            </div>

            <h1 className="hero-title animate-fade-in-up delay-1">
              Wear Your{' '}
              <span className="text-gradient">Vibe.</span>
            </h1>

            <p className="hero-subtitle animate-fade-in-up delay-2">
              Premium print‑on‑demand apparel crafted with AI‑powered creativity.
              Unique designs you won&#39;t find anywhere else.
            </p>

            <div className="hero-actions animate-fade-in-up delay-3">
              <button className="btn btn-primary btn-lg" onClick={scrollToProducts}>
                Explore Collection
              </button>
              <a href={SHOP_URL} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-lg">
                Visit Full Store {Icons.external}
              </a>
            </div>
          </div>

          <div className="hero-scroll-indicator" aria-hidden="true">
            <span>Scroll</span>
            <span className="hero-scroll-line" />
          </div>
        </section>

        {/* ═══════ MARQUEE ═══════ */}
        <div className="marquee" aria-hidden="true">
          <div className="marquee-track">
            {[...Array(2)].map((_, setIndex) => (
              <div key={setIndex} style={{ display: 'flex' }}>
                {[
                  'Premium Quality',
                  'AI-Generated',
                  'Global Shipping',
                  'New Designs Daily',
                  'Unique & Original',
                  'Eco-Friendly',
                  'Made to Order',
                  'Satisfaction Guaranteed',
                ].map((text, i) => (
                  <span className="marquee-item" key={`${setIndex}-${i}`}>
                    <span className="marquee-dot" />
                    {text}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* ═══════ STATS ═══════ */}
        <section className="section" style={{ paddingBottom: '2rem' }}>
          <div className="container">
            <div className="stats-bar">
              {[
                { value: `${products.length || '—'}+`, label: 'Unique Designs' },
                { value: '150+', label: 'Happy Customers' },
                { value: '3x', label: 'Daily Drops' },
                { value: '4.9', label: 'Avg. Rating' },
              ].map((stat, i) => (
                <div className="stat-item animate-fade-in-up" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
                  <div className="stat-value text-gradient">{stat.value}</div>
                  <div className="stat-label">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════ PRODUCTS ═══════ */}
        <section className="section" id="products" ref={productsRef}>
          <div className="container">
            <div style={{ marginBottom: '1rem' }}>
              <span className="section-label">✦ Collection</span>
              <h2 className="section-title">Latest Drops</h2>
              <p className="section-description">
                Fresh from the AI studio — each design is one‑of‑a‑kind. Find your next favourite piece.
              </p>
            </div>

            {/* Filters + Search */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1rem',
              marginBottom: '2rem',
              marginTop: '2rem',
            }}>
              <div className="filter-bar" style={{ marginBottom: 0 }}>
                {PRODUCT_TYPES.map((type) => (
                  <button
                    key={type}
                    className={`filter-tab ${activeFilter === type ? 'active' : ''}`}
                    onClick={() => setActiveFilter(type)}
                  >
                    {type}
                  </button>
                ))}
              </div>

              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  placeholder="Search designs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    padding: '10px 16px 10px 40px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-full)',
                    color: 'var(--text-primary)',
                    fontFamily: 'Outfit, sans-serif',
                    fontSize: '0.9rem',
                    outline: 'none',
                    width: '220px',
                    transition: 'border-color 0.2s ease',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
                  onBlur={(e) => (e.target.style.borderColor = 'var(--border)')}
                />
                <span style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                  {Icons.search}
                </span>
              </div>
            </div>

            {/* Product Grid */}
            {loading ? (
              <div className="products-grid">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="skeleton" style={{ height: '420px' }} />
                ))}
              </div>
            ) : filteredProducts.length > 0 ? (
              <div className="products-grid">
                {filteredProducts.map((product, idx) => {
                  const imageSrc = getDefaultImage(product);
                  const price = getLowestPrice(product);
                  const isNew = isNewProduct(product);

                  return (
                    <div
                      key={product.id}
                      className="product-card animate-fade-in-up"
                      style={{ animationDelay: `${Math.min(idx * 0.05, 0.5)}s` }}
                    >
                      <div className="product-card-image-wrap">
                        {isNew && <span className="product-card-badge">New</span>}
                        {imageSrc ? (
                          <img
                            src={imageSrc}
                            alt={product.title}
                            className="product-card-image"
                            loading="lazy"
                          />
                        ) : (
                          <div style={{
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--text-muted)',
                            fontSize: '2rem',
                          }}>
                            🎨
                          </div>
                        )}
                        <div className="product-card-actions">
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => setSelectedProduct(product)}
                          >
                            {Icons.eye} Quick View
                          </button>
                        </div>
                      </div>

                      <div className="product-card-body">
                        <span className="product-card-category">{getProductType(product)}</span>
                        <h3 className="product-card-title">{product.title}</h3>
                        <div className="product-card-footer">
                          <div>
                            <div className="product-card-price">{formatPrice(price)}</div>
                            <span className="product-card-price-label">Starting from</span>
                          </div>
                          <a
                            href={SHOP_URL}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-primary btn-sm"
                          >
                            Buy {Icons.external}
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🎨</div>
                <h3 className="empty-title">
                  {searchQuery ? 'No matching designs' : 'No products yet'}
                </h3>
                <p className="empty-desc">
                  {searchQuery
                    ? `Nothing matches "${searchQuery}". Try a different search.`
                    : 'Our AI artist is crafting fresh designs. Check back soon!'}
                </p>
              </div>
            )}

            {/* View All CTA */}
            {filteredProducts.length > 0 && (
              <div style={{ textAlign: 'center', marginTop: '3rem' }}>
                <a
                  href={SHOP_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-lg"
                >
                  Browse Full Collection {Icons.external}
                </a>
              </div>
            )}
          </div>
        </section>

        {/* ═══════ FEATURES ═══════ */}
        <section className="section" id="features" style={{ background: 'var(--bg-secondary)' }}>
          <div className="container">
            <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
              <span className="section-label">✦ Why Choose Us</span>
              <h2 className="section-title">Built Different</h2>
              <p className="section-description" style={{ margin: '0 auto' }}>
                Every piece is crafted with care, printed on demand, and shipped worldwide.
              </p>
            </div>

            <div className="features-grid">
              {[
                {
                  icon: Icons.sparkle,
                  title: 'AI-Powered Designs',
                  desc: 'Each design is uniquely generated by our AI creative engine — no two are ever the same.',
                },
                {
                  icon: Icons.truck,
                  title: 'Global Shipping',
                  desc: 'We ship to 200+ countries via our network of production partners closest to you.',
                },
                {
                  icon: Icons.shield,
                  title: 'Quality Guaranteed',
                  desc: 'Premium fabrics and printing techniques. Not happy? Full refund, no questions asked.',
                },
                {
                  icon: Icons.refresh,
                  title: 'Fresh Daily Drops',
                  desc: 'New designs are generated and added to the store multiple times every single day.',
                },
              ].map((feature, i) => (
                <div
                  key={i}
                  className="feature-card animate-fade-in-up"
                  style={{ animationDelay: `${i * 0.1}s` }}
                >
                  <div className="feature-icon">{feature.icon}</div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-desc">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════ NEWSLETTER CTA ═══════ */}
        <section className="cta-section section" id="newsletter">
          <div className="container">
            <div className="cta-card">
              <span className="section-label">✦ Stay Updated</span>
              <h2 className="cta-title">
                Don&#39;t Miss the <span className="text-gradient">Drop</span>
              </h2>
              <p className="cta-desc">
                Get notified when new designs land. Be the first to cop limited edition pieces.
              </p>
              <form
                className="cta-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  alert('Thanks for subscribing! 🎉');
                }}
              >
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="cta-input"
                  required
                />
                <button type="submit" className="btn btn-primary">
                  Subscribe
                </button>
              </form>
            </div>
          </div>
        </section>
      </main>

      {/* ═══════ FOOTER ═══════ */}
      <footer className="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-brand">
              <div className="footer-brand-name">
                <span className="nav-logo-dot" />
                The Daily Print
              </div>
              <p className="footer-brand-desc">
                Premium print-on-demand apparel powered by AI creativity.
                Unique designs generated fresh every day — express your vibe.
              </p>
            </div>

            <div>
              <h4 className="footer-heading">Shop</h4>
              <ul className="footer-links">
                <li><a href="#products" className="footer-link">New Arrivals</a></li>
                <li><a href={SHOP_URL} className="footer-link" target="_blank" rel="noopener noreferrer">All Products</a></li>
                <li><a href={SHOP_URL} className="footer-link" target="_blank" rel="noopener noreferrer">T-Shirts</a></li>
                <li><a href={SHOP_URL} className="footer-link" target="_blank" rel="noopener noreferrer">Hoodies</a></li>
              </ul>
            </div>

            <div>
              <h4 className="footer-heading">Company</h4>
              <ul className="footer-links">
                <li><a href="#features" className="footer-link">About Us</a></li>
                <li><a href="#newsletter" className="footer-link">Contact</a></li>
                <li><a href="#" className="footer-link">FAQ</a></li>
                <li><a href="#" className="footer-link">Shipping Info</a></li>
              </ul>
            </div>

            <div>
              <h4 className="footer-heading">Legal</h4>
              <ul className="footer-links">
                <li><a href="#" className="footer-link">Privacy Policy</a></li>
                <li><a href="#" className="footer-link">Terms of Service</a></li>
                <li><a href="#" className="footer-link">Refund Policy</a></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <span>&copy; {new Date().getFullYear()} The Daily Print. All rights reserved.</span>
            <div className="footer-socials">
              <a href="#" className="footer-social" aria-label="Instagram">✦</a>
              <a href="#" className="footer-social" aria-label="Twitter">𝕏</a>
              <a href="#" className="footer-social" aria-label="Pinterest">𝒫</a>
            </div>
          </div>
        </div>
      </footer>

      {/* ═══════ PRODUCT MODAL ═══════ */}
      {selectedProduct && (
        <div
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedProduct(null);
          }}
          role="dialog"
          aria-modal="true"
        >
          <div className="modal-content" style={{ position: 'relative' }}>
            <button
              className="modal-close"
              onClick={() => setSelectedProduct(null)}
              aria-label="Close modal"
            >
              {Icons.close}
            </button>

            <div className="modal-image">
              {getDefaultImage(selectedProduct) ? (
                <img
                  src={getDefaultImage(selectedProduct)}
                  alt={selectedProduct.title}
                />
              ) : (
                <div style={{
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '4rem',
                  color: 'var(--text-muted)',
                }}>
                  🎨
                </div>
              )}
            </div>

            <div className="modal-body">
              <span className="modal-category">{getProductType(selectedProduct)}</span>
              <h2 className="modal-title">{selectedProduct.title}</h2>
              <p className="modal-desc">
                {selectedProduct.description
                  ? selectedProduct.description.replace(/<[^>]*>/g, '').slice(0, 300)
                  : 'A unique, AI‑generated design printed on premium materials. Express your style with this one‑of‑a‑kind piece.'}
              </p>

              {selectedProduct.tags && selectedProduct.tags.length > 0 && (
                <div className="modal-tags">
                  {selectedProduct.tags.slice(0, 8).map((tag, i) => (
                    <span key={i} className="modal-tag">{tag}</span>
                  ))}
                </div>
              )}

              <div className="modal-price text-gradient">
                {formatPrice(getLowestPrice(selectedProduct))}
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: 'auto' }}>
                <a
                  href={SHOP_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary btn-lg"
                  style={{ flex: 1 }}
                >
                  Buy Now {Icons.external}
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
