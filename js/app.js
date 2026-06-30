/* Homepage finder. The brand cards are pre-rendered into #grid at build time
   (build.py + templates/macros.html.j2). This script only filters and expands
   them -- no client-side rendering, no cars.json fetch. Each card carries a
   data-search attribute (lowercased name + aliases) used for matching. */

const grid = document.getElementById("grid");
const meta = document.getElementById("meta");
const noresults = document.getElementById("noresults");
const nrq = document.getElementById("nrq");
const input = document.getElementById("search");
const clearBtn = document.getElementById("clear");

const cards = Array.from(grid.querySelectorAll(".card"));

function matches(card, q) {
  if (!q) return true;
  const hay = card.dataset.search || "";
  return q.split(/\s+/).every(term => hay.includes(term));
}

function setOpen(card, open) {
  card.classList.toggle("open", open);
  card.querySelector(".card-head").setAttribute("aria-expanded", open ? "true" : "false");
}

function render(q = "") {
  q = q.trim().toLowerCase();
  let visible = 0;
  let lastVisible = null;
  cards.forEach(card => {
    const show = matches(card, q);
    card.hidden = !show;
    setOpen(card, false);          // collapse on every filter, as the old render did
    if (show) { visible++; lastVisible = card; }
  });

  if (visible === 0) {
    meta.textContent = "";
    nrq.textContent = q;
    noresults.hidden = false;
    return;
  }
  noresults.hidden = true;

  if (q) {
    meta.textContent = `${visible} match${visible === 1 ? "" : "es"} for "${q}"`;
    if (visible === 1) setOpen(lastVisible, true);   // single match: open it
  } else {
    meta.textContent = "Showing all car brands.";
  }
}

grid.addEventListener("click", (e) => {
  const head = e.target.closest(".card-head");
  if (!head) return;
  const card = head.closest(".card");
  setOpen(card, !card.classList.contains("open"));
});

let debounce;
input.addEventListener("input", () => {
  clearBtn.style.display = input.value ? "flex" : "none";
  clearTimeout(debounce);
  debounce = setTimeout(() => render(input.value), 120);
});

clearBtn.addEventListener("click", () => {
  input.value = "";
  clearBtn.style.display = "none";
  render("");
  input.focus();
});

render("");

/* ---------- Contribute form (Formspree, native fetch) ---------- */
const cform = document.getElementById("contribute-form");
if (cform) {
  const status = document.getElementById("cf-status");
  const submitBtn = cform.querySelector("button[type=submit]");
  const GH = 'You can also <a href="https://github.com/willsheppard/prevent-keyless-car-theft" target="_blank" rel="noopener">add it on GitHub</a>.';

  cform.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.className = "form-status";
    status.textContent = "Sending…";
    submitBtn.disabled = true;

    try {
      const res = await fetch(cform.action, {
        method: "POST",
        body: new FormData(cform),
        headers: { Accept: "application/json" }
      });
      if (res.ok) {
        cform.reset();
        status.className = "form-status ok";
        status.textContent = "Thanks! We've got it and will review it before it goes live.";
      } else {
        const data = await res.json().catch(() => ({}));
        const msg = data.errors ? data.errors.map(er => er.message).join(", ") : "Something went wrong.";
        status.className = "form-status err";
        status.innerHTML = `${msg} ${GH}`;
      }
    } catch {
      status.className = "form-status err";
      status.innerHTML = `Network error. Please try again. ${GH}`;
    } finally {
      submitBtn.disabled = false;
    }
  });
}
