/* -------------------- SAFE EVENT DELEGATION -------------------- */
document.addEventListener("click", function (e) {
  const buyBtn = e.target.closest(".buy-btn");
  const reserveBtn = e.target.closest(".reserve-btn");

  if (buyBtn) {
    openKittenForm("buy", buyBtn.dataset.kit, buyBtn.dataset.name, buyBtn.dataset.price);
  }

  if (reserveBtn) {
    openKittenForm("reserve", reserveBtn.dataset.kit, reserveBtn.dataset.name, reserveBtn.dataset.price);
  }
});

/* -------------------- FORM LOGIC -------------------- */
function openKittenForm(type, kittenId, kittenName, kittenPrice) {
  const container = document.getElementById("kittenForm");
  if (!container) return;

  const priceValue = Number(kittenPrice) || 0;
  const reservationDeposit = window.RESERVATION_DEPOSIT || 300;
  const depositAmount = Math.min(priceValue, reservationDeposit);
  const balanceDue = Math.max(0, priceValue - depositAmount);
  const money = value => value.toLocaleString("en-US", { style: "currency", currency: "USD" });

  const reserveSummary = type === "reserve"
    ? `
      <div class="reservation-summary">
        <div>
          <span>Reservation Amount</span>
          <strong>${money(depositAmount)}</strong>
        </div>
        <div>
          <span>Balance Due</span>
          <strong>${money(balanceDue)}</strong>
        </div>
      </div>
      <input type="hidden" name="deposit_amount" value="${depositAmount}">
      <input type="hidden" name="balance_due" value="${balanceDue}">
    `
    : "";

  container.innerHTML = `
    <div class="form-inner">
      <h2>${type === "buy" ? "Buy" : "Reserve"} ${kittenName || ""}</h2>
      <p class="warning-text">Price: $${kittenPrice || ""}</p>

      <p class="warning-text">⚠️ We do not deliver or release any kittens until full payment is completed.</p>

      <input type="hidden" name="kitten_id" value="${kittenId || ""}">
      <input type="hidden" name="inquiry_type" value="${type}">
      <input type="hidden" name="payment_method" id="paymentMethodField" value="">

      <label>Kitten</label>
      <input type="text" value="${kittenName || ""}" readonly>

      ${reserveSummary}

      <label>Full Name</label>
      <input type="text" name="name" placeholder="Enter your full name" required>

      <label>Email Address</label>
      <input type="email" name="email" placeholder="Enter your email" required>

      <label>Phone Number</label>
      <input type="tel" name="phone" placeholder="Enter your phone number" required>

      <label>Pickup or Delivery</label>
      <select id="deliveryType" name="delivery_type">
        <option value="pickup">Pickup</option>
        <option value="delivery">Delivery</option>
        <option value="airport">Airport Pickup</option>
      </select>

      <div id="addressField" style="display:none;">
        <label>Delivery Address</label>
        <input type="text" name="address" placeholder="Enter full address">
      </div>

      <label>Payment Method (select all that apply)</label>
      <div class="payments">
        <div class="pay-option">Apple Pay</div>
        <div class="pay-option">Zelle</div>
        <div class="pay-option">CashApp</div>
        <div class="pay-option">Venmo</div>
        <div class="pay-option">Chime</div>
      </div>

      <label>Message</label>
      <textarea name="message" placeholder="Tell us about your home and preferred timing."></textarea>

      <button type="submit" class="submit-btn">Submit</button>
    </div>
  `;

  const form = document.getElementById("kittenForm");
  form.setAttribute("action", "/inquiry");
  form.setAttribute("method", "POST");

  document.getElementById("kitten-form-section").scrollIntoView({ behavior: "smooth" });

  // Delivery toggle
  const deliverySelect = document.getElementById("deliveryType");
  const addressField = document.getElementById("addressField");
  deliverySelect.addEventListener("change", () => {
    addressField.style.display =
      deliverySelect.value === "delivery" ? "block" : "none";
  });

  // Payment selection
  document.querySelectorAll(".pay-option").forEach(option => {
    option.addEventListener("click", () => {
      option.classList.toggle("active");
      const selected = Array.from(document.querySelectorAll(".pay-option.active"))
        .map(el => el.textContent.trim());
      const paymentField = document.getElementById("paymentMethodField");
      if (paymentField) paymentField.value = selected.join(", ");
    });
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const formData = new FormData(form);
    const response = await fetch("/inquiry", {
      method: "POST",
      body: formData
    });
    if (response.ok) {
      form.innerHTML = `
        <div class="form-inner">
          <h2>Thank you!</h2>
          <p>We received your request and will be in touch shortly.</p>
        </div>
      `;
    } else {
      const data = await response.json().catch(() => ({}));
      alert(data.error || "Something went wrong. Please try again.");
    }
  });
}

