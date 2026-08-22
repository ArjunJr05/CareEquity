"""
app.py  —  CareEquity | SDoH Intervention Finder
Run:  streamlit run app.py

Backend: FastAPI on http://localhost:8000
  All data operations call api_client.py, which forwards to the FastAPI
  backend and falls back to direct module calls if the API is unreachable.
"""
import os, math, time, logging, datetime
import folium, pandas as pd, streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import api_client as api

st.set_page_config(
    page_title="CareEquity | SDoH Intervention Finder",
    page_icon="🏥", layout="wide", initial_sidebar_state="expanded",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
KM_TO_MILES = 0.621371

# ── Colour palettes ────────────────────────────────────────────────────────
PRIORITY_COLOUR = {
    "🔴 High Priority":   "#e74c3c",
    "🟠 Medium Priority": "#e67e22",
    "🟡 Low Priority":    "#f1c40f",
}
IV_COLOURS = {
    "Food Assistance":        "#e74c3c",
    "Housing Support":        "#3498db",
    "Transportation Support": "#2ecc71",
    "Healthcare Access":      "#9b59b6",
    "Employment Assistance":  "#f39c12",
    "Utility Assistance":     "#1abc9c",
}
DISTANCE_BADGE = [
    (3,  "#27ae60", "< 3 mi"),
    (9,  "#f39c12", "3–9 mi"),
    (18, "#e67e22", "9–18 mi"),
    (31, "#e74c3c", "18–31 mi"),
]
RANK_MEDALS = {1: ("🥇", "#FFD700"), 2: ("🥈", "#C0C0C0"), 3: ("🥉", "#CD7F32")}
SDOH_DISPLAY = {
    "food_insecurity":         ("🍎 Food Insecurity",   "%"),
    "housing_insecurity":      ("🏠 Housing Insecurity", "%"),
    "transportation_barrier":  ("🚌 Transport Barrier",  "%"),
    "lack_health_insurance":   ("💊 No Insurance",       "%"),
    "poverty_rate":            ("💵 Poverty Rate",       "%"),
    "unemployment_rate":       ("📋 Unemployment",       "%"),
    "svi_overall":             ("⚠️ SVI Overall",       "score"),
    "median_household_income": ("💰 Median Income",      "$"),
}
REQUEST_TEMPLATES = {
    "Food Assistance":
        "I am reaching out on behalf of a resident of {county}, {state} who is currently "
        "experiencing food insecurity. We would like to inquire about available food assistance "
        "programs, food bank access, or meal delivery services your organisation provides.",
    "Housing Support":
        "I am contacting you regarding housing support needs for a resident of {county}, {state}. "
        "The individual requires assistance with transitional housing, shelter placement, or "
        "affordable housing resources. Please advise on available programs and eligibility requirements.",
    "Transportation Support":
        "A resident of {county}, {state} requires transportation assistance to access essential "
        "services including healthcare, employment, and food resources. We are requesting information "
        "about transportation vouchers, ride services, or paratransit options available through your organisation.",
    "Healthcare Access":
        "I am writing to request information about healthcare access programs for an uninsured or "
        "underinsured resident of {county}, {state}. We are seeking sliding-scale clinic services, "
        "free health screenings, or enrollment assistance for health insurance coverage.",
    "Employment Assistance":
        "I am contacting your organisation on behalf of an unemployed resident of {county}, {state} "
        "who is seeking employment assistance. We are requesting information about job placement "
        "services, vocational training, resume support, or workforce development programs you offer.",
    "Utility Assistance":
        "A resident of {county}, {state} is in need of utility assistance due to financial hardship. "
        "We are requesting information about programs that assist with electricity, water, heating, "
        "or other utility costs, including any LIHEAP-affiliated or weatherisation programs available.",
}


# ══════════════════════════════════════════════════════════════════════════
# Small helpers
# ══════════════════════════════════════════════════════════════════════════

def km_to_mi(km):
    return round(float(km or 0) * KM_TO_MILES, 2)

def fmt_mi(km):
    return f"{km_to_mi(km or 0):.1f} mi"

def fmt_metric(v, unit):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    if unit == "$":
        return f"${v:,.0f}"
    if unit == "%":
        return f"{v:.1f}%"
    return f"{v:.3f}"

def dist_badge(km):
    mi = km_to_mi(km)
    for lim, col, lbl in DISTANCE_BADGE:
        if mi <= lim:
            return col, lbl
    return "#95a5a6", f"{mi:.1f} mi"

def gmaps_dir(olat, olon, clat, clon):
    return f"https://www.google.com/maps/dir/{clat},{clon}/{olat},{olon}"

def _has_coords(org):
    try:
        lat = org.get("lat")
        lon = org.get("lon")
        return (lat is not None and lon is not None
                and not math.isnan(float(lat)) and not math.isnan(float(lon)))
    except (TypeError, ValueError):
        return False

def _has_email(org):
    em = (org.get("email") or "").strip()
    return bool(em) and "no public email" not in em.lower()

def _is_csv_source(org):
    return org.get("source", "") == "CareEquity CSV"

def _is_directory_source(org):
    src = org.get("source", "")
    return src in ("CareEquity Directory", "CareEquity CSV")


# ══════════════════════════════════════════════════════════════════════════
# NGO selection — CSV-first pipeline
# ══════════════════════════════════════════════════════════════════════════

def get_top3(all_orgs, intervention="", state_abbr="", county_name="",
             lat=None, lon=None) -> list[dict]:
    """
get_top3 — Select the best 3 orgs to display for a given intervention.

Priority order:
  1. CSV orgs for this state/intervention with email, sorted by distance
  2. CSV orgs from any state with email (national scope top-up)
  3. ngo_directory fallback (guaranteed for Utility Assistance + any gaps)
"""
    # ── Tier 1 & 2: CSV orgs already loaded in all_orgs ──────────────────
    with_email = sorted(
        [o for o in all_orgs if _has_email(o) and (o.get("name") or "").strip()],
        key=lambda x: x.get("distance_km") or 9999,
    )
    result: list[dict] = list(with_email[:3])
    if len(result) >= 3:
        return result[:3]

    # ── Tier 3: ngo_directory guaranteed fallback ─────────────────────────
    if len(result) < 3 and intervention:
        from ngo_directory import get_fallback_ngos
        existing_names = {r["name"].lower() for r in result}
        for org in get_fallback_ngos(intervention, state_abbr, n=3):
            if len(result) >= 3:
                break
            n = (org.get("name") or "").strip().lower()
            if n and n not in existing_names:
                result.append(org)
                existing_names.add(n)

    return result[:3]


# ══════════════════════════════════════════════════════════════════════════
# Cached loaders  — all data now comes from FastAPI via api_client
# (with automatic fallback to local modules if API is offline)
# ══════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="Loading NGO database …", ttl=300)
def load_ngos_for_county(fips: str, lat: float, lon: float) -> dict:
    """
    Calls GET /ngos/all — returns county info + interventions + NGO lists.
    Cached for 5 minutes per (fips, lat, lon) tuple.
    """
    return api.get_all_ngos(fips=fips, lat=lat, lon=lon, top_n=3) or {}


@st.cache_data(show_spinner="Locating county …", ttl=3600)
def cached_geocode(fips: str, county_name: str, state_abbr: str) -> dict | None:
    """Calls GET /counties/{fips}/geocode — cached for 1 hour."""
    return api.geocode_county(fips, county_name, state_abbr)


# ══════════════════════════════════════════════════════════════════════════
# Map popup HTML
# ══════════════════════════════════════════════════════════════════════════

def _org_popup_html(org, clat, clon, iv_label):
    is_dir   = _is_directory_source(org)
    mi       = fmt_mi(org.get("distance_km", 0))
    name     = org.get("name", "Unknown")
    addr     = org.get("address", "") or "—"
    phone    = org.get("phone", "") or "—"
    email    = org.get("email", "") or "—"
    web      = org.get("website", "") or ""
    hours    = org.get("hours", "") or "—"
    olat     = org.get("lat")
    olon     = org.get("lon")
    wlink    = (f'<a href="{web}" target="_blank" style="color:#4fc3f7">Website</a>'
                if web else "—")
    dist_row = "📋 CSV / Directory org" if is_dir and not org.get("distance_km") else f"<b>{mi}</b> from county"
    gmaps_btn = ""
    if olat and olon:
        gurl = gmaps_dir(olat, olon, clat, clon)
        gmaps_btn = (
            f'<div style="margin-top:8px">'
            f'<a href="{gurl}" target="_blank" '
            f'style="background:#4285F4;color:white;padding:5px 10px;'
            f'border-radius:4px;text-decoration:none;font-size:12px">🗺 Get Directions</a></div>'
        )
    return (
        f'<div style="font-family:sans-serif;min-width:230px;max-width:300px">'
        f'<div style="background:#2c3e50;color:white;padding:8px 10px;'
        f'border-radius:6px 6px 0 0;margin:-1px -1px 8px"><b>{name}</b></div>'
        f'<table style="font-size:12px;width:100%;border-collapse:collapse">'
        f'<tr><td>🗂</td><td><b>{iv_label}</b></td></tr>'
        f'<tr><td>📏</td><td>{dist_row}</td></tr>'
        f'<tr><td>📧</td><td>{email}</td></tr>'
        f'<tr><td>📞</td><td>{phone}</td></tr>'
        f'<tr><td>📍</td><td>{addr}</td></tr>'
        f'<tr><td>🕐</td><td>{hours}</td></tr>'
        f'<tr><td>🔗</td><td>{wlink}</td></tr>'
        f'</table>{gmaps_btn}</div>'
    )


# ══════════════════════════════════════════════════════════════════════════
# Map builders
# ══════════════════════════════════════════════════════════════════════════

def _county_pin(m, clat, clon, county_name):
    folium.Marker(
        location=[clat, clon],
        tooltip=f"📍 {county_name} — County Centre",
        popup=folium.Popup(
            f"<b>📍 {county_name}</b><br>County Centre<br>"
            f"<small>({clat:.4f}, {clon:.4f})</small>",
            max_width=220),
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)


def build_overview_map(ngos_by_intervention, clat, clon, county_name, state_abbr=""):
    m = folium.Map(location=[clat, clon], zoom_start=7, tiles="CartoDB positron")
    _county_pin(m, clat, clon, county_name)

    for iv_label, orgs in ngos_by_intervention.items():
        display   = get_top3(orgs, intervention=iv_label, state_abbr=state_abbr,
                             county_name=county_name, lat=clat, lon=clon)
        if not display:
            continue
        iv_colour = IV_COLOURS.get(iv_label, "#3498db")
        cluster   = MarkerCluster(name=iv_label).add_to(m)

        for rank_i, org in enumerate(display, 1):
            olat    = org.get("lat")
            olon    = org.get("lon")
            medal   = RANK_MEDALS.get(rank_i, ("", ""))[0]
            dist_km = org.get("distance_km") or 0

            if olat is None or olon is None:
                # No coords → skip map pin but still show in cards
                continue

            try:
                olat_f = float(olat)
                olon_f = float(olon)
                if math.isnan(olat_f) or math.isnan(olon_f):
                    continue
            except (TypeError, ValueError):
                continue

            pin_loc   = [olat_f, olon_f]
            mi_str    = fmt_mi(dist_km)
            badge_c, _ = dist_badge(dist_km)

            # Dashed route line county → org
            folium.PolyLine(
                locations=[[clat, clon], pin_loc],
                color=iv_colour, weight=2, opacity=0.50, dash_array="6 4",
                tooltip=f"{org.get('name', '')} — {mi_str}",
            ).add_to(m)

            # Midpoint distance badge
            mid_lat = (clat + olat_f) / 2
            mid_lon = (clon + olon_f) / 2
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html=(
                        f'<div style="background:{badge_c};color:white;font-size:10px;'
                        f'font-weight:700;padding:2px 6px;border-radius:10px;'
                        f'white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.3)">'
                        f'{mi_str}</div>'
                    ),
                    icon_size=(60, 20), icon_anchor=(30, 10),
                ),
            ).add_to(m)

            # Org marker
            popup_html = _org_popup_html(org, clat, clon, iv_label)
            src        = org.get("source", "")
            pin_colour = "purple" if src == "CareEquity Directory" else "blue"
            pin_icon   = "info-sign" if src == "CareEquity Directory" else "building"
            folium.Marker(
                location=pin_loc,
                tooltip=f"{medal} #{rank_i} {org.get('name', '')}",
                popup=folium.Popup(popup_html, max_width=310),
                icon=folium.Icon(color=pin_colour, icon=pin_icon, prefix="fa"),
            ).add_to(cluster)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def build_single_org_map(org, clat, clon, county_name, iv_label):
    """Focused route map for one org. Works for CSV, directory and live orgs."""
    olat    = org.get("lat")
    olon    = org.get("lon")
    dist_km = org.get("distance_km") or 0
    iv_col  = IV_COLOURS.get(iv_label, "#3498db")

    # Validate coords
    has_real_coords = False
    if olat is not None and olon is not None:
        try:
            olat_f = float(olat)
            olon_f = float(olon)
            if not math.isnan(olat_f) and not math.isnan(olon_f):
                has_real_coords = True
        except (TypeError, ValueError):
            pass

    if not has_real_coords:
        m = folium.Map(location=[clat, clon], zoom_start=8, tiles="CartoDB positron")
        _county_pin(m, clat, clon, county_name)
        folium.Marker(
            location=[clat + 0.08, clon + 0.08],
            tooltip=f"📋 {org.get('name', '')}",
            popup=folium.Popup(
                _org_popup_html(org, clat, clon, iv_label), max_width=300),
            icon=folium.Icon(color="purple", icon="info-sign", prefix="fa"),
        ).add_to(m)
        return m

    # Real coords — route map
    mi_str = fmt_mi(dist_km)
    m = folium.Map(
        location=[(clat + olat_f) / 2, (clon + olon_f) / 2],
        zoom_start=11, tiles="CartoDB positron",
    )
    _county_pin(m, clat, clon, county_name)
    folium.Marker(
        location=[olat_f, olon_f],
        tooltip=org.get("name", ""),
        popup=folium.Popup(
            _org_popup_html(org, clat, clon, iv_label), max_width=300),
        icon=folium.Icon(color="blue", icon="plus-square", prefix="fa"),
    ).add_to(m)
    folium.PolyLine(
        locations=[[clat, clon], [olat_f, olon_f]],
        color=iv_col, weight=3, opacity=0.85,
        tooltip=f"~{mi_str} straight-line",
    ).add_to(m)
    mid_lat = (clat + olat_f) / 2
    mid_lon = (clon + olon_f) / 2
    folium.Marker(
        location=[mid_lat, mid_lon],
        icon=folium.DivIcon(
            html=(
                f'<div style="background:{iv_col};color:white;font-size:13px;'
                f'font-weight:800;padding:5px 12px;border-radius:14px;'
                f'box-shadow:0 2px 8px rgba(0,0,0,.4);white-space:nowrap">'
                f'📏 {mi_str}</div>'
            ),
            icon_size=(110, 30), icon_anchor=(55, 15),
        ),
    ).add_to(m)
    for loc, lbl, bg in [([clat, clon], "START", "#e74c3c"),
                          ([olat_f, olon_f], "DEST", "#27ae60")]:
        folium.Marker(
            location=loc,
            icon=folium.DivIcon(
                html=(
                    f'<div style="background:{bg};color:white;font-size:10px;'
                    f'padding:2px 7px;border-radius:8px;font-weight:700">{lbl}</div>'
                ),
                icon_size=(50, 20), icon_anchor=(25, -8),
            ),
        ).add_to(m)
    return m


