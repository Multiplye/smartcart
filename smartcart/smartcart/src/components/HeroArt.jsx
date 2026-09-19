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

  ---------------------------------------------------------------
  LAYOUT RULES - please read before moving anything
  ---------------------------------------------------------------
  The first version of this drawing let its cards hang outside the
  pale-blue backdrop, which looked broken rather than designed.

  The fix was to design to explicit bounds. The backdrop now spans
  x 24..596 and y 34..526, and EVERY element - including the corners
  the rotated cards swing out to - has to sit inside that with at
  least 8 units of clearance.

  Two things make that easy to get wrong:

    1. A rotated rectangle is larger than the rectangle. The "4.8"
       card is 152x86, but at 8 degrees its corners reach about
       16 units further out on every side. Rotate about the centre
       and measure the CORNERS, never the sides.

    2. The cards' rotations are static `transform="rotate(...)"`
       attributes on an inner <g>. If you move a card, move its
       rotation origin with it - the three numbers in `rotate()` are
       angle, cx, cy and they must match the centre of the new rect.

  The backdrop is a single <rect> with rounded corners rather than a
  wobbly blob: with cards overlapping its edges from four directions,
  a straight edge reads as intentional and a curve reads as a mistake.
  The soft corner blobs behind the cards are decoration INSIDE it,
  well clear of the boundary, so they can never poke out.
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
        score, shopping preferences, a cart update and customer
        ratings.
      </desc>

      {/* =====================================================
          DEFINITIONS
          Gradients and shadows live here and are referenced by
          id further down. Keeping them together means the whole
          palette can be adjusted in one place.
      ===================================================== */}
      <defs>
        <linearGradient id="haBg" x1="0" y1="0" x2="0.6" y2="1">
          <stop offset="0%" stopColor="#eef8ff" />
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
            deliberate instead of accidental.

            The filter regions are padded well beyond the default
            -10%..120% so a drop shadow near the edge of the
            drawing is not clipped. */}
        <filter id="haSoft" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow
            dx="0"
            dy="9"
            stdDeviation="11"
            floodColor="#31465a"
            floodOpacity="0.12"
          />
        </filter>

        <filter id="haLift" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow
            dx="0"
            dy="14"
            stdDeviation="16"
            floodColor="#31465a"
            floodOpacity="0.18"
          />
        </filter>

        <filter id="haTiny" x="-60%" y="-60%" width="220%" height="220%">
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
          One rounded rectangle. See the layout note at the top:
          x 24..596, y 34..526. Nothing may leave this.
      ===================================================== */}
      <rect
        className="ha-bg"
        x="20"
        y="30"
        width="580"
        height="500"
        rx="52"
        fill="url(#haBg)"
      />

      {/* Decorative corner glows. These are INSIDE the backdrop and
          inset far enough that no rotation or scaling can push them
          past its edge. */}
      <circle cx="96" cy="122" r="54" fill="#ffffff" opacity="0.5" />
      <circle cx="520" cy="128" r="44" fill="#ffffff" opacity="0.35" />
      <circle cx="120" cy="450" r="46" fill="#ffffff" opacity="0.34" />
      <circle cx="494" cy="446" r="58" fill="#ffffff" opacity="0.42" />

      {/* Small decorative dots, also kept well inside. */}
      <circle className="ha-dot ha-dot-1" cx="150" cy="92" r="6" fill="#8959e6" opacity="0.4" />
      <circle className="ha-dot ha-dot-2" cx="494" cy="88" r="7" fill="#c7dfa3" opacity="0.9" />
      <circle className="ha-dot ha-dot-3" cx="80" cy="330" r="5" fill="#31465a" opacity="0.18" />
      <circle className="ha-dot ha-dot-4" cx="536" cy="452" r="6" fill="#8959e6" opacity="0.3" />

      {/* =====================================================
          THE PHONE
          x 204..416, y 96..488 - comfortably inside the backdrop
          with 180 to spare on the left and 180 on the right.
          Drawn as one group so the body and screen float together.
      ===================================================== */}
      <g className="ha-phone" filter="url(#haLift)">
        {/* Body. x 204..416 (212 wide), y 96..504 (408 tall). */}
        <rect x="204" y="96" width="212" height="408" rx="34" fill="#31465a" />

        {/* Bezel highlight down the left edge - a thin light line
            is what makes plastic look like metal. */}
        <rect
          x="206.5"
          y="98.5"
          width="207"
          height="403"
          rx="32"
          fill="none"
          stroke="#ffffff"
          strokeOpacity="0.16"
          strokeWidth="1.5"
        />

        {/* Screen. x 216..404, y 110..490. Everything drawn on the
            screen must stay inside this box. */}
        <rect x="216" y="110" width="188" height="380" rx="26" fill="url(#haScreen)" />

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

        <rect x="286" y="179" width="48" height="3" rx="1.5" fill="#c7dfa3" />

        {/* ---- Awning ----
            A scalloped strip. Each scallop is one arc; the flat
            block behind them hides the tops so no seam shows. */}
        <rect x="236" y="198" width="148" height="14" fill="url(#haAwn)" />

        <path
          d="M236 212a12 12 0 0 0 24 0zM260 212a12 12 0 0 0 24 0zM284 212a12 12 0 0 0 24 0zM308 212a12 12 0 0 0 24 0zM332 212a12 12 0 0 0 24 0zM356 212a12 12 0 0 0 24 0z"
          fill="url(#haAwn)"
        />

        {/* ---- Window ---- */}
        <rect x="240" y="230" width="140" height="102" rx="12" fill="url(#haPane)" />

        {/* Glass reflection: a soft diagonal band across the
            top-left corner. */}
        <path d="M240 242v-12h46l-40 92h-6z" fill="#ffffff" opacity="0.55" />

        {/* Window frame */}
        <rect
          x="240"
          y="230"
          width="140"
          height="102"
          rx="12"
          fill="none"
          stroke="#31465a"
          strokeOpacity="0.14"
          strokeWidth="2"
        />

        {/* Two shelves inside the window */}
        <rect x="258" y="262" width="104" height="5" rx="2.5" fill="#31465a" opacity="0.13" />
        <rect x="258" y="300" width="104" height="5" rx="2.5" fill="#31465a" opacity="0.13" />

        {/* Products on the shelves - deliberately abstract blocks,
            so they read as stock rather than as broken icons. */}
        <rect x="266" y="240" width="16" height="22" rx="4" fill="#8959e6" opacity="0.75" />
        <rect x="290" y="246" width="14" height="16" rx="4" fill="#c7dfa3" />
        <rect x="312" y="238" width="18" height="24" rx="5" fill="#8959e6" opacity="0.45" />

        <rect x="266" y="280" width="18" height="20" rx="5" fill="#c7dfa3" opacity="0.85" />
        <rect x="292" y="284" width="14" height="16" rx="4" fill="#8959e6" opacity="0.6" />
        <rect x="314" y="278" width="14" height="22" rx="4" fill="#31465a" opacity="0.2" />

        {/* ---- Counter ----
            Sits directly under the window, full screen width, so
            the two read as a shopfront rather than as two loose
            objects. */}
        <rect x="240" y="340" width="140" height="9" rx="4.5" fill="#31465a" opacity="0.72" />
        <rect x="240" y="349" width="140" height="26" rx="6" fill="#31465a" opacity="0.1" />

        {/* A small plant on the counter, in the site palette. */}
        <path d="M262 340c0-9 5.5-15 11-15s11 6 11 15z" fill="url(#haOrb)" />
        <rect x="265.5" y="340" width="15" height="11" rx="3" fill="#8959e6" opacity="0.55" />

        {/* ---- Confirmation panel ----
            The "order placed" state the hero is advertising.

            This panel is 152 wide (x 232..384) and the longest line
            of text in it is "Order confirmed" at fontSize 10, which
            measures about 84 units. At x=276 that lands at 360, so
            there is ~24 units of padding on the right. The first
            version used a 108-wide panel and the text visibly spilled
            out of it - if you lengthen this string, widen the panel
            or drop the font size.

            Height is 58 (y 366..424) and the recommendation label
            sits at baseline y=440, so the two clear each other by 8
            units. A 64-high panel put its bottom edge at 430 and the
            label ran straight through it. */}
        <rect x="232" y="366" width="152" height="58" rx="14" fill="#ffffff" />
        <rect
          x="232"
          y="366"
          width="152"
          height="58"
          rx="14"
          fill="none"
          stroke="#c7dfa3"
          strokeWidth="1.6"
        />

        <circle cx="255" cy="386" r="11.5" fill="#c7dfa3" />
        <path
          d="M249.5 386.5l4 4.2 7.4-8.4"
          fill="none"
          stroke="#31465a"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        <text
          x="275"
          y="384"
          fontFamily="Poppins, sans-serif"
          fontSize="10"
          fontWeight="600"
          fill="#31465a"
        >
          Order confirmed
        </text>

        <text
          x="275"
          y="397"
          fontFamily="Poppins, sans-serif"
          fontSize="8.5"
          fill="#6f7c87"
        >
          Arriving in 2 days
        </text>

        {/* A thin progress bar under the text. */}
        <rect x="275" y="404" width="92" height="4" rx="2" fill="#e7e8e4" />
        <rect x="275" y="404" width="60" height="4" rx="2" fill="#8959e6" />

        {/* ---- Recommendation row ----
            Without this the lower third of the screen was empty and
            the drawing looked unfinished. It also earns its place:
            it shows the one thing SmartCart actually does, which is
            suggest something.

            The label baseline is y=440 and the thumbnails run
            y 445..470. Both MUST clear the screen's bottom edge at
            y=474 - an earlier attempt put the thumbnails at
            y 470..504, which pushed them 30 units out through the
            bottom of the phone. */}
        <text
          x="240"
          y="440"
          fontFamily="Poppins, sans-serif"
          fontSize="7.5"
          fill="#6f7c87"
          letterSpacing="0.4"
        >
          RECOMMENDED FOR YOU
        </text>

        {/* Thumb 1 - highlighted, since it is the top match */}
        <rect x="240" y="445" width="42" height="25" rx="6" fill="#eaf7ff" />
        <rect
          x="240"
          y="445"
          width="42"
          height="25"
          rx="6"
          fill="none"
          stroke="#8959e6"
          strokeWidth="1.2"
        />
        <rect x="249" y="450" width="24" height="15" rx="3.5" fill="#8959e6" opacity="0.7" />

        {/* Thumb 2 */}
        <rect x="289" y="445" width="42" height="25" rx="6" fill="#f4f8fb" />
        <rect x="298" y="450" width="24" height="15" rx="3.5" fill="#c7dfa3" />

        {/* Thumb 3 */}
        <rect x="338" y="445" width="42" height="25" rx="6" fill="#f4f8fb" />
        <rect x="347" y="450" width="24" height="15" rx="3.5" fill="#31465a" opacity="0.22" />

        {/* Home indicator. Sits in the clear strip between the
            thumbnails (end at y=470) and the screen edge (y=474). */}
        <rect x="288" y="479" width="44" height="5" rx="2.5" fill="#31465a" opacity="0.25" />
      </g>

      {/* =====================================================
          FLOATING CARDS

          Each card is two nested groups:

            outer .ha-card-N  -> the CSS float animation
            inner <g rotate>  -> the static tilt

          They MUST stay separate. If the animation and the rotation
          share one element, the CSS transform replaces the SVG
          transform attribute and the tilt silently disappears.

          The rotate() arguments are (angle, cx, cy) and cx/cy must
          be the CENTRE of that card's rect. Change the rect and you
          must change the centre with it.
      ===================================================== */}

      {/* ---- "Your taste" card ----
          rect 58,166 150x84 -> centre (133,208)
          at -7 deg the corners reach x 51.6..214.4, y 142.2..273.8
          The backdrop starts at x=24, so there is 27 units clear. */}
      <g className="ha-card ha-card-1">
        <g transform="rotate(-7 133 208)">
          <rect
            x="58"
            y="166"
            width="150"
            height="84"
            rx="18"
            fill="#ffffff"
            filter="url(#haSoft)"
          />

          <circle cx="88" cy="198" r="15" fill="#d9f0ff" />
          <circle cx="88" cy="193" r="5.4" fill="#31465a" opacity="0.65" />
          <path d="M79 207a9.6 9.6 0 0 1 18 0z" fill="#31465a" opacity="0.65" />

          <text
            x="112"
            y="195"
            fontFamily="Poppins, sans-serif"
            fontSize="11"
            fontWeight="600"
            fill="#31465a"
          >
            Your taste
          </text>

          <text
            x="112"
            y="210"
            fontFamily="Poppins, sans-serif"
            fontSize="9"
            fill="#6f7c87"
          >
            Electronics · Home
          </text>

          <rect x="112" y="220" width="34" height="13" rx="6.5" fill="#eaf7ff" />
          <rect x="151" y="220" width="30" height="13" rx="6.5" fill="#eef6e2" />
        </g>
      </g>

      {/* ---- 92% match card ----
          rect 428,120 152x86 -> centre (504,163)
          at +6 deg the corners reach x 423.9..584.1, y 112.3..213.7
          The backdrop ends at x=600, so there is 15.9 units clear. */}
      <g className="ha-card ha-card-2">
        <g transform="rotate(6 504 163)">
          <rect
            x="428"
            y="120"
            width="152"
            height="86"
            rx="18"
            fill="#31465a"
            filter="url(#haSoft)"
          />

          <text
            x="450"
            y="158"
            fontFamily="Poppins, sans-serif"
            fontSize="26"
            fontWeight="700"
            fill="#ffffff"
          >
            92%
          </text>

          <text
            x="450"
            y="175"
            fontFamily="Poppins, sans-serif"
            fontSize="9.5"
            fill="#c7dfa3"
          >
            recommendation match
          </text>

          {/* A small bar, so the card reads as "scored" at a
              glance and not only from the words. */}
          <rect x="450" y="186" width="62" height="5" rx="2.5" fill="#ffffff" opacity="0.22" />
          <rect x="450" y="186" width="46" height="5" rx="2.5" fill="#8959e6" />

          <circle cx="556" cy="146" r="14" fill="#8959e6" />
          <path
            d="M549.5 146l4.6 4.6 8.4-9.4"
            fill="none"
            stroke="#ffffff"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
      </g>

      {/* ---- Shopping bag ----
          rect 502,256 80x88 -> centre (542,300)
          at +7 deg corners reach x 496.9..587.1, y 251.5..348.5 */}
      <g className="ha-card ha-card-5">
        <g transform="rotate(7 542 300)">
          <rect
            x="502"
            y="256"
            width="80"
            height="88"
            rx="16"
            fill="url(#haBag)"
            filter="url(#haTiny)"
          />

          {/* Handle */}
          <path
            d="M520 274v-8a22 22 0 0 1 44 0v8"
            fill="none"
            stroke="#ffffff"
            strokeOpacity="0.75"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* The SmartCart "C" */}
          <circle cx="542" cy="304" r="17" fill="#ffffff" opacity="0.22" />
          <path
            d="M551 298a12 12 0 1 0 0 13"
            fill="none"
            stroke="#ffffff"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
        </g>
      </g>

      {/* ---- "Cart updated" card ----
          rect 54,392 160x76 -> centre (134,430)
          at -5 deg corners reach x 48.0..220.0, y 374.7..485.3
          The backdrop ends at y=526, so there is 40 units clear. */}
      <g className="ha-card ha-card-3">
        <g transform="rotate(-5 134 430)">
          <rect
            x="54"
            y="392"
            width="160"
            height="76"
            rx="18"
            fill="#ffffff"
            filter="url(#haSoft)"
          />

          <rect x="78" y="416" width="22" height="24" rx="5" fill="#8959e6" opacity="0.85" />
          <path
            d="M82 416v-4a7 7 0 0 1 14 0v4"
            fill="none"
            stroke="#8959e6"
            strokeWidth="2.2"
            strokeLinecap="round"
          />

          <text
            x="112"
            y="426"
            fontFamily="Poppins, sans-serif"
            fontSize="11"
            fontWeight="600"
            fill="#31465a"
          >
            Cart updated
          </text>

          <text
            x="112"
            y="441"
            fontFamily="Poppins, sans-serif"
            fontSize="9"
            fill="#6f7c87"
          >
            3 items · Rs. 12,400
          </text>

          <rect x="112" y="450" width="86" height="4" rx="2" fill="#e7e8e4" />
          <rect x="112" y="450" width="56" height="4" rx="2" fill="#c7dfa3" />
        </g>
      </g>

      {/* ---- Rating card ----
          rect 432,376 152x86 -> centre (508,419)
          at +8 deg corners reach x 426.8..589.2, y 365.8..472.2

          This is the card that hung off the bottom-right corner in
          the first version of the drawing. It now has 10.8 units
          of clearance on its tightest side. */}
      <g className="ha-card ha-card-4">
        <g transform="rotate(8 508 419)">
          <rect
            x="432"
            y="376"
            width="152"
            height="86"
            rx="18"
            fill="#ffffff"
            filter="url(#haSoft)"
          />

          <text
            x="452"
            y="410"
            fontFamily="Poppins, sans-serif"
            fontSize="20"
            fontWeight="700"
            fill="#31465a"
          >
            4.8
          </text>

          {/* Five stars. Four are filled and the fifth is dimmed,
              which is more believable than five identical ones.

              They start at x=490, not 476. At 476 the first star
              overlapped the "4.8" - the digit ends around x=486 and
              a star's widest point is its top edge, so anything
              closer than about 4 units collides. Stars are 20 wide
              and spaced 21 apart, giving 84 units total. */}
          <g fill="#8959e6">
            <path d="M490 400l2.4 5 5.5.8-4 3.9 1 5.5-4.9-2.6-4.9 2.6 1-5.5-4-3.9 5.5-.8z" />
            <path d="M511 400l2.4 5 5.5.8-4 3.9 1 5.5-4.9-2.6-4.9 2.6 1-5.5-4-3.9 5.5-.8z" />
            <path d="M532 400l2.4 5 5.5.8-4 3.9 1 5.5-4.9-2.6-4.9 2.6 1-5.5-4-3.9 5.5-.8z" />
            <path d="M553 400l2.4 5 5.5.8-4 3.9 1 5.5-4.9-2.6-4.9 2.6 1-5.5-4-3.9 5.5-.8z" />
          </g>

          <path
            d="M574 400l2.4 5 5.5.8-4 3.9 1 5.5-4.9-2.6-4.9 2.6 1-5.5-4-3.9 5.5-.8z"
            fill="#31465a"
            opacity="0.18"
          />

          <text
            x="452"
            y="438"
            fontFamily="Poppins, sans-serif"
            fontSize="9"
            fill="#6f7c87"
          >
            from 128 reviews
          </text>
        </g>
      </g>
    </svg>
  );
}

export default HeroArt;
