// Background slideshow: cross-fades through the pictures in static/backgrounds/.
(function () {
  var bg = document.querySelector(".bg[data-rotate]");
  if (!bg) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var slides = bg.querySelectorAll(".bg-slide");
  if (slides.length < 2) return;

  var current = 0;
  setInterval(function () {
    slides[current].classList.remove("is-active");
    current = (current + 1) % slides.length;
    slides[current].classList.add("is-active");
  }, 12000); // change picture every 12 seconds
})();

// Comment and contact boxes grow taller as you type (no drag handle needed).
(function () {
  var boxes = document.querySelectorAll(".field textarea");

  function grow(box) {
    box.style.height = "auto";
    box.style.height = box.scrollHeight + 2 + "px"; // +2 covers the border
  }

  boxes.forEach(function (box) {
    box.style.overflow = "hidden"; // set here so the box still scrolls if JS fails
    grow(box);
    box.addEventListener("input", function () { grow(box); });
  });

  // Text wraps differently when the window size changes, so re-measure.
  window.addEventListener("resize", function () { boxes.forEach(grow); });
})();
