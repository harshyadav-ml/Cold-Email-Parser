---
name: Obsidian Precision
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#1f1f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c4c7c8'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#303030'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  inverse-primary: '#5d5f5f'
  secondary: '#c7c6c6'
  on-secondary: '#2f3131'
  secondary-container: '#484949'
  on-secondary-container: '#b8b8b8'
  tertiary: '#ffffff'
  on-tertiary: '#2f3131'
  tertiary-container: '#e2e2e2'
  on-tertiary-container: '#636565'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c7'
  on-primary-fixed: '#1a1c1c'
  on-primary-fixed-variant: '#454747'
  secondary-fixed: '#e3e2e2'
  secondary-fixed-dim: '#c7c6c6'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#464747'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#131313'
  on-background: '#e2e2e2'
  surface-variant: '#353535'
typography:
  display:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 52px
    letterSpacing: -0.04em
  display-mobile:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.03em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 38px
    letterSpacing: -0.03em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 30px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 26px
    letterSpacing: -0.02em
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: -0.01em
  code-inline:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: -0.01em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-tablet: 2rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

This design system embodies technical minimalism, speed, and precision engineering. Tailored for infrastructure tools, high-scale developer platforms, and technical operators, the aesthetic removes all decorative noise in favor of stark contrast, density, and functional hierarchy. 

The aesthetic draws from contemporary developer-first paradigms: pitch-black canvases, razor-thin translucent borders, dense typography, and mechanical utilitarianism. The emotional resonance should be silent authority, absolute stability, and uncompromising performance. Color is not used for aesthetic adornment; it is reserved exclusively for real-time telemetry, terminal logs, and system status states.

## Colors

The palette operates on strict monochrome values with structural surface tiers and precise functional indicators:

- **Base Canvas (`#000000`):** Pitch-black root environment.
- **Surface Elevation 1 (`#0A0A0A`):** Primary containment tier for sidebars, floating overlays, and large sections.
- **Surface Elevation 2 (`#121212`):** Elevated cards, interactive segments, dropdown menus, and nested panels.
- **Surface Elevation 3 (`#1A1A1A`):** Hover states, active tabs, and tertiary controls.
- **Primary / Foreground (`#FFFFFF`):** Maximum contrast foreground for primary action elements, key metrics, and headlines.
- **Secondary Foreground (`#EDEDED`):** High-readability body copy.
- **Muted Foreground (`#A1A1A1`):** Informational subtext, secondary labels, and meta captions.
- **Subtle Muted (`#525252`):** Disabled states, keyboard hints, and placeholder text.
- **Borders (`rgba(255, 255, 255, 0.08)`):** Single-pixel, low-alpha boundary lines. Interactive hover borders elevate to `rgba(255, 255, 255, 0.18)`.
- **Status Accents:** Exclusively dedicated to state:
  - **Live / Operational:** `#00E599` (Emerald with subtle matching outer glow)
  - **Warning / Degraded:** `#F5A623` (Amber)
  - **Critical / Failed:** `#FF0055` (Carmine Red)
  - Purple, indigo, and decorative accent gradients are strictly forbidden across the system.

## Typography

Typography relies on sharp geometric tracking and dense vertical rhythm. Headlines use tight negative tracking (`-0.02em` to `-0.04em`) to establish crisp editorial authority. All metadata, configuration keys, API parameters, timestamps, and live indicators shift to `JetBrains Mono` to enforce spatial clarity and tabular precision.

## Layout & Spacing

The structural layout utilizes a strict 12-column fluid grid bound inside a maximum container width of `1280px` for dashboards and documentation consoles.

- **Mobile (< 768px):** 4-column layout, edge margins of `1rem`, compact gutter spacing of `1rem`. Secondary analytical columns collapse into stacked linear views.
- **Tablet (768px – 1024px):** 8-column layout, edge margins of `2rem`, persistent collapsed navigation bar.
- **Desktop (> 1024px):** 12-column layout with 240px fixed utility sidebar, persistent header, and edge margins scaling up to `3rem`.

All internal element spacing follows a disciplined base-4 rhythmic scale.

## Elevation & Depth

Visual hierarchy is constructed entirely through tonal layering and hair-thin alpha outlines. Traditional heavy drop shadows are eradicated.

- **Depth by Pigment:** Depth is achieved by lightening surfaces as they rise above the pitch-black root (`#000000` base → `#0A0A0A` panel → `#121212` card → `#1A1A1A` hover state).
- **Hairline Outlines:** All elevated containers must feature a uniform `1px solid rgba(255, 255, 255, 0.08)` border.
- **Transient Layers (Modals / Menus):** Overlays apply a 12px backdrop blur (`backdrop-blur-md`) with `rgba(0, 0, 0, 0.75)` masking and a subtle ambient occlusion shadow (`0px 16px 32px rgba(0, 0, 0, 0.8)`).
- **Luminescence:** Interactive hover targets can project an internal gradient border highlight (`linear-gradient(to bottom, rgba(255,255,255,0.15), rgba(255,255,255,0.02))`) to simulate top-down hardware illumination.

## Shapes

The design system employs a soft-industrial radius standard:
- Default elements (buttons, text inputs, segmented pills, badge containers) utilize `0.25rem` (`4px` / `rounded-sm` to `rounded`).
- Parent containers, structural dashboard cards, and modal sheets scale to `0.5rem` (`8px` / `rounded-lg`).
- Status dots and binary user avatars are strictly circular (`rounded-full`).

## Components

### Buttons
- **Primary:** Solid `#FFFFFF` background with pitch-black text (`#000000`), weight 500. On hover, background shifts to `#E5E5E5`. Active state translates scale to `0.98`.
- **Secondary:** Surface `#0A0A0A`, border `1px solid rgba(255, 255, 255, 0.08)`, text `#EDEDED`. Hover elevates surface to `#121212` with border shifting to `rgba(255, 255, 255, 0.18)`.
- **Ghost:** Background transparent, text `#A1A1A1`. Hover triggers text `#FFFFFF` and surface `rgba(255, 255, 255, 0.05)`.

### Status Indicators
- Discrete `6px` by `6px` circular nodes (`rounded-full`).
- **Operational:** Background `#00E599` paired with an outer box-shadow ring: `box-shadow: 0 0 8px rgba(0, 229, 153, 0.45)`.
- **Warning:** Background `#F5A623`, ring `box-shadow: 0 0 8px rgba(245, 166, 35, 0.45)`.
- **Offline / Stale:** Solid `#525252`, no glow.

### Cards & Panels
- Rendered with background `#0A0A0A`, wrapped in a crisp `1px solid rgba(255, 255, 255, 0.08)` border. Nested analytical cards use `#121212`. Hover states on interactive cards adjust border color to `rgba(255, 255, 255, 0.2)` without moving the element.

### Inputs & Form Fields
- Height `36px`, surface `#000000`, border `1px solid rgba(255, 255, 255, 0.12)`, font `Geist` 14px text `#EDEDED`.
- Focus state eliminates standard browser outlines and applies a high-contrast `1px solid #FFFFFF` border accompanied by an inner hairline border ring.

### Checkboxes & Radios
- Box dimensions `14px x 14px`, surface `#000000`, border `1px solid rgba(255, 255, 255, 0.2)`. Selected state fills solid `#FFFFFF` with pitch-black interior glyph.

### Code & Terminal Blocks
- Pitch-black (`#000000`) viewport lined with `1px solid rgba(255, 255, 255, 0.08)`. Text rendered via `JetBrains Mono` 13px at line-height 20px. Action header carries tab headers separated by vertical single-pixel dividers and an action trigger for raw clipboard copy.