/*
  HeroArt
  -------
  The hero illustration for the SmartCart home page.

  It replaces `src/assets/home.png`, which carried a visible "Google"
  watermark and started to look blurry the moment the hero was
  resized on a large screen.

  Why an inline SVG instead of an image file:

    * It is vector, so it stays perfectly sharp at any size.
    * It can be animated per-part. The animation is applied through
      CSS classes (see the "HERO ART" block in App.css) rather than
      CSS-in-JS, so the styling stays in one place with the rest of
      the site, and the existing `prefers-reduced-motion` rule in
      App.css automatically switches the whole thing off for anyone
      who has asked for less motion.
    * Every colour is pulled from the site palette, so the drawing
      cannot drift away from the rest of the design.

  The scene: a phone showing the SmartCart storefront, surrounded
  by floating cards that stand in for the recommendation engine.

  Accessibility: the SVG carries role="img" plus a <title> and a
  <desc>, so a screen reader announces what it is instead of
  reading out a pile of path data.
*/

function HeroArt() {
  return (
    <svg
      className="hero-art"
      viewBox="0 0 620 560"
      role="img"
      aria-labelledby="heroArtTitle heroArtDesc"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title id="heroArtTitle">SmartCart shopping illustration</title>

      <desc id="heroArtDesc">
        A phone showing the SmartCart storefront with a confirmed
        order, surrounded by floating cards for a product match
        score, shopping preferences and customer ratings.
      </desc>

      {/* =====================================================
          DEFINITIONS
          Gradients and shadows live here and are referenced by
          id further down. Keeping them together means the whole
          palette can be adjusted in one place.
      ===================================================== */}
      <defs>
        <linearGradient id="haSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#eaf7ff" />
          <stop offset="100%" stopColor="#d9f0ff" />
        </linearGradient>

        <linearGradient id="haScreen" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#f6fbff" />
        </linearGradient>

        {/* The awning: a slightly stronger purple than the flat
            accent, so it does not look washed out over the screen. */}
        <linearGradient id="haAwn" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#8959e6" />
          <stop offset="100%" stopColor="#a97ef0" />
        </linearGradient>

        {/* The shop window. The light band at the top-left is a
            glass reflection, which is what stops the window from
            reading as a flat rectangle. */}
        <linearGradient id="haPane" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d9f0ff" />
          <stop offset="55%" stopColor="#eaf7ff" />
          <stop offset="100%" stopColor="#c9e9fb" />
        </linearGradient>

        <linearGradient id="haOrb" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#c7dfa3" />
          <stop offset="100%" stopColor="#e4f0c8" />
        </linearGradient>

        <linearGradient id="haBag" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a97ef0" />
          <stop offset="100%" stopColor="#7345cf" />
        </linearGradient>

        {/* Three shadow depths. Small elements get `tiny`, the
            phone gets `lift`, and everything in between gets
            `soft`. Reusing three levels keeps the depth looking
            deliberate instead of accidental. */}
        <filter id="haSoft" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow
            dx="0"
            dy="10"
            stdDeviation="12"
            floodColor="#31465a"
            floodOpacity="0.13"
          />
        </filter>

        <filter id="haLift" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow
            dx="0"
            dy="16"
            stdDeviation="18"
            floodColor="#31465a"
            floodOpacity="0.20"
          />
        </filter>

        <filter id="haTiny" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow
            dx="0"
            dy="5"
            stdDeviation="6"
            floodColor="#31465a"
            floodOpacity="0.14"
          />
        </filter>
      </defs>

      {/* =====================================================
          BACKDROP
          A rounded organic blob behind everything. The phone and
          cards overlap its edge slightly, which is what gives the
          scene a sense of depth.
      ===================================================== */}
      <path
        className="ha-blob"
        d="M300 45c95-16 205 22 246 108 41 86 12 197-59 258-71 61-181 72-268 38C132 415 58 337 45 244 32 151 93 71 185 53c38-7 77-5 115-8z"
        fill="url(#haSky)"
      />

      {/* Decorative dots. These are the smallest animated parts,
          drifting furthest, which reads as the closest layer. */}
      <circle className="ha-dot ha-dot-1" cx="86" cy="150" r="7" fill="#8959e6" opacity="0.45" />
      <circle className="ha-dot ha-dot-2" cx="546" cy="186" r="10" fill="#c7dfa3" opacity="0.9" />
      <circle className="ha-dot ha-dot-3" cx="70" cy="404" r="6" fill="#31465a" opacity="0.22" />
      <circle className="ha-dot ha-dot-4" cx="556" cy="432" r="8" fill="#8959e6" opacity="0.35" />

      {/* =====================================================
          THE PHONE
          Drawn in a group that floats as one unit, because a
          phone whose body and screen drift apart looks broken.
      ===================================================== */}
      <g className="ha-phone" filter="url(#haLift)">
        {/* Body */}
        <rect x="204" y="96" width="212" height="392" rx="34" fill="#31465a" />

        {/* Bezel highlight down the left edge - a one-pixel
            light line is what makes plastic look like metal. */}
        <rect
          x="206.5"
          y="98.5"
          width="207"
          height="387"
          rx="32"
          fill="none"
          stroke="#ffffff"
          strokeOpacity="0.16"
          strokeWidth="1.5"
        />

        {/* Screen */}
        <rect x="216" y="110" width="188" height="364" rx="26" fill="url(#haScreen)" />

        {/* Notch */}
        <rect x="286" y="120" width="48" height="7" rx="3.5" fill="#31465a" opacity="0.35" />

        {/* ---- Shop sign ---- */}
        <text
          x="310"
          y="168"
          textAnchor="middle"
          fontFamily="Poppins, sans-serif"
          fontSize="19"
          fontWeight="700"
          fill="#31465a"
          letterSpacing="-0.3"
        >
          Smart
          <tspan fill="#8959e6">Cart</tspan>
        </text>

        <rect x="286" y="178" width="48" height="3" rx="1.5" fill="#c7dfa3" />

        {/* ---- Awning ----
            A scalloped strip. Each scallop is one <path>;
            the flat block behind them hides the tops. */}
        <rect x="236" y="196" width="148" height="14" fill="url(#haAwn)" />

        <path
          d="M236 210a12 12 0 0 0 24 0zM260 210a12 12 0 0 0 24 0zM284 210a12 12 0 0 0 24 0zM308 210a12 12 0 0 0 24 0zM332 210a12 12 0 0 0 24 0zM356 210a12 12 0 0 0 24 0z"
          fill="url(#haAwn)"
        />

        {/* ---- Window ---- */}
        <rect x="240" y="228" width="140" height="106" rx="12" fill="url(#haPane)" />

        {/* Glass reflection: a soft diagonal band across the
            top-left corner. */}
        <path d="M240 240v-12h46l-40 94h-6z" fill="#ffffff" opacity="0.55" />

        {/* Window frame */}
        <rect
          x="240"
          y="228"
          width="140"
          height="106"
          rx="12"
          fill="none"
          stroke="#31465a"
          strokeOpacity="0.14"
          strokeWidth="2"
        />

        {/* Two shelves inside the window */}
        <rect x="258" y="262" width="104" height="5" rx="2.5" fill="#31465a" opacity="0.13" />
        <rect x="258" y="300" width="104" height="5" rx="2.5" fill="#31465a" opacity="0.13" />

        {/* Products on the shelves - simple blocks, deliberately
            abstract so they never look like a botched icon. */}
        <rect x="266" y="240" width="16" height="22" rx="4" fill="#8959e6" opacity="0.75" />
        <rect x="290" y="246" width="14" height="16" rx="4" fill="#c7dfa3" />
        <rect x="312" y="238" width="18" height="24" rx="5" fill="#8959e6" opacity="0.45" />

        <rect x="266" y="280" width="18" height="20" rx="5" fill="#c7dfa3" opacity="0.85" />
        <rect x="292" y="284" width="14" height="16" rx="4" fill="#8959e6" opacity="0.6" />
        <rect x="314" y="278" width="14" height="22" rx="4" fill="#31465a" opacity="0.2" />

        {/* ---- Counter ---- */}
        <rect x="240" y="342" width="140" height="10" rx="5" fill="#31465a" opacity="0.75" />
        <rect x="240" y="352" width="140" height="52" rx="8" fill="#31465a" opacity="0.12" />

        {/* Small plant on the counter, in a terracotta-free
            palette to keep to the site colours. */}
        <path
          d="M262 342c0-10 6-16 12-16s12 6 12 16z"
          fill="url(#haOrb)"
        />
        <rect x="266" y="342" width="16" height="12" rx="3" fill="#8959e6" opacity="0.55" />

        {/* ---- Confirmation panel ----
            The "order placed" state the hero is advertising. */}
        <rect x="256" y="378" width="108" height="62" rx="14" fill="#ffffff" />
        <rect
          x="256"
          y="378"
          width="108"
          height="62"
          rx="14"
          fill="none"
          stroke="#c7dfa3"
          strokeWidth="1.6"
        />

        <circle cx="278" cy="402" r="13" fill="#c7dfa3" />
        <path
          d="M272 402.5l4.4 4.6 8-9"
          fill="none"
          stroke="#31465a"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        <text
          x="300"
          y="400"
          fontFamily="Poppins, sans-serif"
          fontSize="10"
          fontWeight="600"
          fill="#31465a"
        >
          Order confirmed
        </text>

        <text
          x="300"
          y="414"
          fontFamily="Poppins, sans-serif"
          fontSize="8.5"
          fill="#6f7c87"
        >
          Arriving in 2 days
        </text>

        {/* A thin progress bar under the text. */}
        <rect x="300" y="422" width="52" height="4" rx="2" fill="#e7e8e4" />
        <rect x="300" y="422" width="34" height="4" rx="2" fill="#8959e6" />

        {/* Home indicator */}
        <rect x="288" y="460" width="44" height="5" rx="2.5" fill="#31465a" opacity="0.25" />
      </g>

      {/* =====================================================
          FLOATING CARDS
          Each card sits in its own group so it can drift on its
          own timing. The base rotation is applied to an inner
          group, keeping the CSS animation free to move the outer
          one without fighting the transform.
      ===================================================== */}

      {/* ---- Profile / preferences card ---- */}
      <g className="ha-card ha-card-1">
        <g transform="rotate(-7 122 196)">
          <rect
            x="46"
            y="152"
            width="152"
            height="88"
            rx="18"
            fill="#ffffff"
            filter="url(#haSoft)"
          />

          <circle cx="76" cy="184" r="15" fill="#d9f0ff" />
          <circle cx="76" cy="179" r="5.4" fill="#31465a" opacity="0.65" />
          <path d="M67 193a9.6 9.6 0 0 1 18 0z" fill="#31465a" opacity="0.65" />

          <text
            x="100"
            y="181"
            fontFamily="Poppins, sans-serif"
            fontSize="11"
            fontWeight="600"
            fill="#31465a"
          >
            Your taste
          </text>

          <text
            x="100"
            y="196"
            fontFamily="Poppins, sans-serif"
            fontSize="9"
            fill="#6f7c87"
          >
            Electronics · Home
          </text>

          {/* Three small tags */}
          <rect x="100" y="206" width="34" height="13" rx="6.5" fill="#eaf7ff" />
          <rect x="139" y="206" width="30" height="13" rx="6.5" fill="#eef6e2" />
        </g>
      </g>

      {/* ---- Match score card (the AI's headline number) ---- */}
      <g className="ha-card ha-card-2">
        <g transform="rotate(6 512 158)">
          <rect
            x="424"
            y="112"
            width="176"
            height="92"
            rx="18"
            fill="#31465a"
            filter="url(#haSoft)"
          />

          <text
            x="448"
            y="152"
            fontFamily="Poppins, sans-serif"
            fontSize="27"
            fontWeight="700"
            fill="#ffffff"
          >
            92%
          </text>

          <text
            x="448"
            y="170"
            fontFamily="Poppins, sans-serif"
            fontSize="9.5"
            fill="#c7dfa3"
          >
            recommendation match
          </text>

          {/* A small bar chart, so the card means "scored" at a
              glance rather than only in words. */}
          <rect x="448" y="182" width="60" height="5" rx="2.5" fill="#ffffff" opacity="0.22" />
          <rect x="448" y="182" width="46" height="5" rx="2.5" fill="#8959e6" />

          <circle cx="568" cy="140" r="15" fill="#8959e6" />
          <path
            d="M561 140l5 5 9-10"
            fill="none"
            stroke="#ffffff"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
      </g>

      {/* ---- Cart / user card ---- */}
      <g className="ha-card ha-card-3">
        <g transform="rotate(-5 132 424)">
          <rect
            x="52"
            y="386"
            width="164"
            height="74"
            rx="18"
            fill="#ffffff"
            filter="url(#haSoft)"
          />

          <rect x="76" y="408" width="22" height="24" rx="5" fill="#8959e6" opacity="0.85" />
          <path
            d="M80 408v-4a7 7 0 0 1 14 0v4"
            fill="none"
            stroke="#8959e6"
            strokeWidth="2.2"
            strokeLinecap="round"
          />

          <text
            x="110"
            y="418"
            fontFamily="Poppins, sans-serif"
            fontSize="11"
            fontWeight="600"
            fill="#31465a"
          >
            Cart updated
          </text>

          <text
            x="110"
            y="433"
            fontFamily="Poppins, sans-serif"
            fontSize="9"
            fill="#6f7c87"
          >
            3 items · Rs. 12,400
          </text>

          <rect x="110" y="442" width="88" height="4" rx="2" fill="#e7e8e4" />
          <rect x="110" y="442" width="58" height="4" rx="2" fill="#c7dfa3" />
        </g>
      </g>

      {/* ---- Rating card ---- */}
      <g className="ha-card ha-card-4">
        <g transform="rotate(8 528 402)">
          <rect
            x="452"
            y="360"
            width="152"
            height="86"
            rx="18"
            fill="#ffffff"
            filter="url(#haSoft)"
          />

          <text
            x="478"
            y="396"
            fontFamily="Poppins, sans-serif"
            fontSize="21"
            fontWeight="700"
            fill="#31465a"
          >
            4.8
          </text>

          {/* Five stars. Four are filled, the fifth is dimmed -
              which is more believable than five identical ones. */}
          <g fill="#8959e6">
            <path d="M500 388l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z" />
            <path d="M524 388l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z" />
            <path d="M548 388l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z" />
            <path d="M572 388l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z" />
          </g>

          <path
            d="M596 388l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z"
            fill="#31465a"
            opacity="0.18"
          />

          <text
            x="478"
            y="424"
            fontFamily="Poppins, sans-serif"
            fontSize="9"
            fill="#6f7c87"
          >
            from 128 reviews
          </text>
        </g>
      </g>

      {/* ---- Shopping bag ---- */}
      <g className="ha-card ha-card-5">
        <g transform="rotate(7 552 292)">
          <rect
            x="512"
            y="248"
            width="80"
            height="88"
            rx="16"
            fill="url(#haBag)"
            filter="url(#haTiny)"
          />

          {/* Handle */}
          <path
            d="M530 266v-8a22 22 0 0 1 44 0v8"
            fill="none"
            stroke="#ffffff"
            strokeOpacity="0.75"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* The SmartCart "C" */}
          <circle cx="552" cy="296" r="17" fill="#ffffff" opacity="0.22" />
          <path
            d="M561 290a12 12 0 1 0 0 13"
            fill="none"
            stroke="#ffffff"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
        </g>
      </g>
    </svg>
  );
}

export default HeroArt;
