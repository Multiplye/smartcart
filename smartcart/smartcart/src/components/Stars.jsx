// =========================
// Stars
// =========================
//
// Draws a star rating. Used in three places:
//
//   <Stars value={4.5} />            read-only, half stars allowed
//   <Stars value={3} interactive onSelect={setRating} />   clickable
//
// A note on the "half star": we render five star shapes as a
// background, then overlay a clipped copy filled to the right
// percentage. So 4.5 fills 90% of the row. That is simpler and more
// accurate than trying to draw a half-star glyph.

function Stars({
  value = 0,
  interactive = false,
  onSelect = null,
  size = "md",
}) {
  // How far across the five stars the fill should reach, 0 to 100%
  const percentage = Math.max(0, Math.min(5, value)) * 20;

  const starPath =
    "M12 2.6l2.72 5.52 6.09.89-4.41 4.29 1.04 6.07L12 16.5l-5.44 2.87 " +
    "1.04-6.07-4.41-4.29 6.09-.89L12 2.6z";

  const row = (fillColour, className) => (
    <div className={className}>
      {[1, 2, 3, 4, 5].map((index) => (
        <svg
          key={index}
          viewBox="0 0 24 24"
          width="18"
          height="18"
          aria-hidden="true"
        >
          <path d={starPath} fill={fillColour} />
        </svg>
      ))}
    </div>
  );

  // ---------- Read-only ----------
  if (!interactive) {
    return (
      <span
        className={`stars stars-${size}`}
        title={value > 0 ? `${value} out of 5` : "No ratings yet"}
      >
        {row("#e2e8f0", "stars-layer")}

        <span
          className="stars-fill-clip"
          style={{ width: `${percentage}%` }}
        >
          {row("#f59e0b", "stars-layer")}
        </span>
      </span>
    );
  }

  // ---------- Clickable ----------
  return (
    <span className={`stars stars-${size} stars-clickable`} role="radiogroup">
      {[1, 2, 3, 4, 5].map((index) => (
        <button
          key={index}
          type="button"
          className="star-button"
          role="radio"
          aria-checked={value === index}
          aria-label={`${index} star${index === 1 ? "" : "s"}`}
          onClick={() => onSelect && onSelect(index)}
        >
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
            <path
              d={starPath}
              fill={index <= value ? "#f59e0b" : "#e2e8f0"}
            />
          </svg>
        </button>
      ))}
    </span>
  );
}

export default Stars;
