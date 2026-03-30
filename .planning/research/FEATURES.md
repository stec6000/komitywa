# Feature Landscape

**Domain:** Vegan/plant-based food business website (recipes, ebooks, physical products, newsletter)
**Project:** Kuchenna Komitywa
**Researched:** 2026-03-30

## Table Stakes

Features users expect from a food business website. Missing any of these and the site feels incomplete or untrustworthy.

### Landing Page & Brand Presence

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Hero section with value proposition | First impression; users decide in 3 seconds whether to stay | Low | Strong food photography + clear "who we are" message |
| About / story section | Vegan customers care about brand values and mission | Low | Founder story, why vegan, philosophy |
| Product/service overview cards | Users need to immediately see what's offered | Low | Links to recipes, ebooks, products |
| Contact information & location | Local pickup requires knowing where you are | Low | Address, hours, map embed, phone/email |
| Mobile-responsive design | 70%+ of food blog traffic is mobile; people browse recipes on phones | Medium | Django templates must be mobile-first |
| Fast page load (< 3s) | Core Web Vitals affect SEO; food sites are image-heavy | Medium | Image optimization, lazy loading, compressed assets |

### Recipe Blog

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Recipe cards with structured layout | Standard format: ingredients, steps, times, servings | Medium | Dedicated recipe model, not just blog posts |
| Recipe categories and tags | Users browse by meal type, ingredient, dietary need | Low | Categories: sniadanie, obiad, deser, etc. |
| Recipe search | Users come looking for specific recipes | Medium | Full-text search across title, ingredients, description |
| High-quality recipe photos | Food blogs live or die by photography | Low (technical) | Image upload, responsive sizing, WebP format |
| Recipe Schema.org JSON-LD markup | Google rich snippets increase CTR by up to 82%; non-negotiable for food SEO | Medium | Recipe structured data: name, image, ingredients, steps, times, nutrition, ratings |
| "Jump to recipe" button | Users hate scrolling past story content to find the recipe | Low | Anchor link at top of post |
| Print-friendly recipe view | Users print recipes for the kitchen | Low | CSS print stylesheet or print button |
| Prep time / cook time / total time | Users filter by available time | Low | Fields on recipe model |
| Servings with adjustment | Users need to scale recipes | Low-Medium | Static display is table stakes; interactive scaling is a differentiator |
| Recipe pagination / archive | Browsing older content | Low | Standard Django pagination |

### E-commerce (Ebooks)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Ebook product pages with preview | Users need to see what they're buying: cover, description, table of contents | Low | Product detail page with sample pages/screenshots |
| Shopping cart | Standard e-commerce expectation | Medium | Session-based cart, works for logged-in and guest users |
| Checkout flow with Przelewy24 | Polish users expect BLIK and bank transfers | High | Przelewy24 integration, payment confirmation webhooks |
| Order confirmation page + email | Users need purchase confirmation | Medium | Thank-you page + email with receipt |
| PDF delivery via email | Project constraint: ebooks delivered by email only | Medium | Post-payment email with PDF attachment or secure download link |
| Order history (logged-in users) | Users want to reference past purchases | Low | Simple order list in user profile |

### E-commerce (Physical Products)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Product catalog with photos | Jarred meals and cakes need appetizing presentation | Low | Product list + detail pages |
| Product availability status | Local pickup items may be limited or seasonal | Low | In stock / out of stock / available on [date] |
| Pickup date/time selection | Core to local pickup model | Medium | Date picker during checkout; must define available slots |
| Order confirmation with pickup details | Users need to know when and where to pick up | Low | Email + confirmation page with address, date, instructions |
| Clear pricing with VAT | Legal requirement in Poland | Low | Prices displayed with VAT included (standard in PL) |

### Newsletter

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Email signup form | Basic list building | Low | Inline form in footer + dedicated signup spots |
| GDPR-compliant consent | Legal requirement in EU/Poland | Low | Checkbox with clear consent text, link to privacy policy |
| Subscription confirmation (double opt-in) | GDPR best practice, prevents spam signups | Low | Confirmation email flow |
| Unsubscribe link | Legal requirement | Low | One-click unsubscribe in every email |

### Trust & Legal

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Privacy policy page | GDPR requirement | Low | Static page, Polish language |
| Terms of service / regulamin | Required for e-commerce in Poland | Low | Static page |
| Cookie consent banner | EU e-Privacy directive | Low | Simple banner with accept/reject |
| SSL certificate | Users expect HTTPS; browsers warn otherwise | Low | Infrastructure concern, not app feature |

## Differentiators

