import streamlit as st
from PIL import Image, ImageOps
import base64
import io

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="My Projects",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Data — edit this list to add / remove / update your own projects
#
# Notes on fields:
# - "images": list of image entries. Each entry can be EITHER:
#     * a plain string path/URL, e.g. "RC_Car/Isometric.jpeg", or
#     * a dict for when a photo needs manual rotation correction, e.g.
#       {"path": "RC_Car/Isometric.jpeg", "rotate": 90}
#   "rotate" is clockwise degrees (try 90, 180, or 270/-90 until it looks
#   right — see load_image() below for why this is sometimes needed instead
#   of relying on EXIF alone). Use forward slashes ("RC_Car/Isometric.jpeg")
#   even on Windows — backslashes can be misread as escape characters in
#   Python strings and won't work if you ever deploy on Linux (e.g.
#   Streamlit Community Cloud).
# - "video_url": a YouTube/Vimeo link OR a direct .mp4 path — both work with
#   st.video. Leave as "" if there's no demo video.
# - "errors_encountered": list of {"issue", "solution"} dicts describing
#   bugs/failures you hit and how you fixed them. Leave as [] if none.
# ----------------------------------------------------------------------------
PROJECTS = [
    {
        "title": "RC Obstacle-Avoidance Car",
        "summary": "A four-wheeled robot that is controlled by a remote and has obstacle detection using an ultrasonic sensor.",
        "full_description": (
            "Designed, built, and programmed a fully custom autonomous obstacle-avoidance car, "
            "3D-printing the entire chassis and fasteners from an Onshape CAD model and integrating "
            "an Arduino Uno, L298N motor driver, HC-SR04 ultrasonic sensor, and TSOP34S40 IR receiver, "
            "all documented in a complete KiCad schematic. Along the way, I redesigned the drivetrain "
            "to a rear-wheel-drive layout after parts constraints limited me to two motors, reinforced "
            "3D-printed fasteners that were failing under motor-mount stress, diagnosed and corrected "
            "a ~20% speed discrepancy between the drive motors by adding per-motor PWM compensation in firmware, "
            "and traced erratic ultrasonic readings to electrical interference from a shared breadboard with the "
            "IR receiver — resolving it by separating the sensors onto different boards, which also let me reposition "
            "the ultrasonic sensor for better front-facing coverage. The project brought together CAD design, "
            "DFM considerations for 3D printing, circuit design, and embedded C++, and reinforced how much of engineering "
            "is diagnosing why something isn't working before you can fix it."
        ),
        "tags": ["Onshape", "KiCad", "Arduino", "C++"],
        "images": [
            # If a photo still looks sideways after this fix, turn its entry
            # into a dict and add "rotate" — e.g.:
            # {"path": "RC_Car/Isometric.jpeg", "rotate": 90},
            "RC_Car/Isometric.jpeg",
            #"RC_Car/Front.jpeg",
            "RC_Car/Top.jpeg",
            "RC_Car/Schematic.png",
        ],
        "video_url": "",
        "repo_url": "https://github.com/yourname/line-follower",
        "demo_url": "",
        "status": "Completed",
        "errors_encountered": [
            {
                "issue": "Parts constraints forced a redesign as I did not have the"
                         "four wheels/motors available that most reference builds use.",
                "solution": "I redesigned the drivetrain around a rear-wheel-drive "
                            "layout (inspired by modern car architecture) with two driven wheels "
                            "and two free-rolling casters — which also improved weight distribution "
                            "and structural support.",
            },
            {
                "issue": "The ultrasonic sensor was reading erratically. I traced "
                         "the issue to electrical interference from sharing a breadboard with the IR sensor. ",
                "solution": "I moved the ultrasonic sensor to a separate breadboard, further from the IR sensor, "
                            "resolved the noise. This also allowed me to relocate it to a better front-mounted position for "
                            "improved obstacle detection.",
            },
            {
                "issue": "The car wouldn't drive straight on flat surfaces ",
                "solution": "After investigating, I found the two drive motors — despite being \"identical\" — ran at meaningfully "
                            "different speeds under the same PWM signal. I diagnosed this with direct testing and corrected it with "
                            "a per-motor PWM compensation factor of 20% in firmware, resolving the veering issue",
            }
        ],
    }
]

