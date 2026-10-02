const revealSelectors = [
  "[data-motion]",
  ".page-heading",
  ".toolbar",
  ".page > .panel",
  ".stats-grid > .stat-card",
  ".dashboard-grid > .panel",
  ".report-grid > .report-card",
  ".login-brand",
  ".login-form",
];

const parallaxSelectors = ["[data-parallax]", ".page-heading", ".login-brand"];
const animationNames = {
  fade: "fadeIn",
  "fade-up": "fadeInUp",
  "fade-down": "fadeInDown",
  "fade-left": "fadeInLeft",
  "fade-right": "fadeInRight",
};

function prefersReducedMotion() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

function motionName(element) {
  return animationNames[element.dataset.motion] || "fadeInUp";
}

function markReveal(element, index = 0) {
  if (element.dataset.motionReady === "true") return;

  element.dataset.motionReady = "true";
  element.classList.add("motion-reveal", "motion-pending");
  element.style.setProperty("--animate-delay", `${Math.min(index * 70, 280)}ms`);
}

function reveal(element, observer) {
  element.classList.remove("motion-pending");
  element.classList.add("motion-visible");

  if (prefersReducedMotion()) {
    observer?.unobserve(element);
    return;
  }

  element.classList.add("animate__animated", `animate__${motionName(element)}`);
  observer?.unobserve(element);
}

function collect(root, selectors) {
  const elements = [];
  if (root instanceof Element && selectors.some((selector) => root.matches(selector))) elements.push(root);
  selectors.forEach((selector) => elements.push(...root.querySelectorAll(selector)));
  return [...new Set(elements)];
}

function initMotion() {
  if (window.__serviceflowMotionInitialized) return;
  window.__serviceflowMotionInitialized = true;

  const revealObserver = "IntersectionObserver" in window
    ? new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) reveal(entry.target, revealObserver);
        });
      }, { threshold: .12, rootMargin: "0px 0px -8% 0px" })
    : null;

  const parallaxElements = new Set();
  const register = (root = document) => {
    const revealElements = collect(root, revealSelectors);
    revealElements.forEach((element, index) => {
      markReveal(element, index);
      if (revealObserver) revealObserver.observe(element);
      else reveal(element);
    });

    collect(root, parallaxSelectors).forEach((element) => {
      if (!element.dataset.parallax) element.dataset.parallax = element.classList.contains("login-brand") ? ".24" : ".12";
      element.classList.add("motion-parallax");
      parallaxElements.add(element);
    });
  };

  register();

  if (prefersReducedMotion()) {
    document.querySelectorAll(".motion-pending").forEach((element) => reveal(element));
  }

  let frame = 0;
  const updateParallax = () => {
    frame = 0;
    if (prefersReducedMotion()) return;

    const viewportCenter = window.innerHeight / 2;
    parallaxElements.forEach((element) => {
      if (!element.isConnected) {
        parallaxElements.delete(element);
        return;
      }

      const rect = element.getBoundingClientRect();
      const speed = Number(element.dataset.parallax) || .12;
      const distance = viewportCenter - (rect.top + rect.height / 2);
      const offset = Math.max(-18, Math.min(18, distance * speed * .12));
      element.style.setProperty("--motion-parallax-y", `${offset.toFixed(2)}px`);
      element.style.setProperty("--motion-parallax-decoration-y", `${(-offset * 1.35).toFixed(2)}px`);
    });
  };

  const requestParallaxUpdate = () => {
    if (!frame) frame = window.requestAnimationFrame(updateParallax);
  };

  window.addEventListener("scroll", requestParallaxUpdate, { passive: true });
  window.addEventListener("resize", requestParallaxUpdate, { passive: true });
  requestParallaxUpdate();

  const mutationObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) register(node);
    }));
    requestParallaxUpdate();
  });
  mutationObserver.observe(document.body, { childList: true, subtree: true });
}

export { initMotion };
