# Shadcn UI Integration

Integration of shadcn/ui components into the frontend, replacing custom Tailwind components with shadcn primitives and Phosphor icons.

## Purpose

Modernize the frontend UI by integrating shadcn/ui components with the existing codebase. This provides:
- Consistent design system with radix-lyra style
- Reusable component primitives
- Light/dark mode support with stone color scheme
- Phosphor icons replacing emoji icons
- Upgraded dependencies (Next.js 16, React 19, Tailwind v4)

## Code Location

- **UI Components**: `frontend/components/ui/`
- **Utility Functions**: `frontend/lib/utils.ts`
- **Configuration**: `frontend/` (root level config files)
- **Updated Component**: `frontend/app/components/query/QueryInterface.tsx`

## Implementation Steps

### Phase 1: Dependencies & Configuration Updates

#### 1.1 Update package.json

**File**: `frontend/package.json`

Replace entire file content with:

```json
{
  "name": "story-thread-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "@base-ui/react": "^1.1.0",
    "@phosphor-icons/react": "^2.1.10",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "next": "16.1.6",
    "radix-ui": "^1.4.3",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "shadcn": "^3.8.1",
    "tailwind-merge": "^3.4.0",
    "tw-animate-css": "^1.4.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.1.6",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
```

**Key Changes**:
- Keep original name: "story-thread-frontend"
- Upgrade Next.js: 14.1.0 → 16.1.6
- Upgrade React: 18.2.0 → 19.2.3
- Upgrade Tailwind: 3.4.1 → 4
- Add shadcn dependencies
- Change lint script from "next lint" to "eslint"

#### 1.2 Update tsconfig.json

**File**: `frontend/tsconfig.json`

Replace entire file with:

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.mts"
  ],
  "exclude": ["node_modules"]
}
```

**Key Changes**:
- Add "target": "ES2017"
- Change jsx: "preserve" → "react-jsx"
- Add ".next/dev/types/**/*.ts" and "**/*.mts" to includes

#### 1.3 Create/Update next.config.ts

**File**: `frontend/next.config.ts` (new file, replace next.config.js)

Create with this content (preserving API rewrites):

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
```

**Action**: Delete `frontend/next.config.js` after creating `next.config.ts`

#### 1.4 Create components.json

**File**: `frontend/components.json` (new file)

Create with:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "radix-lyra",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "stone",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "phosphor",
  "rtl": false,
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "menuColor": "default",
  "menuAccent": "subtle",
  "registries": {}
}
```

#### 1.5 Update postcss.config.mjs

**File**: `frontend/postcss.config.mjs` (replace postcss.config.js)

Create with:

```javascript
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
```

**Action**: Delete `frontend/postcss.config.js` after creating `postcss.config.mjs`

#### 1.6 Create eslint.config.mjs

**File**: `frontend/eslint.config.mjs` (new file)

Create with:

```javascript
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
```

#### 1.7 Install Dependencies

Run in `frontend/` directory:

```bash
npm install
```

### Phase 2: Core Infrastructure

#### 2.1 Create lib/utils.ts

**File**: `frontend/lib/utils.ts` (new file)

Create with:

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

#### 2.2 Update app/globals.css

**File**: `frontend/app/globals.css`

Replace entire content with:

```css
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: var(--font-sans);
  --font-mono: var(--font-geist-mono);
  --color-sidebar-ring: var(--sidebar-ring);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar: var(--sidebar);
  --color-chart-5: var(--chart-5);
  --color-chart-4: var(--chart-4);
  --color-chart-3: var(--chart-3);
  --color-chart-2: var(--chart-2);
  --color-chart-1: var(--chart-1);
  --color-ring: var(--ring);
  --color-input: var(--input);
  --color-border: var(--border);
  --color-destructive: var(--destructive);
  --color-accent-foreground: var(--accent-foreground);
  --color-accent: var(--accent);
  --color-muted-foreground: var(--muted-foreground);
  --color-muted: var(--muted);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-secondary: var(--secondary);
  --color-primary-foreground: var(--primary-foreground);
  --color-primary: var(--primary);
  --color-popover-foreground: var(--popover-foreground);
  --color-popover: var(--popover);
  --color-card-foreground: var(--card-foreground);
  --color-card: var(--card);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
  --radius-2xl: calc(var(--radius) + 8px);
  --radius-3xl: calc(var(--radius) + 12px);
  --radius-4xl: calc(var(--radius) + 16px);
}

:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.147 0.004 49.25);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.147 0.004 49.25);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.147 0.004 49.25);
  --primary: oklch(0.216 0.006 56.043);
  --primary-foreground: oklch(0.985 0.001 106.423);
  --secondary: oklch(0.97 0.001 106.424);
  --secondary-foreground: oklch(0.216 0.006 56.043);
  --muted: oklch(0.97 0.001 106.424);
  --muted-foreground: oklch(0.553 0.013 58.071);
  --accent: oklch(0.97 0.001 106.424);
  --accent-foreground: oklch(0.216 0.006 56.043);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.923 0.003 48.717);
  --input: oklch(0.923 0.003 48.717);
  --ring: oklch(0.709 0.01 56.259);
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
  --radius: 0.625rem;
  --sidebar: oklch(0.985 0.001 106.423);
  --sidebar-foreground: oklch(0.147 0.004 49.25);
  --sidebar-primary: oklch(0.216 0.006 56.043);
  --sidebar-primary-foreground: oklch(0.985 0.001 106.423);
  --sidebar-accent: oklch(0.97 0.001 106.424);
  --sidebar-accent-foreground: oklch(0.216 0.006 56.043);
  --sidebar-border: oklch(0.923 0.003 48.717);
  --sidebar-ring: oklch(0.709 0.01 56.259);
}

.dark {
  --background: oklch(0.147 0.004 49.25);
  --foreground: oklch(0.985 0.001 106.423);
  --card: oklch(0.216 0.006 56.043);
  --card-foreground: oklch(0.985 0.001 106.423);
  --popover: oklch(0.216 0.006 56.043);
  --popover-foreground: oklch(0.985 0.001 106.423);
  --primary: oklch(0.923 0.003 48.717);
  --primary-foreground: oklch(0.216 0.006 56.043);
  --secondary: oklch(0.268 0.007 34.298);
  --secondary-foreground: oklch(0.985 0.001 106.423);
  --muted: oklch(0.268 0.007 34.298);
  --muted-foreground: oklch(0.709 0.01 56.259);
  --accent: oklch(0.268 0.007 34.298);
  --accent-foreground: oklch(0.985 0.001 106.423);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.553 0.013 58.071);
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
  --sidebar: oklch(0.216 0.006 56.043);
  --sidebar-foreground: oklch(0.985 0.001 106.423);
  --sidebar-primary: oklch(0.488 0.243 264.376);
  --sidebar-primary-foreground: oklch(0.985 0.001 106.423);
  --sidebar-accent: oklch(0.268 0.007 34.298);
  --sidebar-accent-foreground: oklch(0.985 0.001 106.423);
  --sidebar-border: oklch(1 0 0 / 10%);
  --sidebar-ring: oklch(0.553 0.013 58.071);
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

**Note**: This is Tailwind v4 syntax with @import instead of @tailwind directives.

#### 2.3 Update app/layout.tsx

**File**: `frontend/app/layout.tsx`

Replace with:

```typescript
import type { Metadata } from "next";
import { Geist, Geist_Mono, DM_Sans } from "next/font/google";
import "./globals.css";

const dmSans = DM_Sans({subsets:['latin'],variable:'--font-sans'});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: 'Story Thread Surfacing',
  description: 'Identify and resurface historical Atlantic stories',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={dmSans.variable}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
```

**Key Changes**:
- Import fonts (DM_Sans, Geist, Geist_Mono)
- Add font variables to html and body
- Preserve existing metadata
- Convert to TypeScript with proper typing
- Change function signature to use Readonly

### Phase 3: Component Migration

#### 3.1 Copy UI Components

Copy these 14 files from `frontend/shadcn-create-output/components/ui/` to `frontend/components/ui/`:

1. `alert-dialog.tsx`
2. `badge.tsx`
3. `button.tsx`
4. `card.tsx`
5. `combobox.tsx`
6. `dropdown-menu.tsx`
7. `field.tsx`
8. `input-group.tsx`
9. `input.tsx`
10. `label.tsx`
11. `select.tsx`
12. `separator.tsx`
13. `textarea.tsx`

**Command to copy all at once**:

```bash
cp frontend/shadcn-create-output/components/ui/*.tsx frontend/components/ui/
```

### Phase 4: Update QueryInterface Component

#### 4.1 Replace QueryInterface.tsx

**File**: `frontend/app/components/query/QueryInterface.tsx`

Replace entire content with:

