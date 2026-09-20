import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * Scrolls the window in response to navigation.
 *
 * Handles two cases that React Router does not do for you:
 *
 *   1. A normal page change -> scroll to the top. Without this,
 *      clicking from a long product list to a product page leaves you
 *      halfway down the new page, which feels broken.
 *
 *   2. A link with a hash, like "/#categories" -> scroll to that
 *      section instead. This is what makes the navbar's "Categories"
 *      and "About" links work when you are on /admin and those
 *      sections are back on the home page.
 *
 * ---------------------------------------------------------------------
 * Why this is not a one-shot scrollIntoView
 * ---------------------------------------------------------------------
 * The first version was: poll every 50ms for up to 500ms, and the first
 * time the element exists, scrollIntoView() and stop.
 *
 * That silently undershot. Measured on the real home page, arriving at
 * /#auth from /checkout landed 580px short of the login form and then
 * stayed there:
 *
 *     t=1.0s  y=3918   auth 955px down the viewport
 *     t=1.5s  y=4293   auth 580px down   <- stopped for good
 *     ...unchanged for the next 6.5 seconds...
 *
 * Two separate causes, both fixed below:
 *
 *   a) The home page is still growing when we scroll. Product images
 *      load asynchronously and each one that arrives pushes everything
 *      below it further down. We scrolled to where the form was, then
 *      the form moved.
 *
 *   b) We stopped after 500ms. Anything the page does after that was
 *      unaccounted for.
 *
 * So instead of scrolling once, we keep re-aiming at the target until
 * it stops moving. `targetY` is recalculated from the element's current
 * position on every tick, which absorbs any layout shift above it.
 * A short settle period with no movement ends the loop.
 */

// How long to keep trying before giving up. Generous on purpose: the
// loop exits as soon as the target settles, so a long ceiling costs
// nothing in the normal case and only matters on a slow connection.
const MAX_ATTEMPTS = 60; // 60 x 50ms = 3s

// Ticks with no movement that count as "it has settled".
const SETTLED_TICKS = 4; // 200ms

// How close to the final position counts as arrived, in px.
const CLOSE_ENOUGH = 2;

function ScrollManager() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    // ---------- Case 1: no hash, start at the top ----------
    //
    // `behavior: "auto"` rather than "smooth" on purpose. A smooth
    // scroll here animates the page from wherever it was to the top,
    // which on a route change means the user watches the previous
    // page slide past. Instant is what reads as "a new page loaded".
    if (!hash) {
      window.scrollTo({ top: 0, behavior: "auto" });
      return undefined;
    }

    // ---------- Case 2: hash, aim at the section ----------
    const id = hash.slice(1);
    let attempts = 0;
    let settled = 0;
    let lastTargetY = null;

    const timer = window.setInterval(() => {
      attempts += 1;

      const element = document.getElementById(id);

      // Give up rather than retry forever if the section never appears.
      if (attempts > MAX_ATTEMPTS) {
        window.clearInterval(timer);
        return;
      }

      if (!element) return;

      // Where the section actually is right now. Recomputed every tick
      // so that anything which grew above it (lazy images, mostly) is
      // already taken into account.
      const top =
        element.getBoundingClientRect().top + window.scrollY;

      // Clamp to what the browser can actually reach. Scrolling to a
      // value past the maximum would make the loop below succeed while
      // the target is still off-screen, and we would stop short.
      const maxScroll =
        document.documentElement.scrollHeight - window.innerHeight;
      const targetY = Math.max(0, Math.min(Math.round(top), maxScroll));

      const moved = lastTargetY === null ? Infinity : Math.abs(targetY - lastTargetY);
      lastTargetY = targetY;

      // Has the page stopped moving the target?
      if (moved <= CLOSE_ENOUGH) {
        settled += 1;
      } else {
        settled = 0;
      }

      const arrived = Math.abs(window.scrollY - targetY) <= CLOSE_ENOUGH;

      if (arrived && settled >= SETTLED_TICKS) {
        window.clearInterval(timer);
        return;
      }

      // The first scroll is animated, because that one the user should
      // see. Once we are only correcting for layout shift, jumping is
      // correct - a smooth animation fighting a shifting page shows up
      // as a jitter.
      window.scrollTo({
        top: targetY,
        behavior: attempts === 1 ? "smooth" : "auto",
      });
    }, 50);

    return () => window.clearInterval(timer);
  }, [pathname, hash]);

  // This component only exists for its side effect.
  return null;
}

export default ScrollManager;