# ----------------------------------------------------------------------------
# Custom styling
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ==========================================================================
       ADJUSTABLE SIZES — this is the one place to look to change how big
       anything is. Each variable is used below; change the number, save,
       and the app updates everywhere that value is used.
       ========================================================================== */
    :root {
        /* --- Image heights --- */
        --card-thumbnail-height: 520px;   /* thumbnail photo on each project card (grid view) */
        --gallery-image-height: 480px;    /* photos in the gallery row (detail view) */

        /* --- Text sizes --- */
        --card-title-size: 1.25rem;       /* project title on each card (grid view) */
        --card-summary-size: 1.25rem;      /* project summary paragraph on each card (grid view) */
        --detail-title-size: 2.5rem;        /* project title on the detail page */
        --tag-size: 1.15rem;              /* small tag pills, e.g. "Arduino" */
        --status-badge-size: 0.75rem;     /* "Completed" / "In Progress" pill */
        --description-text-size: 1.1rem;    /* the full project description paragraph */
        --error-heading-size: 1.1rem;    /* "Issue N: ..." expander header text */
        --error-body-size: 1.1rem;        /* solution text inside each expander */
        --error-arrow-size: 1.6rem;        /* the expand/collapse arrow icon to the left of each issue */
    }

    .project-card {
        border: 1px solid #2a2a2a22;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.2rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        background-color: rgba(127, 127, 127, 0.03);
    }
    .project-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }
    .project-card h3 {
        font-size: var(--card-title-size);
    }
    /* Project summary paragraph on each card (grid view) */
    .project-summary {
        font-size: var(--card-summary-size);
        line-height: 1.5;
    }
    .tag {
        display: inline-block;
        background-color: #eef2ff;
        color: #3730a3;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: var(--tag-size);
        margin-right: 6px;
        margin-top: 4px;
    }
    .status-badge {
        float: right;
        font-size: var(--status-badge-size);
        padding: 2px 10px;
        border-radius: 999px;
    }
    .status-Completed { background-color: #dcfce7; color: #166534; }
    .status-InProgress { background-color: #fef9c3; color: #854d0e; }
    /* Card thumbnail: a FIXED height (not max-height) plus full column
       width, so the height variable always has a visible effect — the
       photo is cropped via object-fit to fill that box regardless of its
       own aspect ratio or however wide/narrow the column is. */
    .project-card img {
        width: 100%;
        height: var(--card-thumbnail-height);
        object-fit: cover;
        border-radius: 8px;
    }
    /* Streamlit wraps every st.image() in a container that shows a small
       floating toolbar (fullscreen icon) with its own background — this is
       the "rectangle" that sits above the thumbnail. Hide it and strip any
       default spacing so the photo sits flush at the top of the card. */
    div[data-testid="stElementToolbar"] {
        display: none !important;
    }
    div[data-testid="stImage"] {
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stImageContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* Detail-page project title */
    .detail-title {
        font-size: var(--detail-title-size);
        display: inline-block;
        margin-bottom: 0;
    }
    /* Gallery: all photos in one row, same height, width auto-scaled to
       each photo's aspect ratio. */
    .gallery-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: flex-start;
    }
    .gallery-row img {
        height: var(--gallery-image-height);
        width: auto;
        border-radius: 8px;
    }
    /* Full project description paragraph on the detail page */
    .project-description {
        font-size: var(--description-text-size);
        line-height: 1.6;
    }
    /* Larger, more readable text for the Errors Encountered section. */
    div[data-testid="stExpander"] summary p {
        font-size: var(--error-heading-size) !important;
    }
    div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {
        font-size: var(--error-body-size) !important;
        line-height: 1.6;
    }
    /* Bigger arrow icon to the left of each "Issue N: ..." expander header.
       Streamlit renders this as an svg inside the summary element; scaling
       the svg directly (rather than just its wrapper) is what actually
       changes the visible arrow size. */
    div[data-testid="stExpander"] summary svg {
        width: var(--error-arrow-size) !important;
        height: var(--error-arrow-size) !important;
    }
    div[data-testid="stExpanderToggleIcon"] {
        width: var(--error-arrow-size) !important;
        height: var(--error-arrow-size) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Image loading helper — fixes photos that appear rotated/flipped
#
# Phone/camera photos often store rotation as EXIF metadata instead of
# actually rotating the pixel data, and st.image() does NOT read that tag.
# ImageOps.exif_transpose() fixes the common case by rotating the pixels to
# match the EXIF Orientation tag.
#
# BUT: that only works if the tag is present and correct. It silently does
# nothing if the tag is missing, and it can even rotate the WRONG way if a
# photo was already re-saved/edited by another app that baked in a rotation
# but left a stale Orientation tag behind. That mismatch is the most common
# reason images still look rotated after an EXIF-only fix.
#
# To guarantee a fix regardless of what's in (or missing from) the file's
# metadata, this also supports an explicit manual "rotate" override per
# image (see the PROJECTS data above) that is applied on top of, or instead
# of, the EXIF correction.
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_image(image_entry):
    # Normalize the entry into (path, manual_rotation_degrees)
    if isinstance(image_entry, dict):
        path = image_entry.get("path", "")
        manual_rotation = image_entry.get("rotate", 0)
    else:
        path = image_entry
        manual_rotation = 0

    if isinstance(path, str) and path.startswith(("http://", "https://")):
        # Remote images: st.image fetches these itself, and we can't easily
        # re-rotate a URL. Manual rotation only applies to local files.
        return path

    try:
        img = Image.open(path)
        img.load()  # force-read pixel data now, before any cache/file issues
        img = ImageOps.exif_transpose(img)  # best-effort EXIF-based fix
        if manual_rotation:
            # PIL's rotate() is counter-clockwise for positive angles, so we
            # negate to make "rotate": 90 mean 90° clockwise (the intuitive
            # direction most people mean when a photo is "rotated 90°").
            img = img.rotate(-manual_rotation, expand=True)
        return img
    except Exception:
        # Fall back to the raw path so st.image can at least show its own
        # "image not found" error instead of a silent crash here.
        return path


def image_to_src(image_entry):
    """
    Turns an image entry into a string usable as an <img src="..."> value:
    - Remote URLs pass through unchanged.
    - Local files are loaded (with rotation/EXIF fixes applied) and encoded
      as a base64 data URI, since a raw local filesystem path can't be
      reached by the browser once this loads in the page.
    """
    result = load_image(image_entry)
    if isinstance(result, str):
        return result  # URL, or a path that failed to load (browser will 404)

    buffer = io.BytesIO()
    save_format = "PNG" if result.mode in ("RGBA", "LA", "P") else "JPEG"
    if save_format == "JPEG" and result.mode != "RGB":
        result = result.convert("RGB")
    result.save(buffer, format=save_format)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    mime = "image/png" if save_format == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


# ----------------------------------------------------------------------------
# Session state — tracks whether we're on the grid view or a detail view
# ----------------------------------------------------------------------------
if "selected_project" not in st.session_state:
    st.session_state.selected_project = None


def show_project(title):
    st.session_state.selected_project = title


def show_grid():
    st.session_state.selected_project = None


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.title("🗂️ Syed Shayan Ahmed's Projects")
st.sidebar.write("Browse and filter through my engineering project portfolio.")

search_query = st.sidebar.text_input("Search projects", placeholder="e.g. robot")

all_tags = sorted({tag for p in PROJECTS for tag in p["tags"]})
selected_tags = st.sidebar.multiselect("Filter by tag", options=all_tags)

statuses = sorted({p["status"] for p in PROJECTS})
selected_status = st.sidebar.multiselect("Filter by status", options=statuses)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit 🎈")

# ============================================================================
# DETAIL VIEW
# ============================================================================
if st.session_state.selected_project is not None:
    project = next(
        (p for p in PROJECTS if p["title"] == st.session_state.selected_project), None
    )

    if project is None:
        st.warning("Project not found.")
        st.button("← Back to projects", on_click=show_grid)
    else:
        st.button("← Back to projects", on_click=show_grid)

        status_class = project["status"].replace(" ", "")
        st.markdown(
            f'<h1 class="detail-title">{project["title"]}</h1>'
            f'<span class="status-badge status-{status_class}">{project["status"]}</span>',
            unsafe_allow_html=True,
        )
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in project["tags"])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.write("")

        link_cols = st.columns([1, 1, 4])
        with link_cols[0]:
            if project.get("repo_url"):
                st.link_button("View Code", project["repo_url"])
        with link_cols[1]:
            if project.get("demo_url"):
                st.link_button("Live Demo", project["demo_url"])

        st.markdown("---")

        # --- Image gallery ---
        images = project.get("images", [])
        if images:
            st.subheader("Gallery")
            # All photos in one row at the same height; each photo's width
            # scales automatically to keep its own aspect ratio.
            img_tags = "".join(
                f'<img src="{image_to_src(img)}">' for img in images
            )
            st.markdown(f'<div class="gallery-row">{img_tags}</div>', unsafe_allow_html=True)

        # --- Video demo ---
        if project.get("video_url"):
            st.subheader("Video Demo")
            st.video(project["video_url"])

        # --- Description ---
        st.subheader("Description")
        st.markdown(
            f'<div class="project-description">{project["full_description"]}</div>',
            unsafe_allow_html=True,
        )

        # --- Errors encountered ---
        errors = project.get("errors_encountered", [])
        if errors:
            st.subheader("Errors Encountered")
            for i, err in enumerate(errors, start=1):
                with st.expander(f"Issue {i}: {err['issue']}"):
                    st.markdown(f"**Solution:** {err['solution']}")

# ============================================================================
# GRID VIEW
# ============================================================================
else:
    st.title("My Projects")
    st.write("A collection of engineering things I've built. Use the sidebar to search or filter.")
    st.markdown("---")

    def matches_filters(project):
        haystack = (project["title"] + project["summary"]).lower()
        if search_query and search_query.lower() not in haystack:
            return False
        if selected_tags and not set(selected_tags).intersection(project["tags"]):
            return False
        if selected_status and project["status"] not in selected_status:
            return False
        return True

    filtered_projects = [p for p in PROJECTS if matches_filters(p)]

    if not filtered_projects:
        st.info("No projects match your filters. Try adjusting them in the sidebar.")
    else:
        cols_per_row = 2
        for i in range(0, len(filtered_projects), cols_per_row):
            row_projects = filtered_projects[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            for col, project in zip(cols, row_projects):
                with col:
                    st.markdown('<div class="project-card">', unsafe_allow_html=True)

                    thumbnail = project["images"][0] if project.get("images") else None
                    if thumbnail:
                        # use_container_width lets the image fill the card;
                        # the actual displayed height/crop is now controlled
                        # entirely by the .project-card img CSS rule above
                        # (via --card-thumbnail-height), not by a fixed
                        # pixel width here.
                        st.image(load_image(thumbnail), use_container_width=True)

                    status_class = project["status"].replace(" ", "")
                    st.markdown(
                        f'<h3 style="display:inline-block; margin-bottom:0;">{project["title"]}</h3>'
                        f'<span class="status-badge status-{status_class}">{project["status"]}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="project-summary">{project["summary"]}</div>',
                        unsafe_allow_html=True,
                    )

                    tags_html = "".join(f'<span class="tag">{t}</span>' for t in project["tags"])
                    st.markdown(tags_html, unsafe_allow_html=True)

                    extras = []
                    if len(project.get("images", [])) > 1:
                        extras.append(f"{len(project['images'])} photos")
                    if project.get("video_url"):
                        extras.append("video demo")
                    if project.get("errors_encountered"):
                        extras.append(f"{len(project['errors_encountered'])} issues logged")
                    if extras:
                        st.caption(" · ".join(extras))

                    st.write("")
                    st.button(
                        "View Details",
                        key=f"view_{project['title']}",
                        on_click=show_project,
                        args=(project["title"],),
                        use_container_width=True,
                    )

                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.caption(f"Showing {len(filtered_projects)} of {len(PROJECTS)} projects.")
