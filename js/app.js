const TYPE_LABEL = { temp: "Temporary", auto: "Automatic", perm: "Permanent", info: "Note" };

const grid = document.getElementById("grid");
const meta = document.getElementById("meta");
const noresults = document.getElementById("noresults");
const nrq = document.getElementById("nrq");
const input = document.getElementById("search");
const clearBtn = document.getElementById("clear");

function initials(name) {
  const clean = name.replace(/[^A-Za-zÀ-ž ]/g, "").trim();
  const parts = clean.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return clean.slice(0, 2).toUpperCase();
}

function tagsFor(car) {
  if (car.unknown) return '<span class="tag none">Help needed</span>';
  const types = [...new Set(car.instructions.map(instruction => instruction.type))];
  return types.map(type => `<span class="tag ${type}">${TYPE_LABEL[type]}</span>`).join("");
}

function listHTML(steps, ordered = true) {
  const tag = ordered ? "ol" : "ul";
  return `<${tag}>${steps.map(step => `<li>${step}</li>`).join("")}</${tag}>`;
}

// instructionHTML(instruction): renders one way to disable keyless entry: a tagged
// block with optional intro text, an ordered/unordered step list, labelled
// sub-procedures, and notes. Mirrors render_instruction() in templates/macros.html.j2.
function instructionHTML(instruction) {
  let html = `<div class="instruction"><div class="instruction-head">`;
  html += `<span class="tag ${instruction.type}">${TYPE_LABEL[instruction.type]}</span>`;
  if (instruction.unverified) html += `<span class="tag unverified">Unverified</span>`;
  if (instruction.models) html += `<span class="instruction-models">${instruction.models}</span>`;
  html += `</div>`;
  if (instruction.text) html += `<p>${instruction.text}</p>`;
  // Numbered when order matters: permanent changes, or more than two steps.
  if (instruction.steps) html += listHTML(instruction.steps, instruction.type === "perm" || instruction.steps.length > 2);
  if (instruction.sub) {
    instruction.sub.forEach(sub => {
      html += `<p><strong>${sub.label}:</strong></p>` + listHTML(sub.steps);
    });
  }
  if (instruction.notes) instruction.notes.forEach(note => { html += `<p class="note">${note}</p>`; });
  html += `</div>`;
  return html;
}

function bodyHTML(car) {
  if (car.unknown) {
    return `<div class="card-body"><p class="unknown-body">We don't yet have confirmed instructions for ${car.name}. Many ${car.name} models do support disabling keyless entry -- check your owner's manual under "keyless" or "passive entry".<br><a class="contribute-link" href="#contribute">Know how? Help us add ${car.name} →</a></p></div>`;
  }
  return `<div class="card-body">${car.instructions.map(instructionHTML).join("") + (car.info || []).map(note => `<p class="note">${note}</p>`).join("")}</div>`;
}

function cardHTML(car, idx) {
  return `<div class="card" data-idx="${idx}">
    <button class="card-head" aria-expanded="false" aria-controls="body-${idx}">
      <span class="brand-logo" aria-hidden="true">${initials(car.name)}</span>
      <span class="brand-meta">
        <span class="brand-name">${car.name}</span>
        <span class="brand-tags">${tagsFor(car)}</span>
      </span>
      <svg class="chev" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"></polyline></svg>
    </button>
    ${bodyHTML(car).replace('class="card-body"', `class="card-body" id="body-${idx}"`)}
  </div>`;
}

function matches(car, q) {
  if (!q) return true;
  const hay = (car.name + " " + (car.aliases || []).join(" ")).toLowerCase();
  return q.split(/\s+/).every(term => hay.includes(term));
}

function render(cars, q = "") {
  q = q.trim().toLowerCase();
  const sorted = [...cars].sort((a, b) => a.name.localeCompare(b.name));
  const visible = sorted.filter(c => matches(c, q));

  if (visible.length === 0) {
    grid.innerHTML = "";
    meta.textContent = "";
    nrq.textContent = q;
    noresults.hidden = false;
    return;
  }
  noresults.hidden = true;
  grid.innerHTML = visible.map((c) => cardHTML(c, cars.indexOf(c))).join("");

  if (q) {
    meta.textContent = `${visible.length} match${visible.length === 1 ? "" : "es"} for "${q}"`;
    if (visible.length === 1) {
      const only = grid.querySelector(".card");
      openCard(only);
    }
  } else {
    meta.textContent = `Showing all ${visible.length} car makes. Tap yours, or search above.`;
  }
}

function openCard(card) {
  card.classList.add("open");
  card.querySelector(".card-head").setAttribute("aria-expanded", "true");
}

grid.addEventListener("click", (e) => {
  const head = e.target.closest(".card-head");
  if (!head) return;
  const card = head.closest(".card");
  const isOpen = card.classList.toggle("open");
  head.setAttribute("aria-expanded", isOpen ? "true" : "false");
});

fetch("data/cars.json")
  .then(r => r.json())
  .then(cars => {
    let t;
    input.addEventListener("input", () => {
      clearBtn.style.display = input.value ? "flex" : "none";
      clearTimeout(t);
      t = setTimeout(() => render(cars, input.value), 120);
    });

    clearBtn.addEventListener("click", () => {
      input.value = "";
      clearBtn.style.display = "none";
      render(cars, "");
      input.focus();
    });

    render(cars, "");
  });

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
