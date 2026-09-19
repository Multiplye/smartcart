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
 * The delay matters for case 2: the home page has to render its
 * sections before an element with that id exists. A single frame is
 * usually not enough, so we give it a short timeout and also retry.
 */
function ScrollManager() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    // No hash: a fresh page should start at the top.
    if (!hash) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return undefined;
    }

    const id = hash.slice(1);
    let attempts = 0;

    // Try for about half a second. The element may not exist on the
    // first tick because the target page is still rendering.
    const timer = window.setInterval(() => {
      const element = document.getElementById(id);

      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
        window.clearInterval(timer);
        return;
      }

      attempts += 1;

      if (attempts > 10) window.clearInterval(timer);
    }, 50);

    return () => window.clearInterval(timer);
  }, [pathname, hash]);

  // This component only exists for its side effect.
  return null;
}

export default ScrollManager;
