import Navbar from "./Navbar";

/**
 * Wraps every interior page with the shared navbar.
 *
 * Why this exists: the navbar used to be rendered only inside the Home
 * component. That meant every other page - /products, /orders,
 * /manage, /admin, /recommendations, /product/:id - had NO navigation
 * at all. Once you went to one, the only way out was the browser's
 * back button. Easy to miss, and genuinely broken for a user.
 *
 * Doing it here rather than inside each page is deliberate: adding a
 * page cannot forget the navbar, because the route wraps it.
 */
function PageLayout({ children }) {
  return (
    <div className="app">
      <Navbar />
      {children}
    </div>
  );
}

export default PageLayout;
