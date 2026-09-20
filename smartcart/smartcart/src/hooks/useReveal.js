import { useEffect, useRef, useState } from "react";

/*
  useReveal
  ---------
  Returns a ref to attach to an element, and a boolean saying whether
  that element has entered the viewport yet. Pair it with the `.reveal`
  and `.reveal-in` classes in App.css.

  Why a hook rather than a pure-CSS animation:

    A CSS `animation` on page load fires immediately, whether or not
    the element is on screen. Everything below the fold therefore
    animates while nobody is looking, and the user scrolls down to
    find it already finished - so the effect does nothing. Watching
    the element instead means the animation starts when the eye
    actually arrives.

  ------------------------------------------------------------------
  WHY THE DEFAULT IS "VISIBLE"
  ------------------------------------------------------------------
  The element is treated as already shown unless we are certain we can
  animate it. That ordering matters:

    If the hook instead reported "hidden" by default and waited for an
    observer to correct it, then a browser without
    IntersectionObserver - or a JavaScript error anywhere earlier in
    the bundle - would leave the whole page blank. Hiding content
    should be the *upgrade*, never the default.

  `canObserve` and `wantsReducedMotion` are both checked before the
  effect does anything, and the `.reveal` class is added to the
  element from inside that effect rather than rendered by React - so
  if the effect never runs, nothing is ever hidden.

  The same reasoning covers `prefers-reduced-motion`: when motion is
  reduced there is no animation, no flash, and nothing to go wrong.

  ------------------------------------------------------------------
  USAGE
  ------------------------------------------------------------------
      const [ref, shown] = useReveal();

      <div ref={ref} className={`reveal ${shown ? "reveal-in" : ""}`}>
        ...
      </div>

  For a staggered group, pass a delay in ms:

      const [ref, shown] = useReveal({ delay: index * 80 });

  The delay is written to the element as `--reveal-delay` and read by
  the CSS transition, which keeps the timing in one place.

  `once` is on by default: an element that has been revealed stays
  revealed. Re-animating on every scroll back up is distracting, and
  on a long product list it is a lot of needless work.
*/

function useReveal({
  delay = 0,
  // Fraction of the element that must be visible before it counts as
  // "entered". 0.12 means a sliver is not enough - the element has to
  // be meaningfully on screen. Set to 0 for very tall elements where
  // 12% may never fit in the viewport on a phone.
  threshold = 0.12,
  // Shrink the observation area so the element is revealed slightly
  // BEFORE it reaches the bottom edge, rather than exactly as it
  // touches it. Revealing at the last pixel looks like a glitch,
  // because the user sees the empty state for a moment first.
  rootMargin = "0px 0px -60px 0px",
  once = true,
} = {}) {
  const ref = useRef(null);

  /*
    Start VISIBLE, and stay visible without any state update at all in
    the cases where we are not going to animate:

      - the browser has no IntersectionObserver
      - the user has asked for reduced motion

    Both are resolved once, lazily, on the first render rather than in
    an effect. That matters for two reasons: it avoids a second render
    just to flip the value, and - since these conditions do not change
    during a session - there is nothing to subscribe to. Resolving them
    in an effect would be both slower and, as the linter correctly
    pointed out, a cascading render for no benefit.

    The effect below therefore only has one job: observing.
  */
  const [shown, setShown] = useState(false);

  const canObserve =
    typeof window !== "undefined" &&
    typeof IntersectionObserver !== "undefined";

  const wantsReducedMotion =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // If we cannot observe, or should not animate, the element is
  // treated as already shown - so the effect never runs and the hook
  // returns a permanently visible element.
  const isShown = shown || !canObserve || wantsReducedMotion;

  useEffect(() => {
    const element = ref.current;

    if (!element) return undefined;

    // Nothing to do: the element is visible and staying that way.
    if (!canObserve || wantsReducedMotion) return undefined;

    // Hide it only now that we know we are able to reveal it again.
    // Adding the class here rather than rendering it means that if
    // anything above throws, the element is left visible rather than
    // stuck at opacity 0.
    //
    // Skipped if this element has already been revealed. React runs
    // effects twice in development StrictMode, and the cleanup below
    // removes the class in between - so without this guard the second
    // pass would re-hide an element the user has already seen, and it
    // would visibly blink.
    if (!shown) {
      element.classList.add("reveal");
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setShown(true);

            if (once) {
              observer.unobserve(entry.target);
            }
          } else if (!once) {
            setShown(false);
          }
        });
      },
      { threshold, rootMargin }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
      element.classList.remove("reveal");
    };
  }, [threshold, rootMargin, once, canObserve, wantsReducedMotion, shown]);

  // The delay is exposed as a custom property so the CSS transition
  // reads it. Setting it here rather than in a style attribute at the
  // call site keeps the staggering logic next to the timing.
  const style = delay ? { "--reveal-delay": `${delay}ms` } : undefined;

  return [ref, isShown, style];
}

export default useReveal;
