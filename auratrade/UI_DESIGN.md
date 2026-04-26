# AuraTrade Dashboard — Complete UI Specification

## Document Version: 1.0
## Author: Senior Fintech UI/UX Designer
## Date: 2025-01-20
## Classification: Design Specification for Streamlit Implementation

---

# Table of Contents

1. [Design System Overview](#1-design-system-overview)
2. [Color Tokens & Typography](#2-color-tokens--typography)
3. [Glassmorphism Specification](#3-glassmorphism-specification)
4. [Dashboard Layout Diagram](#4-dashboard-layout-diagram)
5. [Component Specifications](#5-component-specifications)
6. [Complete Streamlit CSS Code](#6-complete-streamlit-css-code)
7. [Streamlit Layout Code](#7-streamlit-layout-code)
8. [Animation & Interaction Specs](#8-animation--interaction-specs)
9. [Responsive Behavior](#9-responsive-behavior)
10. [Asset Checklist](#10-asset-checklist)

---

# 1. Design System Overview

AuraTrade is an **AI-powered futures trading assistant** targeting MES/MNQ micro-futures. The UI communicates **institutional-grade precision** with a **futuristic edge**. Every element reinforces trust, speed, and clarity.

## Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Clarity Under Pressure** | High-contrast colors, immediate visual hierarchy, critical data always visible |
| **Regime Communication** | Blue/Red color coding is the primary visual language — instant regime recognition |
| **Glassmorphism Depth** | Layered frosted glass panels create spatial hierarchy without heavy borders |
| **Motion With Purpose** | Animations only for state changes (regime toggle, entry triggers, alerts) |
| **Neon Accents** | Cyan and crimson glows draw attention to actionable elements |

## Mood Keywords
`Institutional` `Surgical` `Night-Mode` `Futures Pit` `Neon-Noir` `Glass-Dashboard`

---

# 2. Color Tokens & Typography

## Primary Palette

```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0e1a;           /* Deep navy black — main canvas */
  --bg-secondary: #111827;         /* Elevated panels */
  --bg-tertiary: #1a2332;          /* Hover states, inputs */
  --bg-glass: rgba(255,255,255,0.03); /* Glass panel fill */

  /* Accents — Blue Regime (Trend Runner) */
  --blue-primary: #00d4ff;         /* Neon cyan */
  --blue-glow: rgba(0, 212, 255, 0.4);
  --blue-dim: rgba(0, 212, 255, 0.15);
  --blue-dark: #007a99;

  /* Accents — Red Regime (Trap & Revert) */
  --red-primary: #ff3366;          /* Neon crimson */
  --red-glow: rgba(255, 51, 102, 0.4);
  --red-dim: rgba(255, 51, 102, 0.15);
  --red-dark: #cc0033;

  /* Functional Colors */
  --profit: #00ff88;               /* Neon green */
  --profit-dim: rgba(0, 255, 136, 0.15);
  --loss: #ff3366;                 /* Same as red-primary */
  --warning: #ffcc00;              /* Amber */
  --warning-dim: rgba(255, 204, 0, 0.15);
  --info: #00d4ff;                 /* Same as blue-primary */

  /* Text */
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --text-muted: rgba(255, 255, 255, 0.35);
  --text-inverse: #0a0e1a;

  /* Border & Shadow */
  --border-glass: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.15);
  --shadow-float: 0 8px 32px rgba(0, 0, 0, 0.4);
  --shadow-glow-blue: 0 0 20px rgba(0, 212, 255, 0.3);
  --shadow-glow-red: 0 0 20px rgba(255, 51, 102, 0.3);
  --shadow-inset: inset 0 1px 0 rgba(255,255,255,0.05);
}
```

## Typography

| Token | Font | Size | Weight | Letter-Spacing | Usage |
|-------|------|------|--------|---------------|-------|
| Display | Inter | 32px | 700 | -0.02em | Logo, main titles |
| H1 | Inter | 24px | 600 | -0.01em | Section headers |
| H2 | Inter | 18px | 600 | 0 | Card titles |
| Body | Inter | 14px | 400 | 0 | Primary text |
| Body-Small | Inter | 12px | 400 | 0.01em | Secondary text |
| Mono | SF Mono / JetBrains Mono | 14px | 500 | 0.02em | Prices, P&L, timestamps |
| Mono-Small | SF Mono / JetBrains Mono | 11px | 400 | 0.02em | Log entries |
| Badge | Inter | 10px | 700 | 0.05em | Labels, badges |

---

# 3. Glassmorphism Specification

The glassmorphism effect is the **signature visual element** of AuraTrade. Every panel uses this exact specification:

### Standard Glass Panel

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  padding: 16px;
  position: relative;
  overflow: hidden;
}

/* Subtle top-edge highlight for depth */
.glass-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 16px;
  right: 16px;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.15) 20%, 
    rgba(255, 255, 255, 0.15) 80%, 
    transparent
  );
}
```

### Elevated Glass Panel (for floating elements)

```css
.glass-panel-elevated {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  box-shadow: 
    0 12px 48px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  padding: 20px;
}
```

### Regime-Colored Glass Panel (active regime indicator)

```css
.glass-panel-blue {
  background: rgba(0, 212, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(0, 212, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.glass-panel-red {
  background: rgba(255, 51, 102, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 51, 102, 0.2);
  border-radius: 12px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(255, 51, 102, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
```

### Glass Button Base

```css
.glass-button {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.glass-button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.glass-button:active {
  transform: translateY(0);
  background: rgba(255, 255, 255, 0.04);
}
```

---

# 4. Dashboard Layout Diagram

## ASCII Layout — Desktop View (1440px+)

```
+===============================================================================+
|  HEADER BAR (Full Width, 70px height)                                           |
|  [AURA◆TRADE ════════════] [BAL: $50,000.00] [P&L: +$425.50 ▲] [● LIVE] [⏱ 4:32:15] |
+===============================================================================+
|                                                                               |
|  +=====================+  +=============================================+    |
|  | REGIME TOGGLE       |  | CONFIDENCE GAUGE                            |    |
|  |                     |  |                                             |    |
|  |  [BLUE ●━━━━━○ RED] |  |        ╭──────────╮                         |    |
|  |                     |  |       /   85%     \        S-Tier Signal   |    |
|  |  TREND RUNNER       |  |      /  ▲        \      8/11 Sessions    |    |
|  |  "Tuesday detected  |  |     ╰─────────────╯                         |    |
|  |   Mid-week expansion|  |  FVG ✓  VWAP ✓  Level ✓                      |    |
|  |   expected"         |  |                                             |    |
|  +=====================+  +=============================================+    |
|                                                                               |
|  +==========================================+  +==========================+   |
|  |                                          |  | LIVE JOURNAL             |   |
|  |      MAIN CHART AREA                     |  |                          |   |
|  |      (TradingView-like candlesticks)     |  | ▶ 14:35:12 LONG 2 MNQ    |   |
|  |                                          |  |   @ 26,382.50 → +$210    |   |
|  |   ━━━━━━━━━ London High (orange)       |  |   AI: Pattern #7 match   |   |
|  |   ─ ─ ─ 9-EMA (dotted white)             |  |   ✓ WIN                  |   |
|  |   〰 VWAP (yellow curve)                 |  |                          |   |
|  |   [▓▓▓] FVG Bullish (blue box)           |  | ▶ 10:22:45 SHORT 1 MES   |   |
|  |        ▲ Entry Arrow                     |  |   @ 5,842.00 → -$150     |   |
|  |                                          |  |   AI: Failed reclaim     |   |
|  |   Real-time: 26,384.75 ▲ +2.25           |  |   ✗ LOSS (Stop hit)      |   |
|  |                                          |  |                          |   |
|  +==========================================+  +==========================+   |
|                                                                               |
|  +=======================================================================+    |
|  | TRADE CONTROL PANEL                                                   |    |
|  |                                                                       |    |
|  |  [ ████████ ARM SYSTEM ████████ ]  [ POS: 2 MNQ LONG | P&L: +$210 ]   |    |
|  |                                                                       |    |
|  |  [CLOSE POSITION]  Auto-Trade: [● ON]  Confidence > [━━━●━━] 70%     |    |
|  |                                                                       |    |
|  |  Risk Guard: Daily Stop $300 | Max 2 Trades | Drawdown $2000          |    |
|  |                                                                       |    |
|  +=======================================================================+    |
|                                                                               |
|  +=======================================================================+    |
|  | SYSTEM LOG                                                            |    |
|  | 14:32:05 — FVG detected at 26,380. Waiting for retest...              |    |
|  | 14:35:12 — ENTRY TRIGGERED: LONG 2 MNQ @ 26,382.50                     |    |
|  | 14:35:45 — Stop placed @ 26,378.50 | Target 1: VWAP | Target 2: 1.5R  |    |
|  +=======================================================================+    |
|                                                                               |
+===============================================================================+
```

## Grid Specification

```
Dashboard Grid: 12-column
Header: 12 cols (full width)
Regime + Confidence: 4 cols + 8 cols
Chart + Journal: 8 cols + 4 cols
Trade Control: 12 cols
System Log: 12 cols
Gap between panels: 16px
Panel padding: 16px-20px
```

---

# 5. Component Specifications

## 5.1 Header Bar

**Dimensions:** Full width, 72px height, fixed position at top (z-index: 100)
**Background:** `--bg-secondary` with bottom border `1px solid rgba(255,255,255,0.06)`

### Elements (left to right):

| Element | Content | Style |
|---------|---------|-------|
| Logo | "AURA◆TRADE" | Font: Inter 20px bold, letter-spacing: 0.1em. "◆" uses regime color (blue/red). Text has subtle text-shadow glow matching regime |
| Divider | Vertical line | `1px solid var(--border-glass)`, height 32px, margin 0 20px |
| Balance | "BAL: $50,000.00" | Font: Mono 16px, color: `--text-primary`. Label in `--text-secondary` |
| P&L | "+$425.50 ▲" | Font: Mono 18px bold. Color: `--profit` when positive, `--loss` when negative. Arrow icon (▲/▼) |
| Connection | "● LIVE" or "● OFFLINE" | Green dot: `0 0 8px var(--profit)` with pulse animation. Red dot: solid red. Text: 12px uppercase |
| Timer | "⏱ 04:32:15" | Mono font, `--text-secondary`. Countdown to 16:00 EST market close |

### Streamlit Implementation:

```python
# Header Bar Layout
header_cols = st.columns([3, 2, 2, 1, 1, 1])

with header_cols[0]:
    st.markdown("""
        <div class="logo-container">
            <span class="logo-text">AURA<span class="logo-diamond">◆</span>TRADE</span>
        </div>
    """, unsafe_allow_html=True)

with header_cols[1]:
    st.markdown("""
        <div class="header-metric">
            <span class="metric-label">BALANCE</span>
            <span class="metric-value">$50,000.00</span>
        </div>
    """, unsafe_allow_html=True)

with header_cols[2]:
    st.markdown("""
        <div class="header-metric">
            <span class="metric-label">DAILY P&L</span>
            <span class="metric-value profit">+$425.50 ▲</span>
        </div>
    """, unsafe_allow_html=True)

with header_cols[3]:
    st.markdown("""
        <div class="connection-status live">
            <span class="status-dot"></span> LIVE
        </div>
    """, unsafe_allow_html=True)

with header_cols[4]:
    st.markdown("""
        <div class="session-timer">
            <span class="timer-icon">⏱</span>
            <span class="timer-value">04:32:15</span>
        </div>
    """, unsafe_allow_html=True)
```

---

## 5.2 Regime Toggle (Red/Blue)

**Dimensions:** 100% width of its column, min-height 160px
**Container:** `.glass-panel` with regime-specific coloring when active

### Visual Design:

The toggle is a **large horizontal slider** with two states:

```
BLUE STATE:                    RED STATE:
+============================+ +============================+
| ● BLUE  ○ RED              | | ○ BLUE  ● RED              |
|                            | |                            |
|    ↗ TREND RUNNER ↗        | |    ↯ TRAP & REVERT ↯       |
|                            | |                            |
| "Tuesday detected —        | | "Friday detected —          |
|  Mid-week expansion        | |  End-of-week chop          |
|  expected"                 | |  expected"                 |
+============================+ +============================+
```

### CSS for Toggle:

```css
.regime-toggle-container {
  padding: 20px;
  border-radius: 12px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.regime-toggle-container.blue-active {
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.1);
}

.regime-toggle-container.red-active {
  background: rgba(255, 51, 102, 0.05);
  border: 1px solid rgba(255, 51, 102, 0.25);
  box-shadow: 0 0 30px rgba(255, 51, 102, 0.1);
}

.toggle-track {
  width: 100%;
  height: 44px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 22px;
  position: relative;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-knob {
  position: absolute;
  width: 50%;
  height: 40px;
  top: 2px;
  border-radius: 20px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.toggle-knob.blue {
  left: 2px;
  background: rgba(0, 212, 255, 0.2);
  color: var(--blue-primary);
  border: 1px solid rgba(0, 212, 255, 0.4);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}

.toggle-knob.red {
  right: 2px;
  background: rgba(255, 51, 102, 0.2);
  color: var(--red-primary);
  border: 1px solid rgba(255, 51, 102, 0.4);
  box-shadow: 0 0 15px rgba(255, 51, 102, 0.2);
}

.regime-title {
  font-size: 20px;
  font-weight: 700;
  margin-top: 16px;
  text-align: center;
}

.regime-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 8px;
  line-height: 1.5;
  padding: 0 10px;
}

/* Arrow animation for Trend Runner */
@keyframes trendPulse {
  0%, 100% { opacity: 0.6; transform: translateX(0); }
  50% { opacity: 1; transform: translateX(4px); }
}

.trend-arrows {
  font-size: 24px;
  animation: trendPulse 2s ease-in-out infinite;
}

/* Spring animation for Trap & Revert */
@keyframes springCompress {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.8); }
}

.trap-icon {
  font-size: 24px;
  animation: springCompress 2s ease-in-out infinite;
}
```

### Streamlit Implementation:

```python
# Regime Toggle with st.segmented_control (Streamlit 1.28+) or custom HTML
current_regime = "blue"  # or "red"

st.markdown(f"""
    <div class="regime-toggle-container {current_regime}-active">
        <div class="toggle-track">
            <div class="toggle-knob {current_regime}">
                {"BLUE REGIME" if current_regime == "blue" else "RED REGIME"}
            </div>
        </div>
        <div class="regime-title" style="color: {'var(--blue-primary)' if current_regime == 'blue' else 'var(--red-primary)'}">
            {"↗ TREND RUNNER ↗" if current_regime == "blue" else "↯ TRAP & REVERT ↯"}
        </div>
        <div class="regime-subtitle">
            {"Tuesday detected — Mid-week expansion expected. FVG retests align with VWAP. Pyramiding enabled on second FVG." 
             if current_regime == "blue" 
             else "Friday detected — End-of-week chop expected. Failed breakouts above London High/Low. Tighter targets at VWAP."}
        </div>
    </div>
""", unsafe_allow_html=True)
```

---

## 5.3 Confidence Gauge

**Dimensions:** 100% width, 160px height
**Container:** `.glass-panel-elevated`

### Visual Design:

A **semi-circular gauge** (180-degree arc) with color zones:

```
        ╭────────────────────────╮
       /    RED    YELLOW   GREEN \
      /      40%     70%     100%  \
     |         ╭──╮                  |
     |        /    \    ◄── Needle   |
     |       │  85% │                |
     |        \    /                 |
     |         ╰──╯                  |
     |      S-Tier Signal            |
     |   FVG ✓  VWAP ✓  Level ✓      |
     |      8/11 Winning Sessions      |
      \                              /
       \                            /
        ╰────────────────────────╯
```

### CSS for Gauge:

```css
.gauge-container {
  position: relative;
  width: 200px;
  height: 120px;
  margin: 0 auto;
}

.gauge-arc {
  width: 200px;
  height: 100px;
  border-radius: 100px 100px 0 0;
  background: conic-gradient(
    from 180deg at 50% 100%,
    var(--red-primary) 0deg 72deg,      /* 0-40% = red zone */
    var(--warning) 72deg 126deg,         /* 40-70% = yellow zone */
    var(--profit) 126deg 180deg          /* 70-100% = green zone */
  );
  position: relative;
  mask-image: radial-gradient(
    ellipse 80% 100% at 50% 100%,
    transparent 60%,
    black 61%
  );
  -webkit-mask-image: radial-gradient(
    ellipse 80% 100% at 50% 100%,
    transparent 60%,
    black 61%
  );
}

.gauge-needle {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 2px;
  height: 90px;
  background: var(--text-primary);
  transform-origin: bottom center;
  transform: translateX(-50%) rotate(-45deg); /* 85% = ~-10deg from center */
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.gauge-needle::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: -5px;
  width: 12px;
  height: 12px;
  background: var(--text-primary);
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.gauge-value {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px;
  font-weight: 700;
  color: var(--profit);
}

.confluence-factors {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 12px;
}

.factor-badge {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(0, 255, 136, 0.1);
  color: var(--profit);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.factor-badge.missing {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.historical-accuracy {
  text-align: center;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}

.historical-accuracy .highlight {
  color: var(--profit);
  font-weight: 700;
}
```

### Streamlit Implementation:

```python
# Confidence Gauge with HTML/CSS
confidence = 85  # 0-100

# Calculate needle rotation: -90deg (0%) to +90deg (100%)
needle_rotation = -90 + (confidence / 100) * 180

st.markdown(f"""
    <div class="gauge-container">
        <div class="gauge-arc"></div>
        <div class="gauge-needle" style="transform: translateX(-50%) rotate({needle_rotation}deg)"></div>
        <div class="gauge-value">{confidence}%</div>
    </div>
    <div style="text-align: center; margin-top: 8px;">
        <span style="color: var(--profit); font-weight: 700;">S-Tier Signal</span>
    </div>
    <div class="confluence-factors">
        <span class="factor-badge">FVG ✓</span>
        <span class="factor-badge">VWAP ✓</span>
        <span class="factor-badge">Level ✓</span>
    </div>
    <div class="historical-accuracy">
        <span class="highlight">8/11</span> Winning Sessions (73% accuracy)
    </div>
""", unsafe_allow_html=True)
```

---

## 5.4 Live Journal (AI-Powered)

**Dimensions:** 100% width of right column, ~500px height, scrollable
**Container:** `.glass-panel` with `overflow-y: auto; max-height: 500px;`

### Visual Design:

Scrollable panel with trade entries as **timeline cards**:

```
+==================================+
| LIVE JOURNAL            [12]     |
|                                  |
| ╭────────────────────────────╮   |
| │ 14:35:12  ● LONG 2 MNQ    │   |
| │ Entry: 26,382.50           │   |
| │ Target: 26,390.00 | Stop:  │   |
| │ 26,378.50                  │   |
| │ Regime: BLUE (Trend Runner)│   |
| │ P&L: +$210.00              │   |
| │ [WIN] ✓                    │   |
| │ ─────────────────────────  │   |
| │ AI: Trade successful        │   |
| │ because: Price reclaimed   │   |
| │ London Low (major          │   |
| │ structural shift), created  │   |
| │ Bullish FVG, retest        │   |
| │ occurred at VWAP           │   |
| │ confluence — matching       │   |
| │ Pattern #7 from training   │   |
| │ set.                       │   |
| ╰────────────────────────────╯   |
|                                  |
| ╭────────────────────────────╮   |
| │ 10:22:45  ● SHORT 1 MES    │   |
| │ ...                        │   |
| │ [LOSS] ✗                   │   |
| ╰────────────────────────────╯   |
+==================================+
```

### CSS for Journal:

```css
.journal-container {
  max-height: 500px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.journal-container::-webkit-scrollbar {
  width: 4px;
}

.journal-container::-webkit-scrollbar-track {
  background: transparent;
}

.journal-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.15);
  border-radius: 2px;
}

.trade-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}

.trade-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
}

.trade-card.win {
  border-left: 3px solid var(--profit);
}

.trade-card.loss {
  border-left: 3px solid var(--loss);
}

.trade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.trade-timestamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.trade-direction {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 4px;
  letter-spacing: 0.05em;
}

.trade-direction.long {
  background: rgba(0, 255, 136, 0.15);
  color: var(--profit);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.trade-direction.short {
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
  border: 1px solid rgba(255, 51, 102, 0.3);
}

.trade-details {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.trade-pnl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  margin-top: 6px;
}

.trade-pnl.win { color: var(--profit); }
.trade-pnl.loss { color: var(--loss); }

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.badge.win {
  background: rgba(0, 255, 136, 0.15);
  color: var(--profit);
}

.badge.loss {
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
}

.ai-analysis {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.ai-analysis .ai-label {
  color: var(--blue-primary);
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### Streamlit Implementation:

```python
# Live Journal Panel
trades = [
    {
        "timestamp": "14:35:12",
        "direction": "LONG",
        "contracts": 2,
        "instrument": "MNQ",
        "entry": 26382.50,
        "target": 26390.00,
        "stop": 26378.50,
        "regime": "BLUE",
        "pnl": 210.00,
        "result": "win",
        "ai_analysis": "Price reclaimed London Low (major structural shift), created Bullish FVG, retest occurred at VWAP confluence — matching Pattern #7 from training set."
    },
    {
        "timestamp": "10:22:45",
        "direction": "SHORT",
        "contracts": 1,
        "instrument": "MES",
        "entry": 5842.00,
        "target": 5836.00,
        "stop": 5846.00,
        "regime": "RED",
        "pnl": -150.00,
        "result": "loss",
        "ai_analysis": "Failed breakout above London Low. Price reclaimed but FVG was immediately rejected. Stop hit within 3 minutes — chop regime behavior confirmed."
    }
]

st.markdown('<div class="journal-container">', unsafe_allow_html=True)

for trade in trades:
    pnl_color = "var(--profit)" if trade["result"] == "win" else "var(--loss)"
    pnl_sign = "+" if trade["pnl"] > 0 else ""
    
    st.markdown(f"""
        <div class="trade-card {trade['result']}">
            <div class="trade-header">
                <span class="trade-timestamp">{trade['timestamp']}</span>
                <span class="trade-direction {trade['direction'].lower()}">
                    ● {trade['direction']} {trade['contracts']} {trade['instrument']}
                </span>
            </div>
            <div class="trade-details">
                Entry: {trade['entry']:.2f}<br>
                Target: {trade['target']:.2f} | Stop: {trade['stop']:.2f}<br>
                Regime: <span style="color: {'var(--blue-primary)' if trade['regime'] == 'BLUE' else 'var(--red-primary)'}">
                    {trade['regime']}
                </span>
            </div>
            <div class="trade-pnl {trade['result']}">
                {pnl_sign}${trade['pnl']:.2f}
                <span class="badge {trade['result']}">
                    {'✓ WIN' if trade['result'] == 'win' else '✗ LOSS'}
                </span>
            </div>
            <div class="ai-analysis">
                <span class="ai-label">AI Analysis</span><br>
                {trade['ai_analysis']}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
```

---

## 5.5 Main Chart Area

**Dimensions:** 100% width of left column, ~500px height
**Container:** `.glass-panel` with inner padding

### Visual Design:

The chart area is a **placeholder container** for an embedded TradingView chart or lightweight charts implementation. Overlaid with HTML/CSS annotations:

```
+==========================================+
|  MNQ 1-Minute     [O] 26,382.50         |
|  H: 26,390.00  L: 26,375.00  C: +2.25   |
|                                          |
|  ━━━━━━━━━━━━━ 26,388.50 London High    |
|         ╱╲                                 |
|        ╱  ╲    [▓▓▓] Bullish FVG         |
|  ────╱────╲── 26,382.50 VWAP            |
|      ╱      ╲  · · · · 9-EMA            |
|     ╱   ▲    ╲  ← Entry                 |
|    ╱          ╲                          |
|  ━━━━━━━━━━━━━ 26,375.00 London Low     |
|                                          |
|  [TradingView Lightweight Chart Embed]   |
+==========================================+
```

### CSS for Chart Area:

```css
.chart-container {
  position: relative;
  height: 500px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-secondary);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.chart-instrument {
  font-family: 'Inter', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-price-ticker {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  color: var(--profit);
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-change {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 255, 136, 0.15);
}

.chart-ohlc {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 16px;
}

.chart-annotation {
  position: absolute;
  left: 0;
  right: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  padding: 2px 8px;
  pointer-events: none;
}

.level-line-london-high {
  border-top: 2px dashed rgba(255, 153, 0, 0.6);
  color: rgba(255, 153, 0, 0.8);
}

.level-line-london-low {
  border-top: 2px dashed rgba(0, 255, 136, 0.6);
  color: rgba(0, 255, 136, 0.8);
}

.level-line-vwap {
  border-top: 1px solid rgba(255, 204, 0, 0.8);
  color: rgba(255, 204, 0, 0.9);
}

.ema-line {
  border-top: 1px dotted rgba(255, 255, 255, 0.5);
}

.fvg-box-bullish {
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  border-radius: 2px;
}

.fvg-box-bearish {
  background: rgba(255, 51, 102, 0.15);
  border: 1px solid rgba(255, 51, 102, 0.4);
  border-radius: 2px;
}

.entry-marker {
  position: absolute;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 12px solid var(--profit);
  filter: drop-shadow(0 0 6px var(--profit));
}
```

### Streamlit Implementation:

```python
# Main Chart Area
st.markdown("""
    <div class="chart-container">
        <div class="chart-header">
            <div>
                <span class="chart-instrument">MNQ 1-Minute</span>
                <div class="chart-ohlc">
                    <span>O: 26,381.00</span>
                    <span>H: 26,390.00</span>
                    <span>L: 26,375.00</span>
                    <span>C: 26,384.75</span>
                </div>
            </div>
            <div class="chart-price-ticker">
                26,384.75
                <span class="price-change">+2.25</span>
            </div>
        </div>
        <div style="position: relative; height: calc(100% - 60px);">
            <!-- TradingView chart would be embedded here -->
            <div style="width: 100%; height: 100%; background: var(--bg-secondary); 
                        display: flex; align-items: center; justify-content: center;
                        color: var(--text-muted); font-size: 12px;">
                [TradingView Chart Embed]
            </div>
            
            <!-- Overlaid annotations -->
            <div class="chart-annotation level-line-london-high" style="top: 15%;">
                ━━━━━━━━━━━━━ 26,388.50 LONDON HIGH
            </div>
            <div class="chart-annotation level-line-vwap" style="top: 45%;">
                ───────────── 26,382.50 VWAP
            </div>
            <div class="chart-annotation ema-line" style="top: 55%;">
                · · · · · · · 26,380.25 9-EMA
            </div>
            <div class="chart-annotation level-line-london-low" style="top: 85%;">
                ━━━━━━━━━━━━━ 26,375.00 LONDON LOW
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)
```

---

## 5.6 Trade Control Panel

**Dimensions:** Full width, ~140px height
**Container:** `.glass-panel-elevated`

### Visual Design:

```
+=======================================================================+
|                                                                       |
|  [████████████████ ARM SYSTEM ████████████████]                       |
|                                                                       |
|  ┌─────────────────────────────────────────────┐  [CLOSE POSITION]  |
|  │ POSITION: 2 MNQ LONG  |  UNREALIZED: +$210   │     [RED BUTTON]    |
|  │ Entry: 26,382.50 | Stop: 26,378.50            │                     |
|  └─────────────────────────────────────────────┘                     |
|                                                                       |
|  Auto-Trade: [● ON ───────○ OFF]    Confidence > [━━━●━━] 70%        |
|                                                                       |
|  ━━━━━━━━━━━━━━━━━ RISK GUARD ━━━━━━━━━━━━━━━━━                       |
|  Daily Stop: $300/300    Max Trades: 2/2    Drawdown: $200/2000       |
|                                                                       |
+=======================================================================+
```

### CSS for Trade Control:

```css
.arm-button {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.arm-button.inactive {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.arm-button.active {
  background: rgba(0, 255, 136, 0.1);
  color: var(--profit);
  border: 1px solid rgba(0, 255, 136, 0.4);
  box-shadow: 
    0 0 30px rgba(0, 255, 136, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  animation: armGlow 2s ease-in-out infinite;
}

@keyframes armGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.15); }
  50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.3); }
}

.arm-button::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent 40%,
    rgba(255, 255, 255, 0.05) 50%,
    transparent 60%
  );
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.close-button {
  padding: 14px 28px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border-radius: 8px;
  border: 1px solid rgba(255, 51, 102, 0.5);
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 15px rgba(255, 51, 102, 0.1);
}

.close-button:hover {
  background: rgba(255, 51, 102, 0.25);
  box-shadow: 0 0 25px rgba(255, 51, 102, 0.3);
  transform: translateY(-1px);
}

.position-display {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.position-display .position-label {
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.position-display .position-value {
  color: var(--text-primary);
  font-weight: 600;
}

.position-display .pnl-positive {
  color: var(--profit);
}

.position-display .pnl-negative {
  color: var(--loss);
}

.risk-guard-bar {
  display: flex;
  gap: 24px;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.risk-item {
  font-size: 11px;
  color: var(--text-secondary);
}

.risk-item .risk-value {
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-primary);
}

.risk-item .risk-limit {
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-muted);
}

.risk-item.at-limit .risk-value {
  color: var(--warning);
}

/* Slider styling */
input[type="range"] {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  outline: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--blue-primary);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  cursor: pointer;
}
```

### Streamlit Implementation:

```python
# Trade Control Panel
st.markdown("""
    <div class="glass-panel-elevated">
        <div style="display: flex; gap: 16px; align-items: stretch;">
            <!-- ARM Button -->
            <button class="arm-button active" style="flex: 2;">
                ◉ SYSTEM ARMED
            </button>
            
            <!-- Position Display + Close -->
            <div style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
                <div class="position-display">
                    <div class="position-label">Position</div>
                    <div>
                        <span class="position-value">2 MNQ LONG</span>
                        <span class="pnl-positive">| +$210.00</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                        Entry: 26,382.50 | Stop: 26,378.50
                    </div>
                </div>
                <button class="close-button" style="width: 100%;">
                    ⚠ CLOSE POSITION
                </button>
            </div>
        </div>
        
        <!-- Auto-trade controls -->
        <div style="display: flex; gap: 24px; margin-top: 16px; align-items: center;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 12px; color: var(--text-secondary);">Auto-Trade</span>
                <label class="toggle-switch">
                    <input type="checkbox" checked>
                    <span class="toggle-slider"></span>
                </label>
                <span style="font-size: 12px; color: var(--profit); font-weight: 600;">ON</span>
            </div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-size: 11px; color: var(--text-muted);">Confidence Threshold</span>
                    <span style="font-size: 11px; color: var(--blue-primary); font-family: 'JetBrains Mono', monospace;">70%</span>
                </div>
                <input type="range" min="50" max="95" value="70" style="width: 100%;">
            </div>
        </div>
        
        <!-- Risk Guard -->
        <div class="risk-guard-bar">
            <div class="risk-item">
                <span>Daily Stop: </span>
                <span class="risk-value">$0</span>
                <span class="risk-limit"> / $300</span>
            </div>
            <div class="risk-item">
                <span>Trades: </span>
                <span class="risk-value">2</span>
                <span class="risk-limit"> / 2</span>
            </div>
            <div class="risk-item">
                <span>Drawdown: </span>
                <span class="risk-value">$200</span>
                <span class="risk-limit"> / $2000</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)
```

---

## 5.7 Footer / System Log

**Dimensions:** Full width, ~120px height, scrollable
**Container:** `.glass-panel` with darkened background

### Visual Design:

```
+=======================================================================+
| SYSTEM LOG                                                            |
|                                                                       |
|  14:35:45 — Stop placed @ 26,378.50 | Target 1: VWAP | Target 2: 1.5R |
|  14:35:12 — ENTRY TRIGGERED: LONG 2 MNQ @ 26,382.50                |
|  14:32:05 — FVG detected at 26,380. Waiting for retest...            |
|  14:30:22 — London Low reclaimed @ 26,378. Structure shift confirmed. |
|  14:28:15 — VWAP convergence detected. Bullish FVG forming.           |
|                                                                       |
+=======================================================================+
```

### CSS for System Log:

```css
.system-log {
  max-height: 120px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.8;
  padding: 12px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.system-log::-webkit-scrollbar {
  width: 4px;
}

.system-log::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.15);
  border-radius: 2px;
}

.log-entry {
  padding: 2px 0;
  border-left: 2px solid transparent;
  padding-left: 10px;
  margin-left: 2px;
}

.log-entry.info {
  border-left-color: var(--blue-primary);
  color: rgba(255, 255, 255, 0.7);
}

.log-entry.warning {
  border-left-color: var(--warning);
  color: var(--warning);
}

.log-entry.alert {
  border-left-color: var(--loss);
  color: var(--loss);
  font-weight: 600;
  animation: alertPulse 1s ease-in-out;
}

@keyframes alertPulse {
  0% { background: rgba(255, 51, 102, 0); }
  50% { background: rgba(255, 51, 102, 0.1); }
  100% { background: rgba(255, 51, 102, 0); }
}

.log-timestamp {
  color: var(--text-muted);
  margin-right: 8px;
}

.log-level-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  margin-right: 8px;
  letter-spacing: 0.05em;
}

.log-level-badge.info {
  background: rgba(0, 212, 255, 0.15);
  color: var(--blue-primary);
}

.log-level-badge.warning {
  background: rgba(255, 204, 0, 0.15);
  color: var(--warning);
}

.log-level-badge.alert {
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
}
```

### Streamlit Implementation:

```python
# System Log
log_entries = [
    {"time": "14:35:45", "level": "info", "message": "Stop placed @ 26,378.50 | Target 1: VWAP | Target 2: 1.5R"},
    {"time": "14:35:12", "level": "alert", "message": "ENTRY TRIGGERED: LONG 2 MNQ @ 26,382.50"},
    {"time": "14:32:05", "level": "info", "message": "FVG detected at 26,380. Waiting for retest..."},
    {"time": "14:30:22", "level": "warning", "message": "London Low reclaimed @ 26,378. Structure shift confirmed."},
    {"time": "14:28:15", "level": "info", "message": "VWAP convergence detected. Bullish FVG forming."},
    {"time": "14:25:00", "level": "info", "message": "Session opened. BLUE regime active. Waiting for first signal."},
]

st.markdown('<div class="system-log">', unsafe_allow_html=True)

for entry in log_entries:
    st.markdown(f"""
        <div class="log-entry {entry['level']}">
            <span class="log-timestamp">{entry['time']}</span>
            <span class="log-level-badge {entry['level']}">{entry['level']}</span>
            {entry['message']}
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
```

---

# 6. Complete Streamlit CSS Code

This is the **complete, copy-paste ready CSS** that must be injected at the top of your Streamlit app:

```python
import streamlit as st

# ── PAGE CONFIG ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AuraTrade — AI Trading Assistant",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── IMPORTS ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ── CSS VARIABLES ───────────────────────────────────────────────────── */
:root {
  --bg-primary: #0a0e1a;
  --bg-secondary: #111827;
  --bg-tertiary: #1a2332;
  --bg-glass: rgba(255,255,255,0.03);
  --blue-primary: #00d4ff;
  --blue-glow: rgba(0, 212, 255, 0.4);
  --blue-dim: rgba(0, 212, 255, 0.15);
  --blue-dark: #007a99;
  --red-primary: #ff3366;
  --red-glow: rgba(255, 51, 102, 0.4);
  --red-dim: rgba(255, 51, 102, 0.15);
  --red-dark: #cc0033;
  --profit: #00ff88;
  --profit-dim: rgba(0, 255, 136, 0.15);
  --loss: #ff3366;
  --warning: #ffcc00;
  --warning-dim: rgba(255, 204, 0, 0.15);
  --info: #00d4ff;
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --text-muted: rgba(255, 255, 255, 0.35);
  --text-inverse: #0a0e1a;
  --border-glass: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.15);
  --shadow-float: 0 8px 32px rgba(0, 0, 0, 0.4);
  --shadow-glow-blue: 0 0 20px rgba(0, 212, 255, 0.3);
  --shadow-glow-red: 0 0 20px rgba(255, 51, 102, 0.3);
  --shadow-inset: inset 0 1px 0 rgba(255,255,255,0.05);
}

/* ── STREAMLIT BASE OVERRIDES ────────────────────────────────────────── */
.stApp {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit UI chrome */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Remove default padding */
.block-container {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  max-width: 100% !important;
}

/* ── GLASSMORPHISM PANELS ────────────────────────────────────────────── */
.glass-panel {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-glass);
  border-radius: 12px;
  box-shadow: var(--shadow-float), var(--shadow-inset);
  padding: 16px;
  position: relative;
  overflow: hidden;
  margin-bottom: 16px;
}

.glass-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 16px;
  right: 16px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15) 20%, rgba(255,255,255,0.15) 80%, transparent);
}

.glass-panel-elevated {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  padding: 20px;
  position: relative;
  overflow: hidden;
  margin-bottom: 16px;
}

.glass-panel-blue {
  background: rgba(0, 212, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 212, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  padding: 16px;
  margin-bottom: 16px;
}

.glass-panel-red {
  background: rgba(255, 51, 102, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 51, 102, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(255, 51, 102, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  padding: 16px;
  margin-bottom: 16px;
}

/* ── HEADER ──────────────────────────────────────────────────────────── */
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo-text {
  font-family: 'Inter', sans-serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-primary);
}

.logo-diamond {
  color: var(--blue-primary);
  text-shadow: 0 0 10px var(--blue-glow);
}

.logo-diamond.red {
  color: var(--red-primary);
  text-shadow: 0 0 10px var(--red-glow);
}

.header-metric {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.metric-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.metric-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value.profit { color: var(--profit); }
.metric-value.loss { color: var(--loss); }

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--profit);
  box-shadow: 0 0 8px var(--profit);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px var(--profit); }
  50% { opacity: 0.6; box-shadow: 0 0 4px var(--profit); }
}

.connection-status.offline .status-dot {
  background: var(--loss);
  box-shadow: none;
  animation: none;
}

.connection-status.offline {
  color: var(--loss);
}

.session-timer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: var(--text-secondary);
}

.timer-icon {
  font-size: 12px;
}

/* ── REGIME TOGGLE ───────────────────────────────────────────────────── */
.regime-toggle-container {
  padding: 20px;
  border-radius: 12px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.regime-toggle-container.blue-active {
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.1);
}

.regime-toggle-container.red-active {
  background: rgba(255, 51, 102, 0.05);
  border: 1px solid rgba(255, 51, 102, 0.25);
  box-shadow: 0 0 30px rgba(255, 51, 102, 0.1);
}

.toggle-track {
  width: 100%;
  height: 44px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 22px;
  position: relative;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.toggle-knob {
  position: absolute;
  width: calc(50% - 4px);
  height: 40px;
  top: 2px;
  border-radius: 20px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.toggle-knob.blue {
  left: 2px;
  background: rgba(0, 212, 255, 0.2);
  color: var(--blue-primary);
  border: 1px solid rgba(0, 212, 255, 0.4);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}

.toggle-knob.red {
  right: 2px;
  background: rgba(255, 51, 102, 0.2);
  color: var(--red-primary);
  border: 1px solid rgba(255, 51, 102, 0.4);
  box-shadow: 0 0 15px rgba(255, 51, 102, 0.2);
}

.regime-title {
  font-size: 20px;
  font-weight: 700;
  margin-top: 16px;
  text-align: center;
  font-family: 'Inter', sans-serif;
}

.regime-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 8px;
  line-height: 1.5;
  padding: 0 10px;
}

@keyframes trendPulse {
  0%, 100% { opacity: 0.6; transform: translateX(0); }
  50% { opacity: 1; transform: translateX(4px); }
}

.trend-arrows {
  font-size: 24px;
  animation: trendPulse 2s ease-in-out infinite;
  display: inline-block;
}

@keyframes springCompress {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.8); }
}

.trap-icon {
  font-size: 24px;
  animation: springCompress 2s ease-in-out infinite;
  display: inline-block;
}

/* ── CONFIDENCE GAUGE ────────────────────────────────────────────────── */
.gauge-container {
  position: relative;
  width: 200px;
  height: 120px;
  margin: 0 auto;
}

.gauge-arc {
  width: 200px;
  height: 100px;
  border-radius: 100px 100px 0 0;
  background: conic-gradient(from 180deg at 50% 100%, var(--red-primary) 0deg 72deg, var(--warning) 72deg 126deg, var(--profit) 126deg 180deg);
  position: relative;
  mask-image: radial-gradient(ellipse 80% 100% at 50% 100%, transparent 60%, black 61%);
  -webkit-mask-image: radial-gradient(ellipse 80% 100% at 50% 100%, transparent 60%, black 61%);
}

.gauge-needle {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 2px;
  height: 90px;
  background: var(--text-primary);
  transform-origin: bottom center;
  transform: translateX(-50%) rotate(0deg);
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.gauge-needle::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: -5px;
  width: 12px;
  height: 12px;
  background: var(--text-primary);
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.gauge-value {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px;
  font-weight: 700;
  color: var(--profit);
}

.confluence-factors {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 12px;
  flex-wrap: wrap;
}

.factor-badge {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(0, 255, 136, 0.1);
  color: var(--profit);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.factor-badge.missing {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.historical-accuracy {
  text-align: center;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}

.historical-accuracy .highlight {
  color: var(--profit);
  font-weight: 700;
}

/* ── LIVE JOURNAL ────────────────────────────────────────────────────── */
.journal-container {
  max-height: 500px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.journal-container::-webkit-scrollbar { width: 4px; }
.journal-container::-webkit-scrollbar-track { background: transparent; }
.journal-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }

.trade-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}

.trade-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
}

.trade-card.win { border-left: 3px solid var(--profit); }
.trade-card.loss { border-left: 3px solid var(--loss); }

.trade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.trade-timestamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.trade-direction {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 4px;
  letter-spacing: 0.05em;
}

.trade-direction.long {
  background: rgba(0, 255, 136, 0.15);
  color: var(--profit);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.trade-direction.short {
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
  border: 1px solid rgba(255, 51, 102, 0.3);
}

.trade-details {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.trade-pnl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  margin-top: 6px;
}

.trade-pnl.win { color: var(--profit); }
.trade-pnl.loss { color: var(--loss); }

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-left: 8px;
}

.badge.win {
  background: rgba(0, 255, 136, 0.15);
  color: var(--profit);
}

.badge.loss {
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
}

.ai-analysis {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.ai-analysis .ai-label {
  color: var(--blue-primary);
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 4px;
}

/* ── CHART AREA ──────────────────────────────────────────────────────── */
.chart-container {
  position: relative;
  height: 500px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-secondary);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.chart-instrument {
  font-family: 'Inter', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-price-ticker {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  color: var(--profit);
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-change {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 255, 136, 0.15);
}

.chart-ohlc {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 16px;
  margin-top: 4px;
}

.chart-annotation {
  position: absolute;
  left: 0;
  right: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  padding: 2px 16px;
  pointer-events: none;
  z-index: 10;
}

.level-line-london-high {
  border-top: 2px dashed rgba(255, 153, 0, 0.6);
  color: rgba(255, 153, 0, 0.8);
}

.level-line-london-low {
  border-top: 2px dashed rgba(0, 255, 136, 0.6);
  color: rgba(0, 255, 136, 0.8);
}

.level-line-vwap {
  border-top: 1px solid rgba(255, 204, 0, 0.8);
  color: rgba(255, 204, 0, 0.9);
}

.ema-line {
  border-top: 1px dotted rgba(255, 255, 255, 0.5);
  color: rgba(255, 255, 255, 0.5);
}

.fvg-box-bullish {
  position: absolute;
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  border-radius: 2px;
  z-index: 5;
}

.fvg-box-bearish {
  position: absolute;
  background: rgba(255, 51, 102, 0.15);
  border: 1px solid rgba(255, 51, 102, 0.4);
  border-radius: 2px;
  z-index: 5;
}

.entry-marker {
  position: absolute;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 12px solid var(--profit);
  filter: drop-shadow(0 0 6px var(--profit));
  z-index: 10;
}

/* ── TRADE CONTROL ───────────────────────────────────────────────────── */
.arm-button {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

.arm-button.inactive {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.arm-button.active {
  background: rgba(0, 255, 136, 0.1);
  color: var(--profit);
  border: 1px solid rgba(0, 255, 136, 0.4);
  box-shadow: 0 0 30px rgba(0, 255, 136, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  animation: armGlow 2s ease-in-out infinite;
}

@keyframes armGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.15); }
  50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.3); }
}

.close-button {
  padding: 14px 28px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border-radius: 8px;
  border: 1px solid rgba(255, 51, 102, 0.5);
  background: rgba(255, 51, 102, 0.15);
  color: var(--red-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 15px rgba(255, 51, 102, 0.1);
  font-family: 'Inter', sans-serif;
  width: 100%;
}

.close-button:hover {
  background: rgba(255, 51, 102, 0.25);
  box-shadow: 0 0 25px rgba(255, 51, 102, 0.3);
  transform: translateY(-1px);
}

.position-display {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.position-display .position-label {
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 4px;
}

.position-display .position-value {
  color: var(--text-primary);
  font-weight: 600;
}

.position-display .pnl-positive { color: var(--profit); }
.position-display .pnl-negative { color: var(--loss); }

.risk-guard-bar {
  display: flex;
  gap: 24px;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
}

.risk-item {
  font-size: 11px;
  color: var(--text-secondary);
}

.risk-item .risk-value {
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-primary);
  font-weight: 600;
}

.risk-item .risk-limit {
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-muted);
}

.risk-item.at-limit .risk-value { color: var(--warning); }

/* ── SYSTEM LOG ──────────────────────────────────────────────────────── */
.system-log-container {
  max-height: 120px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.8;
  padding: 12px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.system-log-container::-webkit-scrollbar { width: 4px; }
.system-log-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }

.log-entry {
  padding: 2px 0;
  border-left: 2px solid transparent;
  padding-left: 10px;
  margin-left: 2px;
}

.log-entry.info { border-left-color: var(--blue-primary); color: rgba(255, 255, 255, 0.7); }
.log-entry.warning { border-left-color: var(--warning); color: var(--warning); }
.log-entry.alert { border-left-color: var(--loss); color: var(--loss); font-weight: 600; }

.log-timestamp {
  color: var(--text-muted);
  margin-right: 8px;
  font-size: 10px;
}

.log-level-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  margin-right: 8px;
  letter-spacing: 0.05em;
}

.log-level-badge.info { background: rgba(0, 212, 255, 0.15); color: var(--blue-primary); }
.log-level-badge.warning { background: rgba(255, 204, 0, 0.15); color: var(--warning); }
.log-level-badge.alert { background: rgba(255, 51, 102, 0.15); color: var(--red-primary); }

/* ── TOGGLE SWITCH ───────────────────────────────────────────────────── */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.1);
  transition: .3s;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: .3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

input:checked + .toggle-slider {
  background-color: rgba(0, 255, 136, 0.2);
  border-color: rgba(0, 255, 136, 0.4);
}

input:checked + .toggle-slider:before {
  transform: translateX(20px);
  background-color: var(--profit);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

/* ── RANGE SLIDER ────────────────────────────────────────────────────── */
input[type="range"] {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  outline: none;
  margin-top: 6px;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--blue-primary);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  cursor: pointer;
  border: 2px solid var(--bg-primary);
}

input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--blue-primary);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  cursor: pointer;
  border: 2px solid var(--bg-primary);
}

/* ── SCROLLBAR (Global) ──────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }

/* ── RESPONSIVE ──────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .header-bar { flex-wrap: wrap; gap: 12px; }
  .risk-guard-bar { flex-direction: column; gap: 8px; }
  .gauge-container { width: 160px; height: 100px; }
  .gauge-arc { width: 160px; height: 80px; border-radius: 80px 80px 0 0; }
  .gauge-needle { height: 75px; }
  .gauge-value { font-size: 22px; }
}

@media (max-width: 768px) {
  .regime-toggle-container { padding: 14px; }
  .regime-title { font-size: 16px; }
  .chart-container { height: 350px; }
  .journal-container { max-height: 300px; }
}
</style>
""", unsafe_allow_html=True)
```

---

# 7. Streamlit Layout Code

This is the **complete layout structure** for the Streamlit app:

```python
import streamlit as st
import datetime

# ── SESSION STATE ───────────────────────────────────────────────────────
if 'regime' not in st.session_state:
    st.session_state.regime = 'blue'
if 'armed' not in st.session_state:
    st.session_state.armed = True
if 'auto_trade' not in st.session_state:
    st.session_state.auto_trade = True
if 'confidence_threshold' not in st.session_state:
    st.session_state.confidence_threshold = 70

# ── INJECT CSS (from Section 6) ────────────────────────────────────────
# [PASTE THE CSS st.markdown() BLOCK HERE]

# ═══════════════════════════════════════════════════════════════════════
# HEADER BAR
# ═══════════════════════════════════════════════════════════════════════
st.markdown("""
    <div class="header-bar">
        <div style="display: flex; align-items: center; gap: 24px;">
            <div class="logo-container">
                <span class="logo-text">AURA<span class="logo-diamond">◆</span>TRADE</span>
            </div>
            <div style="width: 1px; height: 32px; background: rgba(255,255,255,0.08);"></div>
            <div class="header-metric">
                <span class="metric-label">Balance</span>
                <span class="metric-value">$50,000.00</span>
            </div>
            <div class="header-metric">
                <span class="metric-label">Daily P&L</span>
                <span class="metric-value profit">+$425.50 ▲</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 24px;">
            <div class="connection-status live">
                <span class="status-dot"></span> LIVE
            </div>
            <div class="session-timer">
                <span class="timer-icon">⏱</span>
                <span class="timer-value">04:32:15</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# ROW 1: REGIME TOGGLE + CONFIDENCE GAUGE
# ═══════════════════════════════════════════════════════════════════════
row1_col1, row1_col2 = st.columns([4, 8])

with row1_col1:
    current_regime = st.session_state.regime
    regime_title = "TREND RUNNER" if current_regime == "blue" else "TRAP & REVERT"
    regime_icon = "↗" if current_regime == "blue" else "↯"
    regime_color = "var(--blue-primary)" if current_regime == "blue" else "var(--red-primary)"
    regime_desc = (
        "Tuesday detected — Mid-week expansion expected. FVG retests align with VWAP. Pyramiding enabled on second FVG."
        if current_regime == "blue"
        else "Friday detected — End-of-week chop expected. Failed breakouts above London High/Low. Tighter targets at VWAP."
    )
    
    st.markdown(f"""
        <div class="regime-toggle-container {current_regime}-active">
            <div class="toggle-track">
                <div class="toggle-knob {current_regime}">
                    {current_regime.upper()} REGIME
                </div>
            </div>
            <div class="regime-title" style="color: {regime_color}">
                {regime_icon} {regime_title} {regime_icon}
            </div>
            <div class="regime-subtitle">
                {regime_desc}
            </div>
        </div>
    """, unsafe_allow_html=True)

with row1_col2:
    confidence = 85
    needle_rotation = -90 + (confidence / 100) * 180
    
    st.markdown(f"""
        <div class="glass-panel-elevated" style="display: flex; align-items: center; gap: 24px;">
            <div style="flex: 1;">
                <div class="gauge-container">
                    <div class="gauge-arc"></div>
                    <div class="gauge-needle" style="transform: translateX(-50%) rotate({needle_rotation}deg)"></div>
                    <div class="gauge-value">{confidence}%</div>
                </div>
            </div>
            <div style="flex: 1;">
                <div style="text-align: center; margin-bottom: 8px;">
                    <span style="color: var(--profit); font-weight: 700; font-size: 14px;">S-Tier Signal</span>
                </div>
                <div class="confluence-factors">
                    <span class="factor-badge">FVG ✓</span>
                    <span class="factor-badge">VWAP ✓</span>
                    <span class="factor-badge">Level ✓</span>
                </div>
                <div class="historical-accuracy">
                    <span class="highlight">8/11</span> Winning Sessions (73% accuracy)
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# ROW 2: MAIN CHART + LIVE JOURNAL
# ═══════════════════════════════════════════════════════════════════════
row2_col1, row2_col2 = st.columns([8, 4])

with row2_col1:
    st.markdown("""
        <div class="glass-panel" style="padding: 0; overflow: hidden;">
            <div class="chart-container" style="height: 500px; border-radius: 10px;">
                <div class="chart-header">
                    <div>
                        <span class="chart-instrument">MNQ 1-Minute</span>
                        <div class="chart-ohlc">
                            <span>O: 26,381.00</span>
                            <span>H: 26,390.00</span>
                            <span>L: 26,375.00</span>
                            <span>C: 26,384.75</span>
                        </div>
                    </div>
                    <div class="chart-price-ticker">
                        26,384.75
                        <span class="price-change">+2.25</span>
                    </div>
                </div>
                <div style="position: relative; height: calc(100% - 60px);">
                    <div style="width: 100%; height: 100%; background: var(--bg-secondary); 
                                display: flex; align-items: center; justify-content: center;
                                color: var(--text-muted); font-size: 12px;">
                        [TradingView Lightweight Charts Embed]
                    </div>
                    <div class="chart-annotation level-line-london-high" style="top: 15%;">
                        ━━━━━━━━━━━━━ 26,388.50 LONDON HIGH
                    </div>
                    <div class="chart-annotation level-line-vwap" style="top: 45%;">
                        ───────────── 26,382.50 VWAP
                    </div>
                    <div class="chart-annotation ema-line" style="top: 55%;">
                        · · · · · · · 26,380.25 9-EMA
                    </div>
                    <div class="chart-annotation level-line-london-low" style="top: 85%;">
                        ━━━━━━━━━━━━━ 26,375.00 LONDON LOW
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with row2_col2:
    st.markdown("""
        <div class="glass-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 14px; font-weight: 600;">Live Journal</span>
                <span style="font-size: 11px; color: var(--text-muted); background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px;">12 entries</span>
            </div>
            <div class="journal-container">
    """, unsafe_allow_html=True)
    
    trades = [
        {"timestamp": "14:35:12", "direction": "LONG", "contracts": 2, "instrument": "MNQ", 
         "entry": 26382.50, "target": 26390.00, "stop": 26378.50, "regime": "BLUE", 
         "pnl": 210.00, "result": "win",
         "ai_analysis": "Price reclaimed London Low (major structural shift), created Bullish FVG, retest occurred at VWAP confluence — matching Pattern #7 from training set."},
        {"timestamp": "10:22:45", "direction": "SHORT", "contracts": 1, "instrument": "MES", 
         "entry": 5842.00, "target": 5836.00, "stop": 5846.00, "regime": "RED", 
         "pnl": -150.00, "result": "loss",
         "ai_analysis": "Failed breakout above London Low. Price reclaimed but FVG was immediately rejected. Stop hit within 3 minutes — chop regime behavior confirmed."},
    ]
    
    for trade in trades:
        pnl_sign = "+" if trade["pnl"] > 0 else ""
        pnl_class = "win" if trade["result"] == "win" else "loss"
        regime_color = "var(--blue-primary)" if trade["regime"] == "BLUE" else "var(--red-primary)"
        
        st.markdown(f"""
            <div class="trade-card {pnl_class}">
                <div class="trade-header">
                    <span class="trade-timestamp">{trade['timestamp']}</span>
                    <span class="trade-direction {trade['direction'].lower()}">
                        ● {trade['direction']} {trade['contracts']} {trade['instrument']}
                    </span>
                </div>
                <div class="trade-details">
                    Entry: {trade['entry']:.2f}<br>
                    Target: {trade['target']:.2f} | Stop: {trade['stop']:.2f}<br>
                    Regime: <span style="color: {regime_color}">{trade['regime']}</span>
                </div>
                <div class="trade-pnl {pnl_class}">
                    {pnl_sign}${trade['pnl']:.2f}
                    <span class="badge {pnl_class}">
                        {'✓ WIN' if trade['result'] == 'win' else '✗ LOSS'}
                    </span>
                </div>
                <div class="ai-analysis">
                    <span class="ai-label">AI Analysis</span>
                    {trade['ai_analysis']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
            </div>
        </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# ROW 3: TRADE CONTROL PANEL
# ═══════════════════════════════════════════════════════════════════════
st.markdown("""
    <div class="glass-panel-elevated">
        <div style="display: flex; gap: 16px; align-items: stretch; flex-wrap: wrap;">
            <!-- ARM Button -->
            <button class="arm-button active" style="flex: 2; min-width: 200px;">
                ◉ SYSTEM ARMED — WAITING FOR SIGNAL
            </button>
            
            <!-- Position + Close -->
            <div style="flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 8px;">
                <div class="position-display">
                    <span class="position-label">Active Position</span>
                    <div>
                        <span class="position-value">2 MNQ LONG</span>
                        <span class="pnl-positive">| +$210.00</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                        Entry: 26,382.50 | Stop: 26,378.50 | Target: VWAP
                    </div>
                </div>
                <button class="close-button">
                    ⚠ CLOSE POSITION
                </button>
            </div>
        </div>
        
        <!-- Auto-trade + Confidence -->
        <div style="display: flex; gap: 24px; margin-top: 16px; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 12px; color: var(--text-secondary);">Auto-Trade</span>
                <label class="toggle-switch">
                    <input type="checkbox" checked>
                    <span class="toggle-slider"></span>
                </label>
                <span style="font-size: 12px; color: var(--profit); font-weight: 600;">ON</span>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-size: 11px; color: var(--text-muted);">Confidence Threshold</span>
                    <span style="font-size: 11px; color: var(--blue-primary); font-family: 'JetBrains Mono', monospace;">70%</span>
                </div>
                <input type="range" min="50" max="95" value="70" style="width: 100%;">
            </div>
        </div>
        
        <!-- Risk Guard -->
        <div class="risk-guard-bar">
            <div class="risk-item">
                <span>Daily Stop: </span>
                <span class="risk-value">$0</span>
                <span class="risk-limit"> / $300</span>
            </div>
            <div class="risk-item">
                <span>Trades: </span>
                <span class="risk-value">2</span>
                <span class="risk-limit"> / 2</span>
            </div>
            <div class="risk-item">
                <span>Drawdown: </span>
                <span class="risk-value">$200</span>
                <span class="risk-limit"> / $2000</span>
            </div>
            <div class="risk-item">
                <span>9-EMA Guard: </span>
                <span style="color: var(--profit); font-weight: 600;">ACTIVE</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# ROW 4: SYSTEM LOG
# ═══════════════════════════════════════════════════════════════════════
st.markdown("""
    <div class="glass-panel" style="padding: 0;">
        <div style="padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.06); display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 14px; font-weight: 600;">System Log</span>
            <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Real-time</span>
        </div>
        <div class="system-log-container">
""", unsafe_allow_html=True)

log_entries = [
    {"time": "14:35:45", "level": "info", "message": "Stop placed @ 26,378.50 | Target 1: VWAP | Target 2: 1.5R"},
    {"time": "14:35:12", "level": "alert", "message": "ENTRY TRIGGERED: LONG 2 MNQ @ 26,382.50"},
    {"time": "14:32:05", "level": "info", "message": "FVG detected at 26,380. Waiting for retest..."},
    {"time": "14:30:22", "level": "warning", "message": "London Low reclaimed @ 26,378. Structure shift confirmed."},
    {"time": "14:28:15", "level": "info", "message": "VWAP convergence detected. Bullish FVG forming."},
    {"time": "14:25:00", "level": "info", "message": "Session opened. BLUE regime active. Waiting for first signal."},
]

for entry in log_entries:
    st.markdown(f"""
        <div class="log-entry {entry['level']}">
            <span class="log-timestamp">{entry['time']}</span>
            <span class="log-level-badge {entry['level']}">{entry['level']}</span>
            {entry['message']}
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
        </div>
    </div>
""", unsafe_allow_html=True)
```

---

# 8. Animation & Interaction Specs

## Animation Definitions

| Animation | Duration | Easing | Trigger |
|-----------|----------|--------|---------|
| Regime toggle slide | 400ms | cubic-bezier(0.4, 0, 0.2, 1) | User clicks regime toggle |
| Gauge needle sweep | 600ms | cubic-bezier(0.4, 0, 0.2, 1) | Confidence value updates |
| Arm button glow | 2000ms | ease-in-out (infinite) | System armed state |
| Arm shimmer | 3000ms | linear (infinite) | System armed state |
| Status dot pulse | 2000ms | ease-in-out (infinite) | Connection live |
| Trend arrows pulse | 2000ms | ease-in-out (infinite) | Blue regime active |
| Trap spring compress | 2000ms | ease-in-out (infinite) | Red regime active |
| Alert entry flash | 1000ms | ease-in-out | New alert-level log entry |
| Hover lift | 200ms | ease | Mouse over any card |
| Button press | 100ms | ease | Mouse down on button |

## Hover States

```css
/* All interactive elements */
.interactive {
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.interactive:active {
  transform: translateY(0);
}
```

## Regime Transition Flow

```
User clicks toggle
  → Knob slides (400ms, cubic-bezier)
  → Panel background transitions (400ms)
  → Border color transitions (400ms)
  → Box-shadow glow changes (400ms)
  → Regime icon/animation swaps (instant)
  → Subtext updates (instant)
  → Chart annotations recolor (if applicable)
  → Risk parameters may adjust (tighter targets in RED)
```

---

# 9. Responsive Behavior

## Breakpoints

| Breakpoint | Layout Changes |
|------------|---------------|
| **1440px+** | Full 12-column grid as specified |
| **1024px** | Regime+Gauge stack vertically (6+6). Chart+Journal stack (12 each). Risk bar wraps |
| **768px** | All panels stack vertically. Header wraps. Chart height reduced to 350px. Journal max-height 300px |
| **480px** | Single column. Minimum padding. Gauge scales to 160px. Font sizes reduce 10% |

## Mobile Adaptations

```css
@media (max-width: 768px) {
  .header-bar { padding: 12px 16px; }
  .logo-text { font-size: 16px; }
  .chart-container { height: 350px; }
  .journal-container { max-height: 300px; }
  .regime-title { font-size: 16px; }
  .toggle-track { height: 36px; }
  .toggle-knob { height: 32px; font-size: 10px; }
  .arm-button { font-size: 14px; padding: 12px; }
  .risk-guard-bar { flex-direction: column; gap: 8px; }
}
```

---

# 10. Asset Checklist

## No External Image Assets Required

All visual elements are **code-generated**:

- [x] Logo: CSS text with diamond character (◆) and text-shadow glow
- [x] Regime icons: CSS arrows (↗/↯) with keyframe animations
- [x] Confidence gauge: CSS conic-gradient + mask-image + rotating needle
- [x] Chart annotations: CSS positioned elements with dashed/dotted borders
- [x] FVG boxes: CSS divs with colored backgrounds and borders
- [x] Entry markers: CSS triangles (border technique)
- [x] All badges, labels, status indicators: Pure CSS

## Optional Enhancements (Future)

- [ ] TradingView chart integration (requires JS library)
- [ ] Real-time WebSocket data feed integration
- [ ] Sound effects for entry/exit/alert events
- [ ] Particle background effect (subtle, behind glass panels)

---

# Appendix A: Color-Blind Accessibility Notes

For color-blind users, the regime system uses **both color AND iconography**:
- Blue regime: Trend arrows (↗) + cyan glow
- Red regime: Trap icon (↯) + crimson glow
- Win/loss: Checkmark (✓) vs X (✗) — not just green/red
- Log levels: Text labels (INFO/WARNING/ALERT) — not just colored borders

# Appendix B: Performance Notes

- `backdrop-filter: blur()` is GPU-accelerated but expensive. Limit to ~10 panels.
- Animations use `transform` and `opacity` only — compositor-friendly.
- No box-shadow animations (expensive). Shadow changes happen on state transition only.
- Use `will-change: transform` on the gauge needle for smooth updates.

---

*End of Specification*