# ══════════════════════════════════════════════════════════════════════════
# Send Request dialog  — REAL SMTP email delivery
# ══════════════════════════════════════════════════════════════════════════

def render_send_request_dialog(org, iv_label, county_name, state_abbr, form_idx):
    from urllib.parse import quote

    org_name  = org.get("name", "the organisation")
    org_email = (org.get("email") or "").strip()
    org_phone = org.get("phone", "")
    org_web   = org.get("website", "")
    org_addr  = org.get("address", "")
    iv_col    = IV_COLOURS.get(iv_label, "#3498db")
    template  = REQUEST_TEMPLATES.get(
        iv_label,
        "I am requesting assistance for a resident of {county}, {state}.",
    )
    body_default = template.format(county=county_name, state=state_abbr)

    safe_idx = str(form_idx).replace(" ", "_").replace("/", "_")
    sent_key = f"sent_{safe_idx}"
    req_key  = f"req_{safe_idx}"
    err_key  = f"err_{safe_idx}"

    # ── SMTP status via API ────────────────────────────────────────────────
    status = api.get_email_status()

    # ── Already sent — show receipt ────────────────────────────────────────
    if st.session_state.get(sent_key):
        sent     = st.session_state[sent_key]
        to_shown = sent.get("to_addr", "")
        st.markdown(
            f"""
            <div style="background:#071f07;border:2px solid #27ae60;
                        border-radius:14px;padding:32px 28px;margin:10px 0 16px;
                        text-align:center;">
              <div style="font-size:2.6rem;margin-bottom:10px">✅</div>
              <div style="font-size:1.25rem;font-weight:800;color:#27ae60;margin-bottom:10px;">
                Email Sent Successfully!
              </div>
              <div style="font-size:0.95rem;color:#ccc;margin-bottom:6px;">
                Your request was delivered to
                <b style="color:#e0e0e0">{sent['org_name']}</b>
              </div>
              <div style="font-size:0.82rem;color:#aaa;margin-bottom:4px;">
                📧 &nbsp;<code style="color:#4fc3f7">{to_shown}</code>
              </div>
              <div style="font-size:0.78rem;color:#777;margin-top:8px;">
                {sent.get('timestamp','')}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        bc1, bc2 = st.columns([1.3, 1])
        with bc1:
            if org_web:
                st.link_button("🌐 Visit Organisation Website", org_web,
                               use_container_width=True)
        with bc2:
            if st.button("✕ Close", key=f"close_{sent_key}",
                         use_container_width=True):
                del st.session_state[sent_key]
                st.session_state.pop(err_key, None)
                st.session_state[req_key] = False
                st.rerun()
        return

    # ── Header with SMTP status ────────────────────────────────────────────
    smtp_dot   = "🟢" if status.get("configured") else "🔴"
    smtp_label = (f"SMTP ready · {status.get('username','')}"
                  if status.get("configured") else "SMTP not configured")

    st.markdown(
        f"""
        <div style="background:#080818;border:2px solid {iv_col};
                    border-radius:12px;padding:18px 22px;margin:10px 0 14px;">
          <div style="display:flex;justify-content:space-between;
                      align-items:center;flex-wrap:wrap;gap:8px;">
            <div>
              <div style="font-size:1rem;font-weight:800;color:{iv_col};margin-bottom:2px;">
                📨 Send Assistance Request
              </div>
              <div style="font-size:0.82rem;color:#aaa;">
                To: <b style="color:#e0e0e0">{org_name}</b>
                &nbsp;·&nbsp;
                <span style="color:{iv_col};">{iv_label}</span>
              </div>
            </div>
            <div style="font-size:0.75rem;color:#aaa;background:#1a1a2e;
                        padding:4px 10px;border-radius:8px;white-space:nowrap;">
              {smtp_dot} {smtp_label}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not status.get("configured"):
        st.warning(
            "⚠️ **SMTP not configured** — email will open in your local email "
            "client instead of being sent directly from the server.  \n"
            "Add your Gmail App Password to `.streamlit/secrets.toml`.",
            icon="⚙️",
        )

    if st.session_state.get(err_key):
        st.error(st.session_state[err_key], icon="❌")

    # ── Compose form ───────────────────────────────────────────────────────
    with st.form(key=f"reqform_{safe_idx}"):
        c1, c2 = st.columns(2)
        with c1:
            sender_name  = st.text_input("Your Name / Organisation *",
                                         placeholder="e.g. City Health Department")
        with c2:
            sender_email = st.text_input("Your Email Address * (Reply-To)",
                                         placeholder="you@example.org")
        c3, c4 = st.columns(2)
        with c3:
            org_email_field = st.text_input(
                "Send To (organisation email)", value=org_email,
                placeholder="contact@ngo.org",
                help="Verified email from our NGO database. Edit if needed.",
            )
        with c4:
            st.text_input("Organisation", value=org_name, disabled=True)

        contact_parts = [p for p in [
            org_phone and f"📞 {org_phone}",
            org_addr  and f"📍 {org_addr}",
            org_web   and f"🌐 {org_web}",
        ] if p]
        if contact_parts:
            st.markdown(
                '<div style="background:#1a1a2e;border-radius:8px;padding:8px 12px;'
                'font-size:0.8rem;color:#aaa;margin:2px 0 8px;">'
                + " &nbsp;·&nbsp; ".join(contact_parts) + "</div>",
                unsafe_allow_html=True,
            )

        subject = st.text_input(
            "Subject",
            value=f"{iv_label} Assistance Request — {county_name}, {state_abbr}",
        )
        message = st.text_area("Message Body", value=body_default, height=165,
                               help="Delivered directly to the organisation's inbox.")

        btn_label = ("📤 Send Email Now"
                     if status.get("configured") else "📤 Open in Email Client")
        btn_help  = (f"Sends via {status.get('provider','')} immediately"
                     if status.get("configured") else "Opens your local email client")

        cs, cc, _ = st.columns([1.5, 1, 2.5])
        with cs:
            submitted = st.form_submit_button(btn_label, type="primary",
                                              use_container_width=True, help=btn_help)
        with cc:
            cancelled = st.form_submit_button("✕ Cancel", use_container_width=True)

    # ── Handle submit ──────────────────────────────────────────────────────
    if submitted:
        errors = []
        if not sender_name.strip():
            errors.append("your name")
        if not sender_email.strip() or "@" not in sender_email:
            errors.append("a valid email address for yourself")
        if not org_email_field.strip() or "@" not in org_email_field:
            errors.append("the organisation email address")

        if errors:
            st.warning(f"⚠️ Please enter {', '.join(errors)}.")
        else:
            to_addr = org_email_field.strip()

            if status.get("configured"):
                # ── POST /email/send via api_client ───────────────────────
                with st.spinner(f"Sending email to {to_addr} …"):
                    result = api.send_email(
                        to_addr      = to_addr,
                        subject      = subject.strip(),
                        body         = message.strip(),
                        sender_name  = sender_name.strip(),
                        sender_email = sender_email.strip(),
                        reply_to     = sender_email.strip(),
                    )
                if result.get("success"):
                    st.session_state.pop(err_key, None)
                    st.session_state[sent_key] = {
                        "org_name":  org_name,
                        "to_addr":   to_addr,
                        "web":       org_web,
                        "timestamp": "Sent at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    st.rerun()
                else:
                    st.session_state[err_key] = f"Send failed: {result.get('message','Unknown error')}"
                    st.rerun()
            else:
                # ── mailto fallback ───────────────────────────────────────
                full_body   = f"From: {sender_name.strip()} <{sender_email.strip()}>\n\n{message.strip()}"
                mailto_link = (f"mailto:{to_addr}"
                               f"?subject={quote(subject.strip())}"
                               f"&body={quote(full_body)}")
                st.session_state[sent_key] = {
                    "org_name":  org_name,
                    "to_addr":   to_addr,
                    "mailto":    mailto_link,
                    "web":       org_web,
                    "timestamp": "Prepared at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                st.markdown(
                    f"""<div style="background:#0a1628;border:2px solid #f39c12;
                                border-radius:10px;padding:16px 20px;margin:10px 0;">
                      <div style="color:#f39c12;font-weight:700;margin-bottom:8px;">
                        📋 Message ready — click below to open your email client
                      </div>
                      <a href="{mailto_link}" style="display:inline-block;
                         background:#f39c12;color:#111;font-weight:800;
                         padding:10px 22px;border-radius:8px;text-decoration:none;
                         font-size:14px;">📤 Open Email Client</a></div>""",
                    unsafe_allow_html=True,
                )
                st.rerun()

    if cancelled:
        st.session_state.pop(err_key, None)
        st.session_state[req_key] = False
        st.rerun()

    if st.session_state.get(sent_key):
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# UI sections
# ══════════════════════════════════════════════════════════════════════════

def render_header():
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(
            "<h1 style='margin-bottom:0'>🏥 CareEquity</h1>"
            "<p style='color:#aaa;margin-top:4px'>"
            "SDoH-driven intervention recommendations and NGO matching "
            "for every US county — powered by 1,275 verified organisations</p>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        stats  = api.get_stats()
        n      = stats.get("ngo_count", 0)
        status = api.get_email_status()

        if api.api_is_alive():
            st.success("⚡ API online")
        else:
            st.warning("⚡ API offline")

        if n > 0:
            st.success(f"📋 {n:,} NGOs")
        else:
            st.warning("CSV not found")

        if status.get("configured"):
            st.success("📧 Email ready")
        else:
            st.warning("📧 SMTP off")


def render_county_selector():
    """Uses api_client for state/county lists and county search."""
    st.sidebar.header("📍 Select County")
    mode = st.sidebar.radio("Search by", ["State & County", "FIPS Code", "County Name"])

    if mode == "State & County":
        result = api.list_states_and_counties()
        states = result.get("states", []) if isinstance(result, dict) else []
        state  = st.sidebar.selectbox("State", ["— select —"] + states)
        if state == "— select —":
            return None
        counties = api.list_states_and_counties(state=state)
        if not isinstance(counties, list) or not counties:
            st.sidebar.warning("No counties found.")
            return None
        county_names = [c["county_name"] for c in counties]
        name = st.sidebar.selectbox("County", county_names)
        match = next((c for c in counties if c["county_name"] == name), None)
        return match["county_fips"] if match else None

    elif mode == "FIPS Code":
        val = st.sidebar.text_input("5-digit FIPS", max_chars=5, placeholder="06037")
        if val.strip():
            fips = val.strip().zfill(5)
            profile = api.get_county_profile(fips)
            if profile:
                return fips
            st.sidebar.error(f"FIPS {fips} not found.")
        return None

    else:  # County Name search
        q = st.sidebar.text_input("Search name", placeholder="Los Angeles")
        if not q.strip():
            return None
        matches = api.search_counties(q.strip())
        if not matches:
            st.sidebar.warning("No match.")
            return None
        options = [f"{m['county_name']}, {m['state_abbr']}" for m in matches]
        chosen  = st.sidebar.selectbox("Select", options)
        idx     = options.index(chosen)
        return matches[idx]["county_fips"]


def render_sdoh_profile(info):
    rc = "#e74c3c" if info["high_risk"] else "#27ae60"
    rt = ("🔴 HIGH RISK — SVI Overall > 0.75" if info["high_risk"]
          else "🟢 Standard Risk")
    st.markdown(
        f'<div style="background:{rc}22;border-left:5px solid {rc};'
        f'padding:10px 16px;border-radius:6px;font-weight:600;color:{rc}">'
        f'{rt}</div><br>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for i, (key, (label, unit)) in enumerate(SDOH_DISPLAY.items()):
        cols[i % 4].metric(label, fmt_metric(info.get(key), unit))
    st.markdown("")
    chart_data = {
        "Food Insecurity":  info.get("food_insecurity", 0) or 0,
        "Housing Insecurity": info.get("housing_insecurity", 0) or 0,
        "Transport Barrier": info.get("transportation_barrier", 0) or 0,
        "No Insurance":     info.get("lack_health_insurance", 0) or 0,
        "Poverty Rate":     info.get("poverty_rate", 0) or 0,
        "Unemployment":     info.get("unemployment_rate", 0) or 0,
    }
    st.bar_chart(
        pd.DataFrame({
            "Risk Factor": list(chart_data),
            "Value (%)":   list(chart_data.values()),
        }).set_index("Risk Factor"),
        height=260,
    )


def render_interventions(interventions):
    if not interventions:
        st.info("No intervention data.")
        return
    for rank, iv in enumerate(interventions, 1):
        label  = iv["intervention"]
        sev    = iv["severity"]
        prio   = iv["priority_label"]
        colour = PRIORITY_COLOUR.get(prio, "#95a5a6")
        bar    = int(sev * 100)
        st.markdown(
            f'<div style="border-left:6px solid {colour};padding:14px 18px;'
            f'margin-bottom:14px;background:#16213e;border-radius:8px;'
            f'box-shadow:0 2px 8px rgba(0,0,0,.3)">'
            f'<div style="font-size:0.75rem;color:{colour};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.5px">'
            f'{prio} &nbsp;·&nbsp; #{rank}</div>'
            f'<div style="font-size:1.2rem;font-weight:800;color:#f0f0f0;'
            f'margin:4px 0 10px">{label}</div>'
            f'<div style="background:#0f3460;border-radius:6px;height:12px">'
            f'<div style="width:{bar}%;background:{colour};height:12px;'
            f'border-radius:6px"></div></div>'
            f'<div style="font-size:0.78rem;color:#aaa;margin-top:6px">'
            f'Severity: <b style="color:{colour}">{sev:.3f}</b>'
            f' &nbsp;|&nbsp; {bar}th percentile</div></div>',
            unsafe_allow_html=True,
        )


def _drow(icon, text):
    t = (text or "").strip()
    if not t:
        return ""
    return (f'<div style="font-size:0.82rem;color:#ccc;margin-top:4px">'
            f'{icon} {t.replace("<","&lt;").replace(">","&gt;")}</div>')

def _dlink(url):
    u = (url or "").strip()
    if not u:
        return ""
    d = u[:48] + ("…" if len(u) > 48 else "")
    return (f'<div style="font-size:0.82rem;margin-top:4px">'
            f'<a href="{u}" target="_blank" style="color:#4fc3f7">🌐 {d}</a></div>')

def _verif_badge(org):
    src = org.get("source", "")
    if src == "CareEquity Directory":
        return ('<span style="background:#8e44ad;color:white;font-size:0.62rem;'
                'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
                '📋 DIRECTORY</span>')
    if src == "CareEquity CSV":
        if _has_email(org) and _has_coords(org):
            return ('<span style="background:#27ae60;color:white;font-size:0.62rem;'
                    'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
                    '✓ CSV · EMAIL + GPS</span>')
        if _has_email(org):
            return ('<span style="background:#2980b9;color:white;font-size:0.62rem;'
                    'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
                    '✓ CSV · EMAIL</span>')
        return ('<span style="background:#636e72;color:white;font-size:0.62rem;'
                'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
                '📋 CSV</span>')
    if _has_email(org) and _has_coords(org):
        return ('<span style="background:#27ae60;color:white;font-size:0.62rem;'
                'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
                '✓ EMAIL + GPS</span>')
    if _has_email(org):
        return ('<span style="background:#2980b9;color:white;font-size:0.62rem;'
                'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
                '✓ EMAIL</span>')
    return ""


def render_ngo_cards(ngos_by_intervention, interventions, clat, clon,
                     county_name, state_abbr):
    for iv in interventions:
        label    = iv["intervention"]
        prio     = iv["priority_label"]
        sev      = iv["severity"]
        colour   = PRIORITY_COLOUR.get(prio, "#95a5a6")
        iv_col   = IV_COLOURS.get(label, "#3498db")
        all_orgs = ngos_by_intervention.get(label, [])
        display  = get_top3(all_orgs, intervention=label, state_abbr=state_abbr,
                            county_name=county_name, lat=clat, lon=clon)
        total    = len(all_orgs)
        n_email  = sum(1 for o in display if _has_email(o))

        # ── Section banner ────────────────────────────────────────────────
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{iv_col}22,#0f3460);'
            f'border-left:5px solid {colour};border-radius:10px;'
            f'padding:14px 18px;margin:24px 0 16px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<div><div style="font-size:0.7rem;color:{colour};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">{prio}</div>'
            f'<div style="font-size:1.15rem;font-weight:800;color:#f0f0f0">{label}</div></div>'
            f'<div style="text-align:right">'
            f'<div style="background:{colour}33;border:1px solid {colour};color:{colour};'
            f'font-size:0.8rem;font-weight:700;padding:4px 12px;border-radius:20px">'
            f'Top {len(display)} of {total} found</div>'
            f'<div style="font-size:0.7rem;color:#888;margin-top:4px">'
            f'{n_email} with email · severity {sev:.3f}</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        if not display:
            st.markdown(
                '<div style="background:#1a1a2e;border:1px dashed #444;'
                'border-radius:8px;padding:16px;text-align:center;color:#888">'
                '⚠️ No organisations found.</div>',
                unsafe_allow_html=True,
            )
            continue

        for idx, org in enumerate(display):
            rank      = idx + 1
            medal, mc = RANK_MEDALS[rank]
            dist_km   = org.get("distance_km") or 0
            src       = org.get("source", "")
            is_dir    = src in ("CareEquity Directory",)
            is_csv    = src == "CareEquity CSV"
            name      = org.get("name", "Unknown")
            addr      = org.get("address", "")
            phone     = org.get("phone", "")
            email     = org.get("email", "")
            web       = org.get("website", "")
            hours     = org.get("hours", "")
            olat      = org.get("lat")
            olon      = org.get("lon")

            # Distance display
            if is_dir and not org.get("distance_km"):
                dist_display = "National Org"
                badge_c2     = "#8e44ad"
                badge_l2     = "Directory"
                badge_note   = "national"
            elif is_csv and not org.get("distance_km"):
                dist_display = "CSV Verified"
                badge_c2     = "#2980b9"
                badge_l2     = "Verified"
                badge_note   = "csv"
            else:
                badge_c, badge_l = dist_badge(dist_km)
                dist_display     = fmt_mi(dist_km)
                badge_c2         = badge_c
                badge_l2         = badge_l
                badge_note       = "straight-line"

            gmaps_url = gmaps_dir(olat, olon, clat, clon) if (olat and olon) else "#"
            map_key   = f"map_{label}_{idx}"
            req_key   = f"req_{label}_{idx}"

            detail = (
                _drow("📍", addr)
                + _drow("📧", email)
                + _drow("📞", phone)
                + _drow("🕐", hours)
                + _dlink(web)
                + _drow("📡", src)
            )

            # ── Card ──────────────────────────────────────────────────────
            st.markdown(
                f'<div style="background:#1a1a2e;border-radius:12px;'
                f'padding:20px 18px 14px;margin-bottom:14px;'
                f'border:1px solid {mc}55;box-shadow:0 4px 14px rgba(0,0,0,.45);'
                f'position:relative">'
                f'<div style="position:absolute;top:-11px;left:16px;'
                f'background:{mc};color:#111;font-size:0.72rem;font-weight:800;'
                f'padding:3px 12px;border-radius:20px;box-shadow:0 2px 6px rgba(0,0,0,.4)">'
                f'{medal} #{rank} NEAREST</div>'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:flex-start;gap:12px;margin-top:4px">'
                f'<div style="flex:1">'
                f'<div style="font-size:1rem;font-weight:800;color:#f0f0f0;'
                f'line-height:1.3">{name}{_verif_badge(org)}</div>'
                f'{detail}</div>'
                f'<div style="text-align:center;min-width:90px;flex-shrink:0">'
                f'<div style="background:{badge_c2};color:white;font-size:1.05rem;'
                f'font-weight:800;padding:10px 10px 6px;border-radius:24px;'
                f'box-shadow:0 3px 10px rgba(0,0,0,.4);line-height:1.1">'
                f'{dist_display}</div>'
                f'<div style="font-size:0.68rem;color:{badge_c2};margin-top:5px;'
                f'font-weight:700;text-transform:uppercase;letter-spacing:.5px">'
                f'{badge_l2}</div>'
                f'<div style="font-size:0.62rem;color:#666;margin-top:2px">'
                f'{badge_note}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )

            # ── Buttons ───────────────────────────────────────────────────
            b1, b2, b3, _ = st.columns([1.1, 1.1, 1.3, 2])
            with b1:
                if st.button("🗺 View Map", key=f"btn_map_{label}_{idx}"):
                    st.session_state[map_key] = not st.session_state.get(map_key, False)
            with b2:
                if olat and olon:
                    st.markdown(
                        f'<a href="{gmaps_url}" target="_blank">'
                        f'<button style="background:#4285F4;color:white;border:none;'
                        f'padding:7px 10px;border-radius:7px;cursor:pointer;'
                        f'font-size:12px;font-weight:600;width:100%">'
                        f'🧭 Directions</button></a>',
                        unsafe_allow_html=True,
                    )
            with b3:
                if st.button("📨 Send Request", key=f"btn_req_{label}_{idx}",
                             type="primary"):
                    st.session_state[req_key] = not st.session_state.get(req_key, False)

            # ── Route map (toggled) ────────────────────────────────────────
            if st.session_state.get(map_key):
                iv_col2 = IV_COLOURS.get(label, "#3498db")
                if not (olat and olon) or is_dir:
                    st.markdown(
                        f'<div style="background:#1e0a30;border:1px solid #8e44ad;'
                        f'border-radius:8px;padding:12px 16px;margin:6px 0">'
                        f'<b style="color:#8e44ad">📋 {name}</b> is a national/state '
                        f'organisation. No specific GPS — contact them directly.<br>'
                        f'<span style="color:#aaa;font-size:0.82rem">📧 {email}'
                        + (f' &nbsp;·&nbsp; <a href="{web}" target="_blank" '
                           f'style="color:#4fc3f7">{web}</a>' if web else "")
                        + f'</span></div>',
                        unsafe_allow_html=True,
                    )
                    st_folium(
                        build_single_org_map(org, clat, clon, county_name, label),
                        key=f"folium_{label}_{idx}", height=300,
                        use_container_width=True, returned_objects=[],
                    )
                else:
                    mi_str   = fmt_mi(dist_km)
                    badge_c, _ = dist_badge(dist_km)
                    st.markdown(
                        f'<div style="background:#0f3460;border-radius:8px;'
                        f'padding:10px 14px;margin:6px 0">'
                        f'<b style="color:{iv_col2}">📍 Route: </b>'
                        f'<span style="color:#e0e0e0">{county_name}</span>'
                        f' → <span style="color:#e0e0e0">{name}</span>'
                        f'<span style="color:{badge_c};font-weight:700;margin-left:10px">'
                        f'~{mi_str}</span></div>',
                        unsafe_allow_html=True,
                    )
                    st_folium(
                        build_single_org_map(org, clat, clon, county_name, label),
                        key=f"folium_{label}_{idx}", height=350,
                        use_container_width=True, returned_objects=[],
                    )

            # ── Send Request form (toggled) ────────────────────────────────
            if st.session_state.get(req_key):
                render_send_request_dialog(
                    org, label, county_name, state_abbr,
                    form_idx=f"{label}_{idx}",
                )

            st.markdown(
                '<hr style="border:none;border-top:1px solid #23233a;margin:6px 0">',
                unsafe_allow_html=True,
            )


def render_overview_map(ngos_by_intervention, clat, clon, county_name, state_abbr=""):
    orgs_with_pin = sum(
        1 for v in ngos_by_intervention.values()
        for o in get_top3(v, county_name=county_name)
        if _has_coords(o)
    )
    st.markdown(
        f'<h4 style="margin-bottom:4px">🗺 County Overview Map</h4>'
        f'<p style="color:#aaa;font-size:0.85rem;margin-top:0">'
        f'Shows county centre + up to 3 nearest organisations per intervention '
        f'with confirmed GPS coordinates ({orgs_with_pin} pins). '
        f'Orgs without GPS are shown in the cards below.</p>',
        unsafe_allow_html=True,
    )
    legend_html = "".join(
        f'<span style="background:{c};color:white;padding:2px 9px;'
        f'border-radius:10px;font-size:11px;margin:2px;display:inline-block">{iv}</span>'
        for iv, c in IV_COLOURS.items() if ngos_by_intervention.get(iv)
    )
    st.markdown(f'<div style="margin-bottom:10px">{legend_html}</div>',
                unsafe_allow_html=True)
    st_folium(
        build_overview_map(ngos_by_intervention, clat, clon, county_name, state_abbr),
        key="overview_map", height=520,
        use_container_width=True, returned_objects=[],
    )


def render_data_table(ngos_by_intervention, state_abbr="", county_name="",
                      clat=None, clon=None):
    rows = []
    for iv, orgs in ngos_by_intervention.items():
        for rank_i, org in enumerate(
            get_top3(orgs, iv, state_abbr, county_name, clat, clon), 1
        ):
            src = org.get("source", "")
            no_dist = src in ("CareEquity Directory",) or not org.get("distance_km")
            rows.append({
                "Rank":          f"#{rank_i}",
                "Intervention":  iv,
                "Name":          org.get("name", ""),
                "Distance (mi)": "—" if no_dist else f"{km_to_mi(org.get('distance_km',0)):.1f}",
                "Email":         org.get("email", ""),
                "Phone":         org.get("phone", ""),
                "Website":       org.get("website", ""),
                "City":          org.get("city", "") or org.get("address", ""),
                "State":         org.get("state", state_abbr),
                "Source":        src,
            })
    if not rows:
        return
    tbl = pd.DataFrame(rows)
    st.subheader("📋 Top 3 Organisations per Intervention")
    st.caption(
        "Green badge = email + GPS verified in CSV.  "
        "Purple = national directory org.  "
        "Distance is straight-line from county centre."
    )
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download CSV",
        data=tbl.to_csv(index=False).encode(),
        file_name="nearby_ngos.csv",
        mime="text/csv",
    )


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main():
    render_header()
    selected_fips = render_county_selector()

    if not selected_fips:
        st.info("👈 Select a county in the sidebar to begin.")
        with st.expander("Dataset overview", expanded=True):
            stats = api.get_stats()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total counties",    f"{stats.get('total_counties',0):,}")
            c2.metric("High-risk counties", f"{stats.get('high_risk_counties',0):,}")
            c3.metric("States covered",    f"{stats.get('states_covered',0)}")
            if api.api_is_alive():
                st.caption(f"⚡ FastAPI backend online — {API_BASE}")
            else:
                st.caption("⚡ FastAPI offline — running in local fallback mode")
        return

    # ── Fetch county profile + interventions via API ───────────────────────
    with st.spinner("Loading county data …"):
        iv_data = api.get_county_interventions(selected_fips, top_n=3)

    if not iv_data:
        st.error(f"Could not load data for FIPS {selected_fips}.")
        return

    county_info   = iv_data["county"]
    interventions = iv_data["interventions"]

    rc = "#e74c3c" if county_info["high_risk"] else "#27ae60"
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">'
        f'<h2 style="margin:0">{county_info["county_name"]}, {county_info["state_abbr"]}</h2>'
        f'<span style="background:{rc};color:white;padding:3px 12px;'
        f'border-radius:12px;font-size:0.8rem;font-weight:700">'
        f'{"HIGH RISK" if county_info["high_risk"] else "Standard"}</span></div>'
        f'<p style="color:#aaa;margin:0 0 14px">FIPS: <code>{county_info["county_fips"]}</code>'
        f' &nbsp;·&nbsp; Pop: <b>{int(county_info.get("population") or 0):,}</b>'
        f' &nbsp;·&nbsp; SVI: <b>{county_info.get("svi_overall","N/A")}</b></p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["📊 SDoH Profile", "🎯 Interventions", "🤝 NGOs & Maps"])

    with tab1:
        render_sdoh_profile(county_info)

    with tab2:
        render_interventions(interventions)

    with tab3:
        geo_key = f"geo_{selected_fips}"
        ngo_key = f"ngos_{selected_fips}"

        # ── Geocode via API ───────────────────────────────────────────────
        if geo_key not in st.session_state:
            geo = cached_geocode(
                selected_fips,
                county_info["county_name"],
                county_info["state_abbr"],
            )
            st.session_state[geo_key] = geo

        geo = st.session_state[geo_key]
        if geo is None:
            st.error("Could not geocode this county.")
            return
        clat, clon = geo["lat"], geo["lon"]
        st.caption(f"County centre: {clat:.4f}, {clon:.4f}")

        # ── Load NGOs via GET /ngos/all ───────────────────────────────────
        if ngo_key not in st.session_state:
            with st.spinner("Loading NGOs from verified database …"):
                all_data = load_ngos_for_county(selected_fips, clat, clon)

            if all_data:
                ngo_data = all_data.get("ngos", {})
                st.session_state[ngo_key] = ngo_data
                total   = sum(len(v) for v in ngo_data.values())
                n_email = sum(1 for v in ngo_data.values() for o in v if _has_email(o))
                n_gps   = sum(1 for v in ngo_data.values() for o in v if _has_coords(o))
                st.success(
                    f"✅ Loaded {total} organisations "
                    f"({n_email} with email, {n_gps} with GPS) "
                    f"— via {'API' if api.api_is_alive() else 'local fallback'}."
                )
            else:
                st.error("Failed to load NGO data.")
                return
        else:
            col_refresh, _ = st.columns([1, 5])
            with col_refresh:
                if st.button("🔄 Refresh"):
                    del st.session_state[ngo_key]
                    st.cache_data.clear()
                    st.rerun()

        if ngo_key in st.session_state:
            ngo_data = st.session_state[ngo_key]
            render_overview_map(ngo_data, clat, clon,
                                county_info["county_name"], county_info["state_abbr"])
            st.markdown("---")
            render_ngo_cards(ngo_data, interventions, clat, clon,
                             county_info["county_name"], county_info["state_abbr"])
            st.markdown("---")
            render_data_table(ngo_data,
                              state_abbr=county_info["state_abbr"],
                              county_name=county_info["county_name"],
                              clat=clat, clon=clon)

    # ── Sidebar quick stats ───────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 Quick Stats")

    _s = api.get_email_status()
    if _s.get("configured"):
        st.sidebar.markdown(
            f'<div style="background:#071f07;border-left:4px solid #27ae60;'
            f'padding:6px 10px;border-radius:4px;font-size:0.78rem;'
            f'color:#27ae60;font-weight:600;margin-bottom:6px;">'
            f'📧 Email: {_s["username"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            '<div style="background:#1a0a00;border-left:4px solid #e67e22;'
            'padding:6px 10px;border-radius:4px;font-size:0.78rem;'
            'color:#e67e22;font-weight:600;margin-bottom:6px;">'
            '⚙️ SMTP not configured<br>'
            '<span style="font-weight:400;font-size:0.7rem;">'
            'Edit .streamlit/secrets.toml</span></div>',
            unsafe_allow_html=True,
        )

    # API status badge in sidebar
    if api.api_is_alive():
        st.sidebar.markdown(
            f'<div style="background:#071f07;border-left:4px solid #27ae60;'
            f'padding:6px 10px;border-radius:4px;font-size:0.78rem;'
            f'color:#27ae60;font-weight:600;margin-bottom:6px;">'
            f'⚡ API: {API_BASE}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            '<div style="background:#1a0a00;border-left:4px solid #e67e22;'
            'padding:6px 10px;border-radius:4px;font-size:0.78rem;'
            'color:#e67e22;font-weight:600;margin-bottom:6px;">'
            '⚡ API offline — local mode</div>',
            unsafe_allow_html=True,
        )

    rc2 = "#e74c3c" if county_info["high_risk"] else "#27ae60"
    st.sidebar.markdown(
        f'<div style="background:{rc2}22;border-left:4px solid {rc2};'
        f'padding:6px 10px;border-radius:4px;font-size:0.85rem;'
        f'color:{rc2};font-weight:600">'
        f'{"🔴 HIGH RISK" if county_info["high_risk"] else "🟢 Standard Risk"}</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.metric("SVI Overall",  fmt_metric(county_info.get("svi_overall"), "score"))
    st.sidebar.metric("Population",   f"{int(county_info.get('population') or 0):,}")
    st.sidebar.metric("Poverty Rate", fmt_metric(county_info.get("poverty_rate"), "%"))
    if interventions:
        iv0 = interventions[0]
        c   = PRIORITY_COLOUR.get(iv0["priority_label"], "#aaa")
        st.sidebar.markdown(
            f'<div style="background:#1a1a2e;border-left:4px solid {c};'
            f'padding:8px 12px;border-radius:6px;margin-top:8px">'
            f'<div style="font-size:0.7rem;color:{c};font-weight:700">TOP INTERVENTION</div>'
            f'<div style="font-size:0.95rem;font-weight:700;color:#e0e0e0">'
            f'{iv0["intervention"]}</div>'
            f'<div style="font-size:0.75rem;color:#aaa">Severity: {iv0["severity"]:.3f}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