Features that set Kuchenna Komitywa apart. Not expected, but create loyalty and competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Recipe ratings and reviews | Community engagement; social proof drives trust; helps with Schema.org rich snippets (star ratings in Google) | Medium | Logged-in users rate 1-5 stars + optional comment |
| "I made this" photo uploads | Community building, user-generated content, social proof (Minimalist Baker pattern) | Medium | Users upload photos of their versions; moderation needed |
| Recipe collections / favorites | Personalization drives return visits; users build their own cookbook | Low | Logged-in users save recipes to favorites list |
| Lead magnet (free recipe PDF for signup) | Dramatically increases newsletter conversion vs plain "subscribe" | Low-Medium | Free PDF ebook/recipe card in exchange for email |
| Seasonal / featured recipe highlights | Curated content feels premium; drives engagement with timely content | Low | Admin-curated featured recipes on homepage |
| Related recipes on product pages | Cross-selling: "Made with our jarred pesto" links recipe to product | Low | Manual or tag-based recipe-product linking |
| Bundle deals (ebook + product) | Increases average order value | Medium | Cart logic for bundles/discounts |
| Interactive serving size adjuster | Recipes auto-scale ingredient quantities | Medium | JavaScript-based ingredient multiplication |
| Nutritional information per recipe | Health-conscious vegan audience values this data | Low-Medium | Manual entry per recipe; displays in Schema.org markup |
| Social sharing buttons on recipes | Extends reach; food content is highly shareable | Low | Share to Facebook, Pinterest, WhatsApp |
| Recipe difficulty level | Helps users find appropriate recipes | Low | Simple field: easy/medium/advanced |
| Email welcome sequence | Automated onboarding series builds relationship after signup | Medium | Requires email automation (e.g., via external service or Django tasks) |
| Blog content beyond recipes | Vegan lifestyle, tips, product stories build SEO and authority | Low | Standard blog posts alongside recipe posts |
| Open Graph meta tags for social sharing | Recipe links shared on social media show rich previews with images | Low | og:title, og:image, og:description meta tags |

## Anti-Features

Features to explicitly NOT build. Each would add complexity without proportional value for this project scope.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| User-generated recipes | Moderation burden, quality control nightmare, off-brand content | Keep recipes editorial/admin-only; let users comment and rate |
| Real-time chat / customer support widget | Overkill for a small food business; adds infrastructure complexity | Contact form + email address; FAQ page |
| Subscription/recurring orders | Complex billing logic, inventory management for a business with local pickup | One-time orders only in v1; evaluate demand later |
| Loyalty points / rewards program | Complex to implement well; meaningless with small product catalog | Focus on quality content and newsletter relationship instead |
| Multi-language support | Polish-only constraint; translation adds ongoing maintenance cost | Single language, optimize for Polish SEO |
| Delivery/shipping integration | Out of scope (local pickup only); shipping adds logistics complexity | Clear "local pickup only" messaging; revisit if demand warrants |
| OAuth / social login | Email/password is sufficient; social login adds OAuth complexity and privacy concerns | Keep email-only auth as decided |
| Marketplace / third-party sellers | Completely different business model; massive complexity | Stay single-vendor |
| Mobile app | Web-first approach is correct; PWA could be added later if needed | Responsive web design covers mobile use cases |
| In-browser ebook reader | Project constraint is email delivery; reader adds significant frontend complexity | PDF delivery via email as specified |
| Complex product configurator | Overkill for jarred meals and cakes | Simple product variants if needed (e.g., cake size) |
| AI-powered recipe recommendations | Cool but premature; needs usage data and significant ML infrastructure | Manual curation (featured recipes, related recipes by tag) |
| Comment system on product pages | Low value; product reviews are more useful than discussion threads | Keep comments on recipes only; products get ratings if needed |

## Feature Dependencies

```
Authentication (existing) --> Order History
Authentication (existing) --> Recipe Favorites
Authentication (existing) --> Recipe Ratings/Reviews
Authentication (existing) --> "I Made This" Photos

Recipe Model --> Recipe Categories/Tags
Recipe Model --> Recipe Search
Recipe Model --> Recipe Schema.org Markup
Recipe Model --> Recipe Ratings
Recipe Model --> Print View
Recipe Model --> Social Sharing

Product Model --> Product Catalog
Product Model --> Shopping Cart
Shopping Cart --> Checkout Flow
Checkout Flow --> Przelewy24 Integration
Przelewy24 Integration --> Order Confirmation
Order Confirmation --> PDF Email Delivery (ebooks)
Order Confirmation --> Pickup Details (physical products)
Checkout Flow --> Pickup Date/Time Selection (physical products)

Newsletter Signup Form --> GDPR Consent
Newsletter Signup Form --> Double Opt-in Flow
Newsletter Signup Form --> Lead Magnet Delivery

Landing Page --> Brand Visual Identity (constraint: must be created from scratch)
All Pages --> Mobile-Responsive Design
All Pages --> Cookie Consent Banner
```

## MVP Recommendation

### Must Ship (Phase 1 priority)

These features form the minimum viable product. Without them, the site cannot function as a business.

