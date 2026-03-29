# Design System Strategy: The Synthetic Intelligence Interface

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Tactical HUD."** 

This is not a traditional website or SaaS dashboard; it is a high-fidelity command center designed for the modern security specialist. We are moving away from the "flat web" by embracing depth, light refraction, and technical density. The goal is to create an immersive, high-stakes environment where data feels "projected" onto layers of deep-sea glass. 

By utilizing intentional asymmetry, we mirror the non-linear nature of hacking and network security. We break the grid by allowing tactical overlays to float above core data streams, using heavy backdrop blurs to maintain legibility without sacrificing the complexity of the "Kali Linux" inspired aesthetic. Every pixel must feel intentional, technical, and premium.

---

## 2. Colors & Surface Logic
The palette is rooted in the "Deep Navy" spectrum, utilizing luminance rather than saturation to define importance.

### Palette Roles
- **Primary (`#b4c5ff`):** Use for high-priority interactive elements.
- **Secondary (`#a2e7ff` / `#00D4FF`):** Reserved for system-active states and data highlights.
- **Tertiary (`#00daf3`):** Precision accents and cyber-glows.
- **Surface (`#111417`):** The foundational void upon which all glass panels sit.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for structural sectioning. Boundaries between sections must be defined by **background color shifts**. Use the `surface-container` tiers (Lowest to Highest) to delineate areas. A `surface-container-low` panel sitting on a `surface` background provides all the separation needed through tonal contrast.

### The "Glass & Gradient" Rule
Floating panels must use the **Tactical Glass** formula:
- **Background:** `rgba(10, 15, 30, 0.6)`
- **Blur:** `backdrop-filter: blur(20px);`
- **Border:** A 1px "Ghost Border" using a linear gradient: `linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(0, 212, 255, 0) 100%)`.

### Surface Hierarchy
Nesting is the key to depth. An inner data log should sit in a `surface-container-highest` box inside a `surface-container-low` panel. This creates a "recessed" or "tactical" feel without adding visual noise.

---

## 3. Typography
The typography strategy balances high-end editorial flair with brutalist technical precision.

- **Display & Headlines (Space Grotesk):** This typeface provides a futuristic, wide-aperture look. Use `display-lg` for system titles to establish an authoritative tone. Use `headline-sm` for section headers, always in Uppercase with `0.05em` letter-spacing.
- **Data & Logs (JetBrains Mono):** For all terminal outputs, code snippets, and raw metrics. This font ensures every character is distinct—critical for security environments.
- **Body & Titles (Inter):** The "workhorse" for descriptive text. It is neutral and highly legible, allowing the more characterful fonts to stand out.

---

## 4. Elevation & Depth
In a tactical HUD, depth is information.

- **The Layering Principle:** Instead of shadows, use **Tonal Layering**. Stack `surface-container-lowest` on `surface` to create a "sunken" terminal feel.
- **Ambient Glows:** When a panel needs to "float" (e.g., a critical alert), do not use a black drop-shadow. Instead, use a **diffused cyan glow**: `box-shadow: 0 0 30px rgba(0, 212, 255, 0.08)`. This mimics light emitting from the screen.
- **Asymmetric Depth:** Allow certain HUD elements to overlap. A terminal window might partially cover a secondary data feed, with the `backdrop-blur` creating a beautiful, refracted view of the data beneath.

---

## 5. Components

### Buttons
- **Primary:** Filled with `primary` (`#b4c5ff`), text in `on-primary` (`#002a77`). 0px border radius. On hover, add a subtle Cyan outer glow.
- **Ghost (Tertiary):** No fill. 1px gradient border (Cyan to Transparent). Use for secondary actions like "View Logs."

### Tactical Chips
- Use `0px` radius.
- **Active:** `secondary-container` fill with `on-secondary-container` text.
- **Static:** `surface-container-high` background with `on-surface-variant` text.

### Input Fields
- Underlined only, or 1px Ghost Border. 
- Background: `surface-container-lowest`. 
- Focus state: The bottom border transitions to a full `tertiary` (`#00daf3`) glow.

### Terminal & Lists
- **Forbid Divider Lines.** Use the **Spacing Scale** (specifically `spacing.4` or `spacing.6`) to separate list items. 
- Alternate background shades (`surface-container-low` vs `surface-container-high`) for row zebra-striping in dense data tables.

### Additional Component: The "Pulse Indicator"
- A small 4px circle using `tertiary` with a CSS animation `scale` and `opacity` to indicate live system monitoring or active "listening" states.

---

## 6. Do's and Don'ts

### Do:
- **Use "Space Grotesk" for numbers** in dashboards to give them a high-fidelity, machined look.
- **Embrace "Hard" Edges.** All corners must be `0px`. Roundness suggests consumer-grade friendliness; sharp edges suggest professional-grade precision.
- **Leverage Asymmetry.** Place a small, high-density data widget in the corner of a large, breathing hero area to create a "pro-tool" feel.

### Don't:
- **Never use 100% opaque borders.** They break the immersion of the glass effect.
- **Don't use standard shadows.** If an element feels "flat," increase the backdrop blur or the tonal difference of the surface—do not reach for a `drop-shadow: #000`.
- **Avoid color overload.** 90% of your UI should be Deep Navy and Glass. Use `Electric Blue` and `Cyan` sparingly—only for things that are "on," "active," or "critical."