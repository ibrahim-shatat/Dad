---
name: Executive Command
colors:
  surface: '#fbf9f9'
  surface-dim: '#dbdad9'
  surface-bright: '#fbf9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#e9e8e7'
  surface-container-highest: '#e3e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#464555'
  inverse-surface: '#303031'
  inverse-on-surface: '#f2f0f0'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#4648d4'
  on-secondary: '#ffffff'
  secondary-container: '#6063ee'
  on-secondary-container: '#fffbff'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#fbf9f9'
  on-background: '#1b1c1c'
  surface-variant: '#e3e2e2'
typography:
  display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

The design system embodies a "Dad Executive Interface" philosophy: a modern, high-utility SaaS environment that prioritizes calmness, clarity, and quiet authority. It is tailored for high-stakes decision-making where information density must be balanced with visual breathing room.

The aesthetic blends **Modern Corporate** with a refined **Card-based** layout. It avoids trend-chasing in favor of timeless professional reliability. The interface uses a systematic approach to density, ensuring that power users feel efficient while casual users feel guided. The emotional response should be one of "controlled precision"—like a high-end physical desk or a well-organized leather planner.

## Colors

This design system utilizes a sophisticated, high-contrast palette optimized for legibility and focus. 

- **Primary:** Deep Indigo (#4F46E5) serves as the core brand anchor, used for primary actions, active states, and critical wayfinding.
- **Surface Strategy:** In light mode, surfaces use pure white against a near-white background (#FAFAFA). In dark mode, surfaces are elevated to #17171C against a near-black foundation (#0B0B0F).
- **AI Moments:** AI-driven features are distinguished by a subtle indigo tint (5% opacity) and the inclusion of a sparkle icon to signal intelligent assistance without breaking the professional flow.
- **Semantic Logic:** Green (#16A34A) is reserved for completed or ready states; Red (#EF4444) for failures or overdue tasks; and Amber (#F59E0B) for medium-urgency pending items.

## Typography

The typography system is built exclusively on **Inter** to maximize cross-platform legibility and systematic "tech-native" aesthetics. 

- **Weight Usage:** Use Semibold (600) for headlines to provide a firm visual anchor. Use Medium (500) for interactive labels and Regular (400) for long-form body text.
- **Spacing:** Negative letter spacing is applied to larger headlines to maintain a tight, "executive" feel.
- **Labels:** Small labels use a slight tracking increase and uppercase transform to create clear differentiation from body text when used in data-heavy views.

## Layout & Spacing

The layout philosophy follows a **fixed-fluid hybrid grid**. Content is generally housed within a 12-column grid with a maximum container width of 1280px to prevent excessive line lengths on ultra-wide monitors.

- **Rhythm:** An 8px linear scale (with a 4px step for micro-adjustments) governs all padding and margins. 
- **Margins:** Desktop views utilize 24px (lg) gutters and margins. Mobile views collapse margins to 16px (md) and switch to a single-column reflow for card stacks.
- **Executive Density:** Use "lg" (24px) spacing between major sections to reduce cognitive load, while using "sm" (8px) within card elements to maintain information density.

## Elevation & Depth

Visual hierarchy is established through a combination of **Tonal Layers** and **Soft Shadows**. 

1. **Level 0 (Background):** The base canvas (#FAFAFA / #0B0B0F).
2. **Level 1 (Cards):** Surfaces (#FFFFFF / #17171C) featuring a "hairline border" (1px width, 10% opacity black or 20% opacity white). 
3. **Shadows:** Cards use a "soft low shadow"—a double-layered drop shadow:
   - Layer 1: 0px 1px 2px rgba(0, 0, 0, 0.05)
   - Layer 2: 0px 4px 6px rgba(0, 0, 0, 0.03)
4. **Interactivity:** On hover, cards may subtly lift by increasing shadow diffusion, but never through color changes of the surface itself. This preserves the "stable" executive feel.

## Shapes

The design system uses a **Rounded** (Level 2) shape language to soften the industrial nature of a data-heavy SaaS tool.

- **Standard Radius:** 8px (0.5rem) for cards, input fields, and primary buttons.
- **Large Radius:** 16px (1rem) for decorative elements or modal containers.
- **Icons:** Use Lucide-style line icons with a 2px stroke width and slightly rounded caps to match the UI's geometry.

## Components

- **Buttons:** Primary buttons are solid Deep Indigo with white text. Secondary buttons use the hairline border with primary text. All buttons have an 8px radius.
- **Cards:** The fundamental building block. Must include a 1px hairline border and the defined soft low shadow. 
- **Inputs:** Fields use a light gray stroke in light mode (increasing to primary indigo on focus) and a dark gray stroke in dark mode. 
- **Chips/Badges:** Small 4px radius or fully pill-shaped. Use semantic colors with a 10% background tint and 100% stroke/text color for high legibility.
- **Lists:** Clean, unbordered rows within cards, separated by a 1px horizontal rule. 
- **AI Tooltips/Modals:** Features a 1px Indigo stroke and a sparkle icon in the header to indicate "Executive Assistance" mode.
- **Executive Dashboard:** A specialized component layout featuring a "Topline Metric" row of 4 small cards followed by a "Main Focus" 2/3 width card and a "Sidebar Activity" 1/3 width card.