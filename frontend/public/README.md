# Static Assets Location

## Where to place your hero-bg.jpg image:

Put your microchip background image here:
```
frontend/public/images/hero-bg.jpg
```

## How Next.js public directory works:

- Files in `public/` are served from the root URL `/`
- `public/images/hero-bg.jpg` → accessible at `/images/hero-bg.jpg`
- `public/favicon.ico` → accessible at `/favicon.ico`

## Image recommendations for hero-bg.jpg:

- **Dimensions**: 1920x1080 or higher for full-width backgrounds
- **Format**: JPG for photographs, PNG for graphics with transparency
- **File size**: Optimize to < 500KB for fast loading
- **Content**: Microchip/circuit board imagery works well with the site theme
- **Contrast**: Ensure text remains readable over the background (you can adjust the overlay opacity in the code)

## Other static assets you might want to add:

- `public/favicon.ico` - Browser tab icon
- `public/logo.png` - Company logo
- `public/images/` - Other images for docs, features, etc.

## If you want to adjust the background overlay:

In `frontend/app/page.tsx`, you can uncomment and adjust this line:
```jsx
<div className="absolute inset-0 bg-black/50 z-0"></div>
```

Change `bg-black/50` to:
- `bg-black/30` for lighter overlay
- `bg-black/70` for darker overlay
- `bg-white/20` for a light/bright overlay
