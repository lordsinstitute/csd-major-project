/**
 * PropLens AI - Frontend Controller (JavaScript ES6+)
 * Leaflet.js Interactive Map, Map Scanner (Pillar 1), Smart Estimator (Pillar 2),
 * Explainability Breakdown (Pillar 3), and SQLite Database Logging Integration.
 */

// Determine API Base URL dynamically (supports Flask server on any port, or local file:// protocol)
const API_BASE = (window.location.protocol === "http:" || window.location.protocol === "https:")
  ? window.location.origin
  : "http://127.0.0.1:5000";

// Global Application State (Default: New York City)
const state = {
  map: null,
  propertyMarker: null,
  radiusCircle: null,
  amenitiesLayerGroup: null,
  currentLat: 40.7128,
  currentLng: -74.0060,
  latestScan: null
};

// Prominent New York City Geospatial Presets
const NYC_PRESETS = {
  "Manhattan Hub": { lat: 40.7580, lng: -73.9855, name: "Manhattan Hub (Times Square)" },
  "Tech Corridor": { lat: 40.7260, lng: -73.9988, name: "Tech Corridor (SoHo/Greenwich Village)" },
  "Suburban Greens": { lat: 40.6782, lng: -73.9442, name: "Suburban Greens (Brooklyn)" },
  "Lakeside Enclave": { lat: 40.7829, lng: -73.9654, name: "Lakeside Enclave (Central Park)" }
};

// Category Icons and Color Mappings for Leaflet Markers
const CATEGORY_META = {
  transit: { icon: "🚇", class: "pin-transit", color: "#06b6d4", label: "Transit" },
  school: { icon: "🏫", class: "pin-school", color: "#f59e0b", label: "School" },
  hospital: { icon: "🏥", class: "pin-hospital", color: "#ef4444", label: "Hospital" },
  park: { icon: "🌳", class: "pin-park", color: "#10b981", label: "Park" },
  commercial: { icon: "🛍️", class: "pin-commercial", color: "#a855f7", label: "Commercial" }
};

// =============================================================================
// INITIALIZATION
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initLeafletMap();
  initFormEventListeners();
  checkSystemHealth();
  fetchHistory();

  // Initial trigger for New York City
  updatePropertyLocation(state.currentLat, state.currentLng, "New York City (Downtown)");

  // Force Leaflet to recalculate container bounds after DOM layout settles to prevent blank/black screen rendering
  setTimeout(() => {
    if (state.map) {
      state.map.invalidateSize();
    }
  }, 100);
  setTimeout(() => {
    if (state.map) {
      state.map.invalidateSize();
    }
  }, 400);
});

// Recalculate container bounds on window resize
window.addEventListener("resize", () => {
  if (state.map) {
    state.map.invalidateSize();
  }
});

// =============================================================================
// PILLAR 1: LEAFLET MAP & 1KM SCANNER ENGINE
// =============================================================================
function initLeafletMap() {
  const mapElement = document.getElementById("map") || document.getElementById("leaflet-map");
  if (!mapElement) {
    console.error("Leaflet map container not found!");
    return;
  }

  // Initialize Leaflet map instance centered on New York City at default zoom level 12
  state.map = L.map(mapElement, {
    center: [state.currentLat, state.currentLng],
    zoom: 12,
    zoomControl: true
  });

  // OpenStreetMap Tile Layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | PropLens AI'
  }).addTo(state.map);

  // Layer group for dynamic 1km amenity markers
  state.amenitiesLayerGroup = L.layerGroup().addTo(state.map);

  // Map Click Handler: captures coordinates and executes 1km scan
  state.map.on("click", (e) => {
    const { lat, lng } = e.latlng;
    // Clear active preset buttons when clicking custom location
    document.querySelectorAll(".preset-btn").forEach(btn => btn.classList.remove("active"));
    updatePropertyLocation(lat, lng, "Custom Selected Pin");
  });

  // Force initial bounding calculation
  state.map.invalidateSize();
}

