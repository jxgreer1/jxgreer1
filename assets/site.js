/* Shared behaviour for the top-level pages. Every block checks for its own
   elements, so each page only gets what it has markup for. */
(function(){
  "use strict";

  /* Jan to Mar and Jul to Sep are Tesla terms in the Bay Area; the other six
     months are class at Kettering in Flint. Reads the month on every load. */
  var city = document.getElementById("city");
  if (city){
    var m = new Date().getMonth() + 1;
    city.textContent = ((m>=1&&m<=3)||(m>=7&&m<=9)) ? "Palo Alto" : "Flint";
  }

  /* nav picks up a ground once you leave the top */
  var nav = document.querySelector(".nav");
  function onScroll(){ nav.classList.toggle("scrolled", window.scrollY > 8); }
  if (nav){ onScroll(); window.addEventListener("scroll", onScroll, { passive: true }); }

  var POSTS = window.POSTS || [];

  /* Feed posts carry a shortcode; photos from a data export do not, so the
     link is only offered when there is somewhere to go. */
  function url(p){
    if (p.u) return p.u;
    var c = p.p || "";
    return (c && c.charAt(0) !== "x") ? "https://www.instagram.com/p/" + c + "/" : "";
  }
  function src(p){ return "ig/" + p.f; }

  function shot(p, i){
    var fig = document.createElement("figure");
    fig.className = "shot";
    var btn = document.createElement("button");
    btn.type = "button"; btn.className = "plate";
    btn.setAttribute("aria-label", "Enlarge: " + p.t);
    var im = new Image();
    im.src = src(p); im.alt = p.t; im.width = p.w; im.height = p.h;
    im.loading = i < 3 ? "eager" : "lazy"; im.decoding = "async";
    btn.appendChild(im);
    btn.addEventListener("click", function(){ show(POSTS.indexOf(p)); });
    fig.appendChild(btn);
    return fig;
  }

  /* home: newest post sits centered under the name */
  var lat = document.getElementById("latest");
  if (lat && POSTS.length){
    var top0 = shot(POSTS[0], 0), cap = document.createElement("figcaption");
    cap.innerHTML = '<span class="tag">Latest</span><span class="t"></span> &middot; ' + POSTS[0].d +
      ' &middot; <a href="photographs.html">More photographs &rsaquo;</a>';
    cap.querySelector(".t").textContent = POSTS[0].t;
    top0.appendChild(cap);
    lat.appendChild(top0);
  }

  /* photographs: alternating one-up and two-up, Apple-ish rhythm */
  var g = document.getElementById("gallery");
  if (g){
    var rest = POSTS.slice(1), n = 0, k = 0;
    while (n < rest.length){
      if (k % 3 === 0){
        g.appendChild(shot(rest[n], n)); n += 1;
      } else {
        var row = document.createElement("div");
        row.className = "grow";
        row.appendChild(shot(rest[n], n));
        if (rest[n+1]) row.appendChild(shot(rest[n+1], n+1));
        g.appendChild(row); n += 2;
      }
      k += 1;
    }
  }

  /* ---- lightbox ---- */
  var box = document.getElementById("box"), at = 0, bimg, bcap;
  function show(i){
    if (!box) return;
    at = (i + POSTS.length) % POSTS.length;
    var p = POSTS[at];
    bimg.src = src(p); bimg.alt = p.t;
    var href = url(p);
    bcap.innerHTML = '<span class="t"></span> &middot; ' + p.d +
      (href ? ' &middot; <a href="' + href + '" target="_blank" rel="noopener">View on Instagram</a>' : "");
    bcap.querySelector(".t").textContent = p.t;
    if (!box.open){ box.showModal ? box.showModal() : box.setAttribute("open",""); }
  }
  if (box){
    bimg = document.getElementById("boximg");
    bcap = document.getElementById("boxcap");
    var hide = function(){ box.close ? box.close() : box.removeAttribute("open"); };
    document.getElementById("boxx").addEventListener("click", hide);
    box.addEventListener("click", function(e){ if (e.target === box) hide(); });
    box.addEventListener("keydown", function(e){
      if (e.key === "ArrowRight"){ show(at+1); e.preventDefault(); }
      if (e.key === "ArrowLeft"){ show(at-1); e.preventDefault(); }
    });
  }

  /* ---- scroll reveal, below the fold only, with a hard safety net ---- */
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!still && "IntersectionObserver" in window){
    /* each block reveals on its own, so a section cascades rather than
       arriving in one slab */
    var sel = ".band .inner > h1, .band .inner > h2, .band .inner > .sub, .band .inner > .prose," +
              ".band .inner > .intro, .band .inner > .cv, .band .inner > .tools," +
              ".band .inner > .resume, .band .inner > .projects," +
              ".band .inner > .cta, .band .inner > .stats, .gallery .shot";
    var targets = [];
    Array.prototype.forEach.call(document.querySelectorAll(sel), function(el){
      if (el.getBoundingClientRect().top > window.innerHeight){
        el.classList.add("rise");
        targets.push(el);
      }
    });
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if (e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    targets.forEach(function(el){ io.observe(el); });
    /* nothing stays hidden, whatever happens */
    setTimeout(function(){ targets.forEach(function(el){ el.classList.add("in"); }); }, 2500);
  }

  /* ---- contact: copy email ---- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-copy]"), function(b){
    b.addEventListener("click", function(){
      var text = b.getAttribute("data-copy");
      function ok(){
        b.textContent = "Copied"; b.classList.add("done");
        setTimeout(function(){ b.textContent = "Copy"; b.classList.remove("done"); }, 1800);
      }
      if (navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(ok, function(){ window.location.href = "mailto:" + text; });
      } else {
        window.location.href = "mailto:" + text;
      }
    });
  });

  /* ---- big numbers count up the first time they're seen ----
     The real value is in the HTML, so without JS (or with reduced motion)
     it simply shows the final number. */
  var nums = document.querySelectorAll("[data-count]");
  if (nums.length && !still && "IntersectionObserver" in window && window.requestAnimationFrame){
    var fmt = function(el, v){ return (el.getAttribute("data-pre") || "") + v + (el.getAttribute("data-suf") || ""); };
    var count = function(el, delay){
      var end = Number(el.getAttribute("data-count")), dur = 1500, t0 = null;
      setTimeout(function(){
        requestAnimationFrame(function step(t){
          if (t0 === null) t0 = t;
          var p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
          el.textContent = fmt(el, Math.round(end * e));
          if (p < 1) requestAnimationFrame(step);
        });
      }, delay);
    };
    Array.prototype.forEach.call(nums, function(el){ el.textContent = fmt(el, 0); });
    var cio = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if (!e.isIntersecting) return;
        var i = Array.prototype.indexOf.call(nums, e.target);
        count(e.target, (i % 4) * 110);
        cio.unobserve(e.target);
      });
    }, { threshold: 0.6 });
    Array.prototype.forEach.call(nums, function(el){ cio.observe(el); });
  }
})();