/* -------------------- TESTIMONIALS STAGGERED BOUNCE -------------------- */
const testimonialTrack = document.querySelector(".testimonial-track");
if (testimonialTrack) {
  const originalCards = Array.from(
    testimonialTrack.querySelectorAll(".testimonial-card")
  );
  const data = originalCards.map(card => ({
    img: card.querySelector("img")?.getAttribute("src") || "",
    quote: card.querySelector("p")?.textContent || "",
    author: card.querySelector("span")?.textContent || ""
  }));

  if (data.length >= 3) {
    testimonialTrack.innerHTML = "";

    const buildCard = item => {
      const card = document.createElement("div");
      card.className = "testimonial-card";
      card.innerHTML = `
        <img src="${item.img}" alt="Testimonial photo">
        <p>${item.quote}</p>
        <span>${item.author}</span>
      `;
      return card;
    };

    const slots = [];
    [0, 1, 2].forEach(idx => {
      const card = buildCard(data[idx]);
      testimonialTrack.appendChild(card);
      slots.push({ el: card, idx });
    });

    let nextIndex = 3;
    const rotateSlot = slot => {
      const current = new Set(slots.map(s => s.idx));
      let idx = nextIndex % data.length;
      nextIndex += 1;
      let guard = 0;
      while (current.has(idx) && guard < data.length) {
        idx = nextIndex % data.length;
        nextIndex += 1;
        guard += 1;
      }

      slot.idx = idx;
      const item = data[idx];
      const img = slot.el.querySelector("img");
      const p = slot.el.querySelector("p");
      const span = slot.el.querySelector("span");
      if (img) img.src = item.img;
      if (p) p.textContent = item.quote;
      if (span) span.textContent = item.author;

      slot.el.classList.remove("fade-in");
      void slot.el.offsetWidth;
      slot.el.classList.add("fade-in");
    };

    let slotCursor = 0;
    setInterval(() => {
      rotateSlot(slots[slotCursor]);
      slotCursor = (slotCursor + 1) % slots.length;
    }, 4000);
  }
}

/* -------------------- NAVBAR SCROLL EFFECT -------------------- */
const navbar = document.querySelector(".navbar");
if (navbar) {
  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  });
}

/* -------------------- MOBILE NAV TOGGLE -------------------- */
const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");
if (menuToggle && navLinks) {
  const toggleMenu = () => {
    navLinks.classList.toggle("open");
    menuToggle.setAttribute(
      "aria-expanded",
      navLinks.classList.contains("open")
    );
  };

  menuToggle.addEventListener("click", toggleMenu);
  menuToggle.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleMenu();
    }
  });

  navLinks.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("open");
      menuToggle.setAttribute("aria-expanded", "false");
    });
  });
}

/* -------------------- INFO DROPDOWN TOGGLE -------------------- */
const dropdownLinks = document.querySelectorAll(".nav-dropdown > a");
if (dropdownLinks.length) {
  dropdownLinks.forEach(link => {
    link.addEventListener("click", e => {
      const parent = link.parentElement;
      const menu = parent?.querySelector(".dropdown-menu");
      if (menu) {
        e.preventDefault();
        parent.classList.toggle("open");
      }
    });
  });

  document.addEventListener("click", e => {
    if (!e.target.closest(".nav-dropdown")) {
      document
        .querySelectorAll(".nav-dropdown.open")
        .forEach(el => el.classList.remove("open"));
    }
  });
}

/* -------------------- ADMIN NAV TOGGLE -------------------- */
const adminToggle = document.querySelector(".admin-menu-toggle");
const adminLinks = document.querySelector(".admin-links");
if (adminToggle && adminLinks) {
  const toggleAdmin = () => {
    adminLinks.classList.toggle("open");
    adminToggle.setAttribute(
      "aria-expanded",
      adminLinks.classList.contains("open")
    );
  };

  adminToggle.addEventListener("click", toggleAdmin);
  adminToggle.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleAdmin();
    }
  });
}

/* -------------------- KITTEN GALLERY -------------------- */
const mainImage = document.getElementById("mainImage");
const galleryThumbs = document.querySelectorAll(".gallery-thumb");
const galleryMain = document.querySelector(".gallery-main");
if (mainImage && galleryThumbs.length) {
  let currentIndex = 0;

  const setActiveThumb = button => {
    galleryThumbs.forEach(btn => btn.classList.remove("active"));
    button.classList.add("active");
  };

  const setImageByIndex = index => {
    const total = galleryThumbs.length;
    const safeIndex = (index + total) % total;
    const button = galleryThumbs[safeIndex];
    const full = button.getAttribute("data-full");
    if (full) {
      mainImage.src = full;
      currentIndex = safeIndex;
      setActiveThumb(button);
    }
  };

  galleryThumbs.forEach((button, index) => {
    if (index === 0) setActiveThumb(button);
    button.addEventListener("click", () => setImageByIndex(index));
  });

  setImageByIndex(0);

  if (galleryMain) {
    let startX = 0;
    let startY = 0;
    let dragging = false;

    galleryMain.addEventListener("touchstart", e => {
      if (e.touches.length !== 1) return;
      dragging = true;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    });

    galleryMain.addEventListener("touchend", e => {
      if (!dragging) return;
      dragging = false;
      const endX = e.changedTouches[0].clientX;
      const endY = e.changedTouches[0].clientY;
      const deltaX = endX - startX;
      const deltaY = endY - startY;

      if (Math.abs(deltaX) > 40 && Math.abs(deltaX) > Math.abs(deltaY)) {
        if (deltaX < 0) {
          setImageByIndex(currentIndex + 1);
        } else {
          setImageByIndex(currentIndex - 1);
        }
      }
    });
  }
}

/* Expose reservation deposit from page when available */
const depositSource = document.querySelector("[data-reservation-deposit]");
if (depositSource) {
  const value = Number(depositSource.getAttribute("data-reservation-deposit"));
  if (!Number.isNaN(value)) {
    window.RESERVATION_DEPOSIT = value;
  }
}

const magSections = document.querySelectorAll('.mag-section');

function checkMagSections() {
  magSections.forEach(section => {
    const rect = section.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100) {
      section.classList.add('in-view');
    }
  });
}

window.addEventListener('scroll', checkMagSections);
window.addEventListener('load', checkMagSections);