/**
 * Creates custom HTML div icon for Leaflet markers
 */
function createCustomIcon(emoji, bgClass, size = 30) {
  return L.divIcon({
    className: "custom-leaflet-pin",
    html: `<div class="custom-pin ${bgClass}" style="width:${size}px; height:${size}px; line-height:${size}px; text-align:center;">${emoji}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2]
  });
}

/**
 * Updates selected property marker and 1km radius visual circle
 */
function updatePropertyLocation(lat, lng, locationLabel = "Selected Location") {
  state.currentLat = parseFloat(lat.toFixed(6));
  state.currentLng = parseFloat(lng.toFixed(6));

  // Update input boxes
  document.getElementById("prop-lat").value = state.currentLat;
  document.getElementById("prop-lng").value = state.currentLng;

  // 1. Position Property Marker
  if (state.propertyMarker) {
    state.propertyMarker.setLatLng([state.currentLat, state.currentLng]);
  } else {
    state.propertyMarker = L.marker([state.currentLat, state.currentLng], {
      icon: createCustomIcon("📍", "pin-property", 36),
      draggable: true
    }).addTo(state.map);

    // Support dragging property pin
    state.propertyMarker.on("dragend", (e) => {
      const pos = e.target.getLatLng();
      updatePropertyLocation(pos.lat, pos.lng, "Dragged Pin");
    });
  }

  state.propertyMarker.bindPopup(`
    <div class="popup-title">📌 ${locationLabel}</div>
    <div>Lat: <b>${state.currentLat}</b>, Lng: <b>${state.currentLng}</b></div>
    <div style="margin-top: 4px; font-size: 0.7rem; color: #9ca3af;">Scanning 1,000m perimeter...</div>
  `).openPopup();

  // 2. Position 1km (1,000 meters) Radius Circle
  if (state.radiusCircle) {
    state.radiusCircle.setLatLng([state.currentLat, state.currentLng]);
  } else {
    state.radiusCircle = L.circle([state.currentLat, state.currentLng], {
      radius: 1000,
      color: "#6366f1",
      fillColor: "#6366f1",
      fillOpacity: 0.12,
      weight: 2,
      dashArray: "6, 6"
    }).addTo(state.map);
  }

  // Smoothly pan map to new coordinates
  state.map.panTo([state.currentLat, state.currentLng], { animate: true, duration: 0.6 });

  // 3. Trigger Backend 1km Amenity Scan (Pillar 1)
  fetchNeighborhoodAmenities(state.currentLat, state.currentLng);
}

/**
 * Calls backend /api/scan-amenities endpoint to retrieve amenities within 1km
 */
async function fetchNeighborhoodAmenities(lat, lng) {
  const container = document.getElementById("amenity-items-container");
  container.innerHTML = `<p class="placeholder-text">Scanning 1 km radius for transit, schools, hospitals & parks...</p>`;

  try {
    const response = await fetch(`${API_BASE}/api/scan-amenities`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latitude: lat, longitude: lng })
    });

    if (!response.ok) throw new Error("Failed to scan amenities");

    const data = await response.json();
    state.latestScan = data;

    // Update Category Counters
    document.getElementById("count-transit").textContent = data.counts.transit || 0;
    document.getElementById("count-school").textContent = data.counts.schools || 0;
    document.getElementById("count-hospital").textContent = data.counts.hospitals || 0;
    document.getElementById("count-park").textContent = data.counts.parks || 0;
    document.getElementById("count-commercial").textContent = data.counts.commercial || 0;

    // Update Result Card Livability Preview
    document.getElementById("res-livability").textContent = `${data.livability_score} / 100`;
    document.getElementById("res-amenity-total").textContent = `${data.total_amenities} Detected`;

    // Render Amenity List Items in Sidebar
    renderAmenityList(data.amenities);

    // Plot Amenity Markers on Leaflet Map
    renderAmenityMarkers(data.amenities);

  } catch (error) {
    console.warn("Amenity scan error:", error);
    container.innerHTML = `<p class="placeholder-text" style="color:#ef4444;">Unable to load amenities from backend.</p>`;
  }
}

/**
 * Renders categorized amenity pins onto Leaflet map inside 1km radius
 */
function renderAmenityMarkers(amenities) {
  state.amenitiesLayerGroup.clearLayers();

  amenities.forEach(amenity => {
    const meta = CATEGORY_META[amenity.category] || { icon: "📍", class: "pin-property", color: "#6366f1", label: "Amenity" };
    const marker = L.marker([amenity.latitude, amenity.longitude], {
      icon: createCustomIcon(meta.icon, meta.class, 26)
    });

    marker.bindPopup(`
      <div class="popup-title">${amenity.name}</div>
      <div class="popup-badge" style="background:${meta.color}22; color:${meta.color}; border:1px solid ${meta.color}44;">
        ${meta.icon} ${meta.label}
      </div>
      <div>Distance: <b>${amenity.distance_meters} meters</b></div>
      <div style="font-size:0.7rem; color:#9ca3af; margin-top:2px;">User Rating: ⭐ ${amenity.rating} / 5.0</div>
    `);

    state.amenitiesLayerGroup.addLayer(marker);
  });
}

/**
 * Populates sidebar list of nearby amenities
 */
function renderAmenityList(amenities) {
  const container = document.getElementById("amenity-items-container");
  if (!amenities || amenities.length === 0) {
    container.innerHTML = `<p class="placeholder-text">No amenities detected within 1km.</p>`;
    return;
  }

  container.innerHTML = amenities.slice(0, 15).map(item => {
    const meta = CATEGORY_META[item.category] || { icon: "📍", label: "Place" };
    return `
      <div class="amenity-row">
        <div class="amenity-row-info">
          <span>${meta.icon}</span>
          <span style="font-weight:600; color:#e5e7eb;">${item.name}</span>
        </div>
        <span class="amenity-dist">${item.distance_meters}m</span>
      </div>
    `;
  }).join("");
}

// =============================================================================
// PILLAR 2 & 3: SMART VALUATION ESTIMATOR & EXPLAINABILITY
// =============================================================================
function initFormEventListeners() {
  const form = document.getElementById("property-form");
  const areaSlider = document.getElementById("prop-area");
  const ageSlider = document.getElementById("prop-age");
  const areaVal = document.getElementById("area-val");
  const ageVal = document.getElementById("age-val");

  // Dynamic slider indicators
  areaSlider.addEventListener("input", (e) => {
    areaVal.textContent = Number(e.target.value).toLocaleString();
  });

  ageSlider.addEventListener("input", (e) => {
    ageVal.textContent = e.target.value;
  });

  // Toggle button groups (Bedrooms & Bathrooms)
  setupButtonGroup("bhk-group", "prop-bedrooms");
  setupButtonGroup("bath-group", "prop-bathrooms");

  // Preset location buttons
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".preset-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const lat = parseFloat(btn.dataset.lat);
      const lng = parseFloat(btn.dataset.lng);
      const name = btn.dataset.name;
      updatePropertyLocation(lat, lng, name);
    });
  });

  // Manual coordinate input changes
  document.getElementById("prop-lat").addEventListener("change", (e) => {
    const val = parseFloat(e.target.value);
    if (Number.isFinite(val) && val >= -90 && val <= 90) {
      updatePropertyLocation(val, state.currentLng, "Custom Coordinates");
    } else {
      e.target.value = state.currentLat;
    }
  });
  document.getElementById("prop-lng").addEventListener("change", (e) => {
    const val = parseFloat(e.target.value);
    if (Number.isFinite(val) && val >= -180 && val <= 180) {
      updatePropertyLocation(state.currentLat, val, "Custom Coordinates");
    } else {
      e.target.value = state.currentLng;
    }
  });

  // Clear history button
  document.getElementById("btn-clear-history").addEventListener("click", clearHistory);

  // Form Submission -> Triggers /api/predict
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleCalculateValuation();
  });
}

function setupButtonGroup(groupId, hiddenInputId) {
  const group = document.getElementById(groupId);
  const hiddenInput = document.getElementById(hiddenInputId);
  const buttons = group.querySelectorAll(".btn-toggle");

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      hiddenInput.value = btn.dataset.val;
    });
  });
}

/**
 * Handles property valuation calculation request
 */
async function handleCalculateValuation() {
  const submitBtn = document.getElementById("submit-btn");
  const btnText = submitBtn.querySelector(".btn-text");
  const spinner = submitBtn.querySelector(".spinner");

  // Gather Form Inputs
  const propertyType = document.querySelector('input[name="property_type"]:checked').value;
  const areaSqft = parseFloat(document.getElementById("prop-area").value);
  const propertyAge = parseInt(document.getElementById("prop-age").value);
  const bedrooms = parseInt(document.getElementById("prop-bedrooms").value);
  const bathrooms = parseInt(document.getElementById("prop-bathrooms").value);
  const lat = state.currentLat;
  const lng = state.currentLng;

  // Set loading UI
  submitBtn.disabled = true;
  btnText.textContent = "Estimating Valuation...";
  spinner.style.display = "inline-block";

  try {
    const payload = {
      property_type: propertyType,
      area_sqft: areaSqft,
      bedrooms: bedrooms,
      bathrooms: bathrooms,
      property_age: propertyAge,
      latitude: lat,
      longitude: lng
    };

    const response = await fetch(`${API_BASE}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error("Valuation calculation failed");

    const data = await response.json();
    renderValuationResults(data);

    // Refresh SQLite History Table
    fetchHistory();

  } catch (error) {
    console.error("Valuation Error:", error);
    alert("Could not complete valuation. Ensure Flask backend server is running on http://127.0.0.1:5000.");
  } finally {
    submitBtn.disabled = false;
    btnText.textContent = "⚡ Calculate Market Valuation & Scan 1km";
    spinner.style.display = "none";
  }
}

/**
 * Updates UI with predicted market valuation and explainability decomposition
 */
function renderValuationResults(data) {
  const val = data.valuation;
  const breakdown = val.breakdown;
  const scan = data.neighborhood_scan;

  // Pillar 2: Price Summary
  document.getElementById("res-price").textContent = Number(val.predicted_price).toLocaleString();
  document.getElementById("res-confidence").textContent =
    `$${Number(val.confidence_low).toLocaleString()} - $${Number(val.confidence_high).toLocaleString()}`;
  document.getElementById("res-sqft-rate").textContent = `$${val.price_per_sqft} / sqft`;
  document.getElementById("res-livability").textContent = `${scan.livability_score} / 100`;
  document.getElementById("res-amenity-total").textContent = `${scan.total_amenities} Detected`;

  // Pillar 3: Factor Decomposition (Explainability Bars)
  // 1. Size
  document.getElementById("bar-size-val").textContent =
    `+$${Number(breakdown.size_contribution).toLocaleString()} (${breakdown.size_percentage}%)`;
  document.getElementById("bar-size").style.width = `${Math.min(100, breakdown.size_percentage * 1.5)}%`;

  // 2. Neighborhood Amenities
  document.getElementById("bar-amenity-val").textContent =
    `+$${Number(breakdown.neighborhood_amenity_contribution).toLocaleString()} (${breakdown.neighborhood_percentage}%)`;
  document.getElementById("bar-amenity").style.width = `${Math.min(100, breakdown.neighborhood_percentage * 1.8)}%`;

  // 3. Room Configuration
  document.getElementById("bar-rooms-val").textContent =
    `+$${Number(breakdown.rooms_contribution).toLocaleString()} (${breakdown.rooms_percentage}%)`;
  document.getElementById("bar-rooms").style.width = `${Math.min(100, breakdown.rooms_percentage * 1.8)}%`;

  // 4. Property Type Premium
  const typeWrapper = document.getElementById("type-premium-wrapper");
  if (breakdown.property_type_premium > 0) {
    typeWrapper.style.display = "flex";
    document.getElementById("bar-type-val").textContent =
      `+$${Number(breakdown.property_type_premium).toLocaleString()} (${breakdown.property_type_percentage}%)`;
    document.getElementById("bar-type").style.width = `${Math.min(100, breakdown.property_type_percentage * 1.8)}%`;
  } else {
    typeWrapper.style.display = "none";
  }

  // 5. Age Depreciation
  document.getElementById("bar-age-val").textContent =
    `-$${Number(Math.abs(breakdown.age_depreciation)).toLocaleString()}`;
  const ageDeprPct = Math.min(100, (Math.abs(breakdown.age_depreciation) / (val.predicted_price || 1)) * 300);
  document.getElementById("bar-age").style.width = `${ageDeprPct}%`;

  // Sub-factor Badges
  const subs = breakdown.sub_factors;
  document.getElementById("sub-transit").textContent = `+$${Number(subs.transit_and_metro).toLocaleString()}`;
  document.getElementById("sub-schools").textContent = `+$${Number(subs.premier_schools).toLocaleString()}`;
  document.getElementById("sub-health").textContent = `+$${Number(subs.healthcare_access).toLocaleString()}`;
  document.getElementById("sub-parks").textContent = `+$${Number(subs.parks_and_greenery).toLocaleString()}`;

  // Scroll to valuation results smoothly
  document.getElementById("valuation-result-card").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// =============================================================================
// DATABASE LOGGING (SQLite proplens.db)
// =============================================================================
async function fetchHistory() {
  const tbody = document.getElementById("history-table-body");
  try {
    const res = await fetch(`${API_BASE}/api/history?limit=10`);
    if (!res.ok) throw new Error("History fetch error");
    const data = await res.json();

    if (!data.records || data.records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="placeholder-cell">No property valuation queries logged yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.records.map(row => {
      const timeStr = row.timestamp ? row.timestamp.split(" ")[1] || row.timestamp : "--";
      return `
        <tr>
          <td>#${row.id}</td>
          <td>${row.property_type.replace("_", " ")}</td>
          <td>${row.area_sqft} sqft</td>
          <td>${row.bedrooms}B</td>
          <td style="color:#34d399; font-weight:700;">$${Number(row.predicted_price).toLocaleString()}</td>
          <td><span style="color:#06b6d4;">${row.livability_score}</span></td>
          <td>${timeStr}</td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.warn("Could not fetch database records:", err);
    tbody.innerHTML = `<tr><td colspan="7" class="placeholder-cell">Database records will appear after first prediction.</td></tr>`;
  }
}

async function clearHistory() {
  if (!confirm("Are you sure you want to clear the SQLite query log?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/history/clear`, { method: "POST" });
    if (res.ok) {
      fetchHistory();
    }
  } catch (err) {
    console.error("Clear history error:", err);
  }
}

// =============================================================================
// SYSTEM HEALTH CHECK
// =============================================================================
async function checkSystemHealth() {
  const statusElem = document.getElementById("system-status");
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      statusElem.innerHTML = `
        <span class="status-dot"></span>
        <span class="status-text">Flask & SQLite Connected</span>
      `;
    }
  } catch (err) {
    statusElem.innerHTML = `
      <span class="status-dot" style="background:#f59e0b; box-shadow:0 0 8px #f59e0b;"></span>
      <span class="status-text" style="color:#fbbf24;">Standby / Offline</span>
    `;
  }
}
