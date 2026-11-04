/* Shared behaviour for the pages under projects/: sub-nav highlighting,
   swipe-row arrows, and videos that only play while on screen. */
(function(){
  "use strict";
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var hasIO = "IntersectionObserver" in window;

  /* ---- sub-nav: underline the section you're reading ---- */
  var box = document.querySelector(".subnav-links");
  var links = box ? Array.prototype.slice.call(box.querySelectorAll('a[href^="#"]')) : [];
  function mark(id){
    links.forEach(function(a){
      var on = a.getAttribute("href") === "#" + id;
      a.classList.toggle("on", on);
      if (on){
        a.setAttribute("aria-current", "true");
        if (box.scrollWidth > box.clientWidth){
          box.scrollTo({ left: a.offsetLeft - box.offsetLeft - 24, behavior: still ? "auto" : "smooth" });
        }
      } else {
        a.removeAttribute("aria-current");
      }
    });
  }
  if (links.length && hasIO){
    var spy = new IntersectionObserver(function(es){
      es.forEach(function(e){ if (e.isIntersecting) mark(e.target.id); });
    }, { rootMargin: "-35% 0px -60% 0px" });
    links.forEach(function(a){
      var el = document.getElementById(a.getAttribute("href").slice(1));
      if (el) spy.observe(el);
    });
  }

  /* ---- swipe rows ---- */
  Array.prototype.forEach.call(document.querySelectorAll(".rail"), function(rail){
    var track = rail.querySelector(".rail-track"),
        nav = rail.querySelector(".rail-nav");
    if (!track || !nav) return;
    var prev = nav.querySelector("[data-dir='-1']"),
        next = nav.querySelector("[data-dir='1']");
    function update(){
      var max = track.scrollWidth - track.clientWidth;
      nav.hidden = max <= 2;
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft >= max - 2;
    }
    [prev, next].forEach(function(b){
      b.addEventListener("click", function(){
        var step = Math.max(track.clientWidth * 0.75, 280) * Number(b.getAttribute("data-dir"));
        track.scrollBy({ left: step, behavior: still ? "auto" : "smooth" });
      });
    });
    track.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    window.addEventListener("load", update);
    update();
  });

  /* ---- videos play only while on screen ---- */
  var vids = document.querySelectorAll("video[data-autoplay]");
  if (vids.length && hasIO && !still){
    var vio = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if (e.isIntersecting){ var p = e.target.play(); if (p && p.catch) p.catch(function(){}); }
        else e.target.pause();
      });
    }, { threshold: 0.35 });
    Array.prototype.forEach.call(vids, function(v){ vio.observe(v); });
  }
})();