1. **Landing page** with hero, about, services overview, contact/location -- this IS the business's public face
2. **Recipe blog** with recipe cards, categories, search, photos, Schema.org markup -- primary traffic driver and brand builder
3. **Ebook product pages + cart + checkout + Przelewy24 + email PDF delivery** -- revenue stream #1
4. **Physical product catalog + cart + checkout + pickup scheduling** -- revenue stream #2 (can share cart/checkout with ebooks)
5. **Newsletter signup** with GDPR consent and double opt-in -- list building from day one
6. **Legal pages** (privacy policy, terms, cookie consent) -- legal requirement, cannot launch without these

### Ship Soon After (Phase 2)

7. **Recipe ratings and reviews** -- community engagement, SEO boost from rich snippets
8. **Recipe favorites/collections** -- drives return visits
9. **Lead magnet for newsletter** -- significantly improves conversion
10. **Order history in user profile** -- table stakes for returning customers
11. **Open Graph tags + social sharing** -- extends reach with minimal effort

### Defer (Phase 3+)

12. **"I made this" photo uploads** -- community building but needs moderation
13. **Interactive serving adjuster** -- nice UX but not critical
14. **Email welcome sequence** -- requires email automation infrastructure
15. **Bundle deals** -- requires cart complexity
16. **Nutritional information** -- valuable but labor-intensive data entry

## Feature Prioritization Matrix

| Feature | User Value | Business Value | Complexity | Priority |
|---------|-----------|---------------|------------|----------|
| Landing page | High | High | Low | P0 - Ship first |
| Recipe blog (full) | High | High (SEO) | Medium | P0 - Ship first |
| Recipe Schema.org markup | Medium | High (SEO) | Medium | P0 - Ship with recipes |
| Ebook store + checkout | High | High (revenue) | High | P0 - Ship first |
| Physical product store | High | High (revenue) | High | P0 - Ship first |
| Przelewy24 integration | High | Critical | High | P0 - Ship first |
| Newsletter signup | Medium | High (retention) | Low | P0 - Ship first |
| Legal pages | Low | Critical (legal) | Low | P0 - Ship first |
| Mobile-responsive design | High | High (SEO) | Medium | P0 - Across all phases |
| Cookie consent | Low | Critical (legal) | Low | P0 - Ship first |
| Recipe ratings/reviews | Medium | Medium (SEO) | Medium | P1 - Ship soon |
| Recipe favorites | Medium | Medium (retention) | Low | P1 - Ship soon |
| Lead magnet | Low | High (conversion) | Low | P1 - Ship soon |
| Order history | Medium | Low | Low | P1 - Ship soon |
| OG tags + sharing | Low | Medium (reach) | Low | P1 - Ship soon |
| "I made this" photos | Low | Medium (community) | Medium | P2 - Defer |
| Serving adjuster | Medium | Low | Medium | P2 - Defer |
| Email welcome sequence | Low | Medium (retention) | Medium | P2 - Defer |
| Bundle deals | Low | Medium (AOV) | Medium | P2 - Defer |
| Nutritional info | Medium | Low | Low-Medium | P2 - Defer |

## Sources

- [Google Recipe Schema Docs](https://developers.google.com/search/docs/appearance/structured-data/recipe)
- [Schema.org Recipe Type](https://schema.org/Recipe)
- [Top 10 Website Features for Food & Beverage Brands 2025](https://theartlogic.com/top-10-food-beverage-website-design-trends-2025/)
- [18 Essential Features for Food E-commerce](https://commercebuild.com/blog/18-essential-features-every-food-and-beverage-ecommerce-site-needs/)
- [SEO for Food Bloggers 2025 Guide](https://www.clickrank.ai/seo-for-food-bloggers-guide/)
- [Recipe Blog SEO - Bootstrapped Ventures](https://bootstrapped.ventures/seo-for-food-blogs/)
- [Food Blog SEO Tips - Foodie Digital](https://foodiedigital.com/seo-tips-for-food-bloggers/)
- [Vegan Digital Marketing Strategies](https://bnevol.com/blog/vegan-digital-marketing/8-impactful-digital-marketing-strategies-for-vegan-businesses)
- [Newsletter Signup Best Practices - Moosend](https://moosend.com/blog/newsletter-signup-examples/)
- [Growing Food Blog Email List - Real Balanced](https://realbalanced.com/blog/business/double-your-food-blogs-email-list/)
- [Restaurant Pickup Best Practices - Square](https://squareup.com/us/en/the-bottom-line/inside-square/square-online-restaurants-pickup-and-delivery-best-practices)
- [Przelewy24 Guide - Noda](https://noda.live/articles/przelewy24-guide)
- [Minimalist Baker](https://minimalistbaker.com/) and [Deliciously Ella](https://deliciouslyella.com/) as competitor references
