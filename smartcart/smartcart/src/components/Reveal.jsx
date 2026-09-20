import useReveal from "../hooks/useReveal";

/*
  Reveal
  ------
  A thin wrapper around useReveal so applying the scroll animation
  does not mean threading a ref, a boolean and a style object through
  every call site. Reading

      <Reveal delay={i * 80} className="product-card"> ... </Reveal>

  is a lot clearer than the three-line equivalent, and it keeps the
  `${shown ? "reveal-in" : ""}` template in one place instead of
  repeated across a dozen components.

  Props:
    as        - element to render. Defaults to a div, but pass "li",
                "section", "article" etc. so the markup stays semantic.
    delay     - stagger in ms.
    variant   - "", "lg" or "fade". See the CSS block for what each does.
    className - merged with the reveal classes, so existing styling
                on the element is untouched.
    ...rest   - everything else is passed straight through (id, style,
                aria-* and so on).

  Note that the reveal classes are added to the EXISTING className
  rather than replacing it. A product card keeps being a
  `.product-card`; it just also becomes a `.reveal`.
*/

function Reveal({
  as: Element = "div",
  delay = 0,
  variant = "",
  className = "",
  children,
  style,
  ...rest
}) {
  const [ref, shown, delayStyle] = useReveal({ delay });

  const variantClass =
    variant === "lg" ? "reveal-lg" : variant === "fade" ? "reveal-fade" : "";

  // `ref` is attached through the DOM property rather than as a JSX
  // attribute, because it has to land on whichever element `as`
  // renders, and that tag is not known until runtime.
  //
  // ORDER MATTERS HERE. `{...rest}` is spread FIRST, and className and
  // style are set after it. If it were the other way round, a caller
  // passing their own className or style would overwrite the reveal
  // classes and the stagger delay, and the element would simply never
  // animate - with no error to explain why. Because `as` is destructured
  // out above, it cannot come back through `rest` and crash the element.
  return (
    <Element
      {...rest}
      ref={ref}
      className={[
        className,
        "reveal",
        variantClass,
        shown ? "reveal-in" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ ...style, ...delayStyle }}
    >
      {children}
    </Element>
  );
}

export default Reveal;
