---
name: Dad Executive Interface
colors:
  surface: '#fbf8ff'
  surface-dim: '#dad9e3'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f2fd'
  surface-container: '#eeedf7'
  surface-container-high: '#e8e7f1'
  surface-container-highest: '#e3e1ec'
  on-surface: '#1a1b22'
  on-surface-variant: '#464555'
  inverse-surface: '#2f3038'
  inverse-on-surface: '#f1effa'
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
  background: '#fbf8ff'
  on-background: '#1a1b22'
  surface-variant: '#e3e1ec'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-page: 40px
  container-max: 1440px
  card-padding: 20px
---

## Brand & Style
The design system is anchored in a philosophy of "Reliable Clarity." It targets high-level executives and power users who require an AI assistant that feels like a quiet, high-end workspace rather than a distracting tool. 

The aesthetic blends **Modern Corporate** efficiency with **Minimalist** warmth. It takes inspiration from the precision of developer tools but softens the edges for a more executive appeal. The UI utilizes a card-based architecture to compartmentalize complex AI data into digestible, calm units of information. The emotional response should be one of immediate competence, focus, and trust.

## Colors
The palette is centered around a **Deep Indigo** primary, representing intelligence and stability. 

- **Primary:** Used for actionable states, active indicators, and high-priority branding moments.
- **Backgrounds:** The "Near-white" and "Near-black" foundations provide a low-glare canvas that reduces eye strain during long working sessions.
- **Surfaces:** Cards and modals use pure white in light mode and a slightly elevated gray in dark mode to create subtle separation from the canvas.
- **Borders:** All surfaces are defined by hairline borders (1px) rather than heavy shadows to maintain a crisp, structured feel.

## Typography
The typography uses **Inter** exclusively to leverage its exceptional legibility and systematic feel. 

The scale is intentionally conservative to avoid "loud" interfaces. Headlines use slightly tighter letter spacing and a semi-bold weight to feel authoritative. Body text remains generous in line height to facilitate the reading of long-form AI summaries and reports. Labels use a slight tracking increase when uppercase to differentiate them from interactive body text.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. The sidebar remains at a fixed width (260px) while the main content area expands within a 1440px container.

- **Grid:** A 12-column grid is used for the main dashboard view, with cards typically spanning 4, 6, or 12 columns.
- **Rhythm:** An 8px linear scale (4px, 8px, 16px, 24px, 32px, 48px, 64px) governs all padding and margins. 
- **Mobile:** On mobile devices, the 40px page margin shrinks to 16px, and all multi-column cards collapse into a single-column vertical stack.

## Elevation & Depth
Depth is achieved through **Tonal Layering** supplemented by ultra-soft shadows.

- **Base Layer:** The page background.
- **Surface Layer:** Cards and secondary navigation sit on this layer. They are defined by a 1px border (`border_light` or `border_dark`).
- **Raised Layer:** Modals, dropdowns, and tooltips. These use a "Soft Low Shadow" (0px 4px 12px rgba(0,0,0,0.05)) to suggest floating without creating visual noise.
- **Interactive Depth:** Buttons should not have heavy shadows; instead, they use subtle color shifts or a 1px inner highlight to appear slightly tactile.

## Shapes
The shape language is sophisticated and approachable. 
- **Standard Elements:** Buttons and input fields use a `0.5rem` (8px) radius.
- **Large Elements:** Dashboard cards and main container wrappers use a `1rem` (16px) radius to create a distinct "pod" feel for different AI modules.
- **Icons:** Use **Lucide-style** line icons with a 2px stroke width and slightly rounded caps to match the UI's rounded corners.

## Components
- **Buttons:** Primary buttons use the Indigo background with white text. Secondary buttons use a ghost style (border only) or a subtle gray fill.
- **Cards:** The core of the dashboard. Every card must have a consistent header (Title + Icon/Action) and 20px internal padding.
- **Inputs:** Clean, 1px bordered boxes that turn Indigo on focus. Labels should sit above the input in the `label-md` style.
- **Chips:** Used for "AI Status" or "Categories." These should have a light tinted background of the primary color with a slightly darker text (e.g., Indigo-50 background with Indigo-700 text).
- **Lists:** Clean rows with 12px vertical padding, separated by a 1px hairline divider. Hover states should use a subtle background tint change.
- **Navigation:** Vertical sidebar with clear icons. The "Active" state is indicated by a vertical 3px Indigo pill on the left edge and a weighted font.