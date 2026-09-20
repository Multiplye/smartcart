import { Link } from "react-router-dom";

import Reveal from "./Reveal";
import CategoryIcon from "./CategoryIcon";

/*
  NotFound
  --------
  Shown for any URL that matches no route.

  Before this existed the app had no catch-all route at all, so an
  unknown path rendered literally nothing - not even the navbar, since
  the navbar setup lives inside each page rather than around them.
  A mistyped URL gave you a blank white screen with no way back, which
  looks like the site is broken rather than like the page is missing.

  Two deliberate choices:

    * It is wrapped in PageLayout by the route, so it gets the navbar
      and the footer. The user can always navigate away.

    * It offers the three most likely destinations rather than one
      "go home" link. Someone who mistyped /product/12 is probably
      looking for the catalogue, not the landing page.
*/

function NotFound() {
  return (
    <main className="notfound-page">
      <Reveal className="notfound-inner" variant="lg">
        <span className="section-label">
          ERROR 404
        </span>

        <h1>
          We could not find
          <br />
          <span>that page.</span>
        </h1>

        <p>
          The link may be out of date, or the address may have a
          typo in it. Everything else is still where you left it.
        </p>

        {/* The three places someone is most likely to have been
            heading. The catalogue leads, because that is the most
            common destination from a broken link. */}
        <div className="notfound-actions">
          <Link to="/products" className="shop-btn">
            Browse Products
          </Link>

          <Link to="/recommendations" className="learn-btn">
            See Recommendations
          </Link>

          <Link to="/" className="learn-btn">
            Back to Home
          </Link>
        </div>

        {/* A light visual echo of the category cards, so the page
            looks designed rather than like a dead end. Decorative
            only - hence aria-hidden on each. */}
        <div className="notfound-icons" aria-hidden="true">
          {["Electronics", "Fashion", "Home"].map((name) => (
            <span className="notfound-icon" key={name}>
              <CategoryIcon category={name} />
            </span>
          ))}
        </div>
      </Reveal>
    </main>
  );
}

export default NotFound;
