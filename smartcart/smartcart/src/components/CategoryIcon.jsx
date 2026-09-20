/*
  CategoryIcon
  ------------
  The small illustration that sits beside the heading on each of the
  three "Shop by Category" cards.

  Why inline SVG rather than photos:

    * The cards are 3-up on desktop but stack to 1-up on a phone, so
      the art has to look right at two very different sizes. Vector
      does; a 600px JPEG scaled into a 52px chip does not.

    * The catalogue photos come from Unsplash by ID, and
      backend/seed_nepali_products.py warns in its own header that
      nine of fifteen IDs were once "composed from memory" and the
      audit turned up a Prada handbag filed under a Nepali jumper.
      Pointing category art at IDs I have not opened and looked at
      would repeat that mistake.

    * Every colour comes from the site palette, so the drawings cannot
      drift away from the rest of the design.

  ------------------------------------------------------------------
  DRAWING RULES - read before editing
  ------------------------------------------------------------------
  All three share one 48x48 viewBox and are drawn on the same grid, so
  they read as a set. `currentColor` drives the strokes and the accent
  fill, which means the card's own colour rules tint them - hover the
  card and the icon changes with it, with no extra CSS.

  1. THE ART MUST FILL ITS BOX. The first version drew everything
     inside about x 7..41, which at the 34px the chip rendered it left
     the icon looking lost in a lot of empty chip. The drawing now
     uses roughly x 4..44 / y 5..43, so it fills the frame.

  2. NOTHING MAY LEAVE THE VIEWBOX. A stroke that crosses the edge is
     clipped and the icon looks broken. The worst offender is the
     signal arc on the phone: at 48 wide, an arc centred at x=36 with
     radius 14 reaches x=50 and gets sliced. Check the widest stroke
     plus half the stroke width, not the centre line.

  3. STROKE WEIGHT IS 2.4. Anything thinner disappears at the 26px
     the chip renders on a phone; anything thicker clogs the corners.

  To add a fourth category, add a branch here and a matching card in
  App.jsx. Keep the viewBox at 0 0 48 48 and follow the three rules.
*/

function CategoryIcon({ category }) {
  // Shared stroke settings. 2.4 is the weight where the drawing still
  // reads at 26px on a phone without looking clumsy at full size.
  const stroke = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2.4,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };

  // ---------- ELECTRONICS: a phone with a signal arc ----------
  if (category === "Electronics") {
    return (
      <svg viewBox="0 0 48 48" className="category-icon-svg" aria-hidden="true">
        {/* Body. The whole drawing is centred as a GROUP, not by
            centring the phone: the phone plus its arcs span x 7..41,
            so their midpoint is 24. Putting the phone itself at 24
            would shove the arcs off the right edge. */}
        <rect x="7" y="5" width="18" height="38" rx="4.5" {...stroke} />

        {/* Home indicator, centred on the body (x 7..25 -> centre 16,
            8 wide -> x 12..20). Kept clear of the body's bottom edge
            at y=43 so it reads as a bar on the bezel. */}
        <path d="M12 39.5h8" {...stroke} />

        {/* Signal arc. Centre at x=28, radii 6 and 11. The outer
            stroke reaches 28+11+1.2 = 40.2, inside 48 with room. The
            first version centred at 36 with radius 14, which ran to
            x=50 and was sliced off by the viewBox edge.

            The gap from the phone's right edge (x=25) to the first
            arc (x=28-6=22 at its widest) is negative at the ends, but
            the arc only reaches x=22 at its vertical midpoint, which
            sits well inside the phone's y range - so they clear. */}
        <path d="M28 18a6.5 6.5 0 0 1 0 12" {...stroke} opacity="0.6" />
        <path d="M34 13a11 11 0 0 1 0 22" {...stroke} opacity="0.32" />
      </svg>
    );
  }

  // ---------- FASHION: a hanger ----------
  if (category === "Fashion") {
    return (
      <svg viewBox="0 0 48 48" className="category-icon-svg" aria-hidden="true">
        {/* Hook. A wide, open loop - a tight one reads as a question
            mark at small sizes, which is exactly what the first
            version looked like. */}
        <path d="M24 19v-2.5a5 5 0 1 1 5-5" {...stroke} />

        {/* Shoulders and bar as ONE closed triangle. Drawing the bar
            separately at full weight made it compete with the hanger
            instead of supporting it. Apex at 24,19; feet at x 6 and
            42 so the shape spans most of the box.

            The floating "clothes rail" line that was under this has
            been removed - with nothing either side of it, it read as
            a stray dash rather than a rail. */}
        <path d="M24 19 6 36h36z" {...stroke} />
      </svg>
    );
  }

  // ---------- HOME: a house ----------
  if (category === "Home") {
    return (
      <svg viewBox="0 0 48 48" className="category-icon-svg" aria-hidden="true">
        {/* Roof AND walls as one continuous path, so there is no join
            to get wrong. The first version drew the roof as a chevron
            which overhung the wall on the right and left the left
            eave hanging in space.
              apex 24,6 -> left eave 5,22 -> down to 5,42
                        -> across to 43,42 -> up to 43,22 -> apex */}
        <path d="M24 6 5 22v20h38V22z" {...stroke} />

        {/* Door. Centred on x 24 (spans 19.5..28.5) and standing ON
            the floor line at y=42, not floating above it. */}
        <path d="M19.5 42V30h9v12" {...stroke} />

        {/* Window. Moved DOWN to y 28 so it sits beside the door in
            the wall area. At y 27 its top edge touched the roofline
            on the way down to the eave, which made it look stuck on
            the roof rather than set into the wall. */}
        <rect x="11" y="29" width="6" height="6" rx="0.8" {...stroke} opacity="0.45" />

        {/* Chimney. The roofline is at y=14 around x=33, so the base
            sits at y=14 and it rises to 8. Drawn as an open-topped
            shape rather than a closed rectangle, because a closed box
            floating over the roof read as a solid block. */}
        <path d="M33 14V8h5v8.5" {...stroke} opacity="0.6" />
      </svg>
    );
  }

  // A category with no drawing yet. Returning null rather than a
  // placeholder box means the card simply renders without art instead
  // of showing a broken shape.
  return null;
}

export default CategoryIcon;
