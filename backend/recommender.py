"""
SmartCart - Recommendation Engine
==================================

HOW IT WORKS, IN PLAIN ENGLISH
------------------------------

This is a CONTENT-BASED recommender. It does not know anything about
other shoppers. It looks only at what the products themselves say, and
finds products whose descriptions look alike.

The technique is called TF-IDF with cosine similarity. Two fairly
scary names for two simple ideas.

  TF-IDF  ("term frequency - inverse document frequency")

      Turn each product into a list of numbers, one per word.

      The "TF" part: a word that appears a lot in THIS product's text
      matters more for this product.

      The "IDF" part: but a word that appears in EVERY product - like
      "the" or "and" or, in our data, "product" - tells us nothing
      about what makes this product different. So common words are
      pushed towards zero.

      The result: the word "headphones" counts for a lot, the word
      "product" counts for almost nothing.

  COSINE SIMILARITY

      Now every product is an arrow pointing somewhere in a very
      high-dimensional space. Two products about similar things point
      in similar directions.

      Cosine similarity measures the ANGLE between two arrows, not the
      distance between their tips. That matters: a short description
      and a long one can still be "about the same thing", and cosine
      ignores length. The answer runs from 0 (nothing in common) to
      1 (identical wording).

WHY CONTENT-BASED, AND NOT COLLABORATIVE FILTERING?
    Collaborative filtering ("people who bought X also bought Y") needs
    a lot of purchase history before it is any good - it suffers from
    the "cold start" problem on a new shop. Content-based works from
    day one, because it only needs the product text.

    For a coursework project this is the honest choice, and it is the
    one described in the project handoff.

THE STAR RATING BLEND
    Pure text similarity has one weakness: it cannot tell that
    something is popular. Two nearly identical products score the
    same even if one has fifty 5-star reviews and the other has none.

    So the final score mixes both:

        final = 0.85 * text_similarity + 0.15 * rating_score

    The text similarity stays in charge - that is what "similar
    product" means. The rating nudges well-reviewed items up. The
    weights are a judgement call, not a law of nature; they are named
    constants below so they are easy to find and easy to defend.

WHY THE MODEL IS REBUILT, NOT SAVED
    The matrix is built fresh whenever the product list changes. Our
    catalogue is 30 products, so this takes a few milliseconds. For a
    large catalogue you would cache it, but caching would add a whole
    "when do I invalidate this?" problem for no benefit at this size.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# How much each ingredient contributes to the final score.
# These must add up to 1.0.
TEXT_WEIGHT = 0.85
RATING_WEIGHT = 0.15

# How many recommendations to return by default
DEFAULT_LIMIT = 4


def build_text(product):
    """Turn a product into the block of text we compare.

    This function is the heart of the whole thing. Whatever we put in
    here is all the model will ever know about a product.

    We join the name, category and description together. The name is
    repeated because it is the most informative part - "Wireless
    Headphones" says more than a whole sentence of filler - and
    repeating it makes the TF-IDF weighting treat it as important.

    Category is included with a prefix so that products in the same
    category share a word even when their descriptions do not.
    Category matching is a decent signal on its own.
    """
    name = product.name or ""
    category = product.category or ""
    description = product.description or ""

    return " ".join([
        name,
        name,
        f"category_{category.lower().replace(' ', '_')}",
        description,
    ])


def build_matrix(products):
    """Fit a TF-IDF model and return (matrix, ordered_product_ids).

    The matrix has one row per product and one column per word in the
    vocabulary. Most entries are 0 - a product only uses a small
    fraction of all the words - which is why this is called a SPARSE
    matrix.
    """
    if not products:
        return None, []

    texts = [build_text(product) for product in products]

    vectorizer = TfidfVectorizer(
        # Drop English filler words: "the", "and", "with"...
        stop_words="english",

        # Ignore terms that appear in fewer than 2 products. A word used
        # by one product alone cannot link it to anything.
        min_df=2,

        # Words are already lowercase in our data, but this is safer
        lowercase=True,

        # Also compare pairs of neighbouring words, so "wireless
        # headphones" is a feature in its own right, not just
        # "wireless" and "headphones" separately. Two-word phrases are
        # often the most descriptive thing in a short product name.
        ngram_range=(1, 2),

        # The standard TF-IDF settings
        sublinear_tf=True,
    )

    matrix = vectorizer.fit_transform(texts)

    return matrix, [product.id for product in products]


def rating_score(product):
    """Turn a product's star rating into a number from 0 to 1.

    A product with no reviews scores 0.5 - neutral. Not punished for
    being new, not rewarded for being unknown.

    A 1-star product scores 0.0 and a 5-star product scores 1.0.
    """
    average = getattr(product, "rating_average", None)

    if not average:
        return 0.5

    return max(0.0, min(1.0, (float(average) - 1.0) / 4.0))


def similar_products(target, candidates, limit=DEFAULT_LIMIT):
    """Find products similar to `target`.

    `target` is a Product, `candidates` is the full list of Products.

    Returns a list of (product, score) sorted best first, excluding the
    target itself.

    Each product needs a `rating_average` attribute for the blend. The
    caller attaches it before calling - see the route in app.py.
    """
    if not candidates or len(candidates) < 2:
        return []

    # Keep the target in the list so the matrix rows line up
    working = [target] + [
        product for product in candidates if product.id != target.id
    ]

    matrix, product_ids = build_matrix(working)

    if matrix is None or matrix.shape[0] < 2:
        return []

    # Row 0 is the target (we put it first above)
    positions = {product_id: index for index, product_id in enumerate(product_ids)}

    target_index = positions.get(target.id)

    if target_index is None:
        return []

    # Compare the target's row against every row.
    # This is one row times the whole matrix, so the result is a flat
    # array of similarities, one per product.
    similarities = cosine_similarity(
        matrix[target_index], matrix
    ).flatten()

    by_id = {product.id: product for product in working}

    # Work out the rating range so we can normalise it. Without this,
    # the rating term would dominate simply because 5 is a bigger
    # number than a similarity of 0.3.
    ratings = [rating_score(by_id[pid]) for pid in product_ids]
    lowest, highest = min(ratings), max(ratings)
    span = highest - lowest

    scored = []

    for product_id, similarity in zip(product_ids, similarities):
        if product_id == target.id:
            continue

        product = by_id.get(product_id)

        if product is None:
            continue

        # Scale this product's rating into 0..1 across the candidate set
        raw_rating = rating_score(product)
        normalised_rating = (
            (raw_rating - lowest) / span if span > 0 else 0.5
        )

        score = (TEXT_WEIGHT * float(similarity)) + (
            RATING_WEIGHT * normalised_rating
        )

        scored.append((product, round(score, 4), round(float(similarity), 4)))

    # Highest score first. Ties broken by id so the order is stable and
    # the same request twice gives the same answer.
    scored.sort(key=lambda row: (-row[1], row[0].id))

    return scored[:limit]


def recommend_from_history(purchased, candidates, limit=DEFAULT_LIMIT):
    """Personalised recommendations based on what a user has bought.

    THE IDEA
        A shopper buys a kettle and a toaster. We build a "taste
        profile" by adding together the TF-IDF rows of everything they
        bought, then find the products closest to that combined arrow.

        This is why it is worth using TF-IDF rows rather than plain
        word counting: the rows are already weighted so that
        distinctive words matter more, so the profile is automatically
        about what makes those products distinctive.

    `purchased` is a list of Products the user has ordered.
    `candidates` is everything available to recommend.
    """
    if not purchased or not candidates:
        return []

    purchased_ids = {product.id for product in purchased}

    # Only recommend things they have not already bought
    pool = [
        product for product in candidates
        if product.id not in purchased_ids
    ]

    if not pool:
        return []

    # Build one matrix covering both, so the words line up
    working = list(purchased) + list(pool)

    matrix, product_ids = build_matrix(working)

    if matrix is None:
        return []

    positions = {product_id: index for index, product_id in enumerate(product_ids)}

    purchased_rows = [
        positions[product.id] for product in purchased
        if product.id in positions
    ]

    if not purchased_rows:
        return []

    # The taste profile is the average of what they bought.
    # mean() over axis 0 collapses the chosen rows into a single row.
    profile = matrix[purchased_rows].mean(axis=0)

    # numpy gives back a matrix; make it a plain 2D row for sklearn
    profile = np.asarray(profile)

    similarities = cosine_similarity(profile, matrix).flatten()

    by_id = {product.id: product for product in working}

    ratings = [rating_score(by_id[pid]) for pid in product_ids]
    lowest, highest = min(ratings), max(ratings)
    span = highest - lowest

    scored = []

    for product in pool:
        index = positions.get(product.id)

        if index is None:
            continue

        similarity = float(similarities[index])

        raw_rating = rating_score(product)
        normalised_rating = (
            (raw_rating - lowest) / span if span > 0 else 0.5
        )

        score = (TEXT_WEIGHT * similarity) + (RATING_WEIGHT * normalised_rating)

        scored.append((product, round(score, 4), round(similarity, 4)))

    scored.sort(key=lambda row: (-row[1], row[0].id))

    return scored[:limit]


def popular_products(candidates, limit=DEFAULT_LIMIT):
    """The fallback: highest rated first, then anything unreviewed.

    Used for a brand new visitor who has no order history, and for a
    brand new product that shares no words with anything.

    Better than showing nothing: a cold-start fallback is the
    difference between an empty section and a useful one.
    """
    if not candidates:
        return []

    def sort_key(product):
        average = getattr(product, "rating_average", 0) or 0
        count = getattr(product, "rating_count", 0) or 0

        # Negatives so that higher ratings sort first.
        # Reviews with more votes win ties, which avoids one lucky
        # 5-star review outranking something with fifty reviews.
        return (-float(average), -int(count), product.id)

    ordered = sorted(candidates, key=sort_key)

    return [(product, 0.0, 0.0) for product in ordered[:limit]]
