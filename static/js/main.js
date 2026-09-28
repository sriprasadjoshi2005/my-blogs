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