```typescript
'use client';

import { useState } from 'react';
import { MagnifyingGlassIcon, ArticleIcon, LightbulbIcon } from '@phosphor-icons/react';
import { analyzeText, analyzeArticle, getProactiveSuggestions } from '@/app/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';

export default function QueryInterface() {
  const [activeTab, setActiveTab] = useState<'text' | 'article'>('text');
  const [text, setText] = useState('');
  const [articleId, setArticleId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTextSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeText(text);
      console.log('Analysis result:', result);
      // TODO: Update results panel
    } catch (error) {
      console.error('Error analyzing text:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleArticleSubmit = async () => {
    if (!articleId.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeArticle(articleId);
      console.log('Article analysis result:', result);
      // TODO: Update results panel
    } catch (error) {
      console.error('Error analyzing article:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProactiveTrigger = async () => {
    setLoading(true);
    try {
      const result = await getProactiveSuggestions();
      console.log('Proactive suggestions:', result);
      // TODO: Update results panel
    } catch (error) {
      console.error('Error getting proactive suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MagnifyingGlassIcon className="size-4" />
          Input
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Tabs */}
        <div className="flex space-x-1 bg-muted p-1 rounded-lg">
          <Button
            onClick={() => setActiveTab('text')}
            variant={activeTab === 'text' ? 'default' : 'ghost'}
            className="flex-1"
          >
            Text
          </Button>
          <Button
            onClick={() => setActiveTab('article')}
            variant={activeTab === 'article' ? 'default' : 'ghost'}
            className="flex-1"
          >
            Article ID
          </Button>
        </div>

        {/* Text Input */}
        {activeTab === 'text' && (
          <div className="space-y-4">
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste article content or draft here..."
              className="min-h-48"
            />
            <Button
              onClick={handleTextSubmit}
              disabled={loading || !text.trim()}
              className="w-full"
            >
              {loading ? 'Analyzing...' : 'Find Connections'}
            </Button>
          </div>
        )}

        {/* Article ID Input */}
        {activeTab === 'article' && (
          <div className="space-y-4">
            <Input
              value={articleId}
              onChange={(e) => setArticleId(e.target.value)}
              placeholder="Enter article ID (e.g., atlantic_12345)"
            />
            <Button
              onClick={handleArticleSubmit}
              disabled={loading || !articleId.trim()}
              className="w-full"
            >
              {loading ? 'Analyzing...' : 'Analyze Article'}
            </Button>
          </div>
        )}

        {/* Divider */}
        <Separator />

        {/* Proactive Button */}
        <Button
          onClick={handleProactiveTrigger}
          disabled={loading}
          variant="secondary"
          className="w-full"
        >
          <LightbulbIcon className="mr-2 size-4" />
          {loading ? 'Scanning...' : 'Scan Proactive Suggestions'}
        </Button>
      </CardContent>
    </Card>
  );
}
```

**Key Changes**:
- Import Phosphor icons (MagnifyingGlassIcon, LightbulbIcon) to replace emojis
- Import shadcn components (Button, Card, Input, Textarea, Separator)
- Replace emoji (🔍) with MagnifyingGlassIcon
- Replace custom buttons with Button component
- Replace textarea with Textarea component
- Replace input with Input component
- Replace card div structure with Card/CardHeader/CardTitle/CardContent
- Replace custom divider with Separator component
- Add LightbulbIcon to proactive button for better UX
- Use proper button variants (default, ghost, secondary)
- Add proper spacing and sizing classes

### Phase 5: Testing & Verification

#### 5.1 Build Verification

Run these commands in `frontend/` directory:

```bash
# Check for TypeScript errors
npm run build

# Run linting
npm run lint

# Start development server
npm run dev
```

#### 5.2 Manual Verification Checklist

- [ ] Development server starts without errors
- [ ] QueryInterface renders correctly with shadcn components
- [ ] Text/Article ID tabs switch properly
- [ ] Text input and button work
- [ ] Article ID input and button work
- [ ] Proactive suggestions button works
- [ ] Icons display correctly (MagnifyingGlassIcon, LightbulbIcon)
- [ ] Loading states work on all buttons
- [ ] Dark mode toggles correctly (if implemented)
- [ ] Console has no errors

#### 5.3 API Rewrite Verification

Verify backend API still works by checking browser console for successful API calls:
- `/api/v1/analyze/text`
- `/api/v1/analyze/article`
- `/api/v1/proactive-suggestions`

### Phase 6: Cleanup

#### 6.1 Remove shadcn-create-output Directory

```bash
rm -rf frontend/shadcn-create-output
```

#### 6.2 Update spec/index.md

**File**: `spec/index.md`

Add entry to the table:

| Document | Code | Purpose |
|----------|------|---------|
| | | (existing entries...) |
| [Shadcn UI Integration](shadcn-ui-integration.md) | `frontend/components/ui/`, `frontend/lib/utils.ts` | Integration of shadcn/ui components with radix-lyra style, Phosphor icons, and stone color scheme. Upgrades Next.js to 16, React to 19, Tailwind to v4, and updates QueryInterface to use shadcn primitives. |

## Important Notes

### Compatibility Considerations

1. **Tailwind v4 Syntax**: Uses @import instead of @tailwind directives. Verify custom Tailwind classes still work.

2. **Next.js 16 Breaking Changes**: Check all Next.js-specific features (API routes, rewrites, etc.) still work.

3. **React 19 Internal Changes**: Test all React components for compatibility, especially with React Server Components.

4. **Path Aliases**: @/* imports should work with tsconfig paths configuration.

### Preserved Elements

- API rewrite configuration in next.config.ts
- Existing `app/components/blocks/` structure
- Existing `app/components/results/` structure
- All business logic in components
- Makefile scripts

### Future Enhancements

After this integration:
- Consider migrating block components to shadcn patterns
- Add more shadcn components (Tabs, Dialog, etc.)
- Implement dark mode toggle
- Add more Phosphor icons throughout the app
- Consider Form components from shadcn for better form handling

## References

- Source files: `frontend/shadcn-create-output/`
- shadcn/ui documentation: https://ui.shadcn.com
- Phosphor icons: https://phosphoricons.com
- Next.js 16 docs: https://nextjs.org/docs
- Tailwind CSS v4 docs: https://tailwindcss.com/blog/tailwindcss-v4-alpha
