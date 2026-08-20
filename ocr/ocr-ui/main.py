import os

import requests
import streamlit as st


# ============================================================
# Configuration
# ============================================================

# Docker:
#   BACKEND_URL=http://ocr-backend:8000
#
# Local execution:
#   http://127.0.0.1:8000

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="CareEquity Medical Data Extractor",
    page_icon="🏥",
    layout="wide",
)


# ============================================================
# Session State
# ============================================================

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

if "file_format" not in st.session_state:
    st.session_state.file_format = None


# ============================================================
# Header
# ============================================================

st.title("CareEquity Medical Data Extractor 🏥")

st.write(
    "Upload a medical PDF or Word document (.docx) "
    "to extract structured patient, clinical, and "
    "Social Determinants of Health (SDOH) information."
)


# ============================================================
# Document Upload
# ============================================================

file = st.file_uploader(
    "Upload medical document",
    type=["pdf", "docx"],
    help="Supported formats: PDF and DOCX",
)


# ============================================================
# Document Type
# ============================================================

file_format = st.radio(
    "Select document type",
    options=[
        "patient_details",
    ],
    horizontal=True,
)


# ============================================================
# Extract Information
# ============================================================

if file and st.button(
    "Extract Information",
    type="primary",
):

    with st.spinner(
        "Processing medical document..."
    ):

        try:

            # ------------------------------------------------
            # Determine uploaded file type
            # ------------------------------------------------

            filename = file.name.lower()

            if filename.endswith(".pdf"):

                mime_type = "application/pdf"

            elif filename.endswith(".docx"):

                mime_type = (
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )

            else:

                st.error(
                    "Only PDF and DOCX files are supported."
                )

                st.stop()

            # ------------------------------------------------
            # Prepare multipart file
            # ------------------------------------------------

            files = {
                "file": (
                    file.name,
                    file.getvalue(),
                    mime_type,
                )
            }

            # ------------------------------------------------
            # Form data
            # ------------------------------------------------

            data = {
                "file_format": file_format,
            }

            # ------------------------------------------------
            # Send to FastAPI backend
            # ------------------------------------------------

            response = requests.post(
                f"{BACKEND_URL}/extract",
                data=data,
                files=files,
                timeout=180,
            )

            # ------------------------------------------------
            # Raise HTTP errors
            # ------------------------------------------------

            response.raise_for_status()

            # ------------------------------------------------
            # Parse response
            # ------------------------------------------------

            result = response.json()

            st.session_state.extracted_data = result
            st.session_state.file_format = file_format

            st.success(
                "Document processed successfully."
            )

        except requests.exceptions.Timeout:

            st.error(
                "The document took too long to process. "
                "Please try a smaller document."
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "Unable to connect to the OCR backend. "
                "Please make sure the FastAPI backend is running."
            )

        except requests.exceptions.HTTPError as error:

            try:

                error_detail = response.json().get(
                    "detail",
                    str(error),
                )

            except Exception:

                error_detail = str(error)

            st.error(
                f"Backend error: {error_detail}"
            )

        except requests.exceptions.RequestException as error:

            st.error(
                f"Request failed: {error}"
            )

        except Exception as error:

            st.error(
                f"Unexpected error: {error}"
            )


# ============================================================
# Uploaded Document Information
# ============================================================

if file:

    st.divider()

    st.subheader(
        "📄 Uploaded Document"
    )

    file_bytes = file.getvalue()

    file_size_kb = (
        len(file_bytes) / 1024
    )

    st.write(
        f"**File:** {file.name}"
    )

    st.write(
        f"**Size:** {file_size_kb:.2f} KB"
    )

    st.write(
        f"**Type:** "
        f"{'PDF' if file.name.lower().endswith('.pdf') else 'DOCX'}"
    )

    # Determine MIME type for download
    if file.name.lower().endswith(".pdf"):

        download_mime = "application/pdf"

    else:

        download_mime = (
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    st.download_button(
        label="Download Uploaded Document",
        data=file_bytes,
        file_name=file.name,
        mime=download_mime,
    )


# ============================================================
# Extracted Information
# ============================================================

result = st.session_state.extracted_data


if result:

    st.divider()

    st.header(
        "📋 Extracted Information"
    )

    # ========================================================
    # Main extracted data
    # ========================================================

    extracted_data = result.get(
        "data",
        {},
    )

    # ========================================================
    # Sections
    # ========================================================

    patient_info = extracted_data.get(
        "patient_info",
        {},
    )

    clinical_context = extracted_data.get(
        "clinical_context",
        {},
    )

    vital_signs = extracted_data.get(
        "vital_signs",
        {},
    )

    medical_problems = extracted_data.get(
        "medical_problems",
        {},
    )

    medications = extracted_data.get(
        "medications",
        {},
    )

    preventive_health = extracted_data.get(
        "preventive_health",
        {},
    )

    social_determinants = extracted_data.get(
        "social_determinants",
        {},
    )


    # ========================================================
    # Patient Information
    # ========================================================

    st.subheader(
        "👤 Patient Information"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.text_input(
            "Patient Name",
            value=str(
                patient_info.get(
                    "name",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Date of Birth",
            value=str(
                patient_info.get(
                    "date_of_birth",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Age",
            value=str(
                patient_info.get(
                    "age",
                    "",
                ) or ""
            ),
            disabled=True,
        )

    with col2:

        st.text_input(
            "Gender",
            value=str(
                patient_info.get(
                    "gender",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "MRN",
            value=str(
                patient_info.get(
                    "mrn",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Phone",
            value=str(
                patient_info.get(
                    "phone",
                    "",
                ) or ""
            ),
            disabled=True,
        )

    with col3:

        st.text_input(
            "Email",
            value=str(
                patient_info.get(
                    "email",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_area(
            "Address",
            value=str(
                patient_info.get(
                    "address",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Emergency Contact",
            value=str(
                patient_info.get(
                    "emergency_contact",
                    "",
                ) or ""
            ),
            disabled=True,
        )


    # ========================================================
    # Clinical Context
    # ========================================================

    st.subheader(
        "🩺 Clinical Context"
    )

    st.text_input(
        "Chief Complaint",
        value=str(
            clinical_context.get(
                "chief_complaint",
                "",
            ) or ""
        ),
        disabled=True,
    )

    st.text_input(
        "Reason for Visit",
        value=str(
            clinical_context.get(
                "reason_for_visit",
                "",
            ) or ""
        ),
        disabled=True,
    )

    medical_history = clinical_context.get(
        "medical_history",
        [],
    )

    if isinstance(
        medical_history,
        list,
    ):

        medical_history_text = "\n".join(
            f"• {item}"
            for item in medical_history
        )

    else:

        medical_history_text = str(
            medical_history or ""
        )

    st.text_area(
        "Medical History",
        value=medical_history_text,
        disabled=True,
    )

    allergies = clinical_context.get(
        "allergies",
        [],
    )

    if isinstance(
        allergies,
        list,
    ):

        allergies_text = ", ".join(
            str(item)
            for item in allergies
        )

    else:

        allergies_text = str(
            allergies or ""
        )

    st.text_input(
        "Allergies",
        value=allergies_text,
        disabled=True,
    )

    st.text_area(
        "Provider Notes",
        value=str(
            clinical_context.get(
                "provider_notes",
                "",
            ) or ""
        ),
        disabled=True,
    )


    # ========================================================
    # Vital Signs
    # ========================================================

    st.subheader(
        "❤️ Vital Signs"
    )

    v1, v2, v3, v4 = st.columns(4)

    with v1:

        st.metric(
            "Blood Pressure",
            str(
                vital_signs.get(
                    "blood_pressure",
                    "N/A",
                )
            ),
        )

    with v2:

        heart_rate = vital_signs.get(
            "heart_rate",
            "N/A",
        )

        st.metric(
            "Heart Rate",
            str(heart_rate),
        )

    with v3:

        temperature = vital_signs.get(
            "temperature",
            "N/A",
        )

        st.metric(
            "Temperature",
            str(temperature),
        )

    with v4:

        oxygen = vital_signs.get(
            "oxygen_saturation",
            "N/A",
        )

        st.metric(
            "SpO₂",
            str(oxygen),
        )


    # ========================================================
    # Additional Vital Signs
    # ========================================================

    vv1, vv2, vv3, vv4 = st.columns(4)

    with vv1:

        st.metric(
            "Respiratory Rate",
            str(
                vital_signs.get(
                    "respiratory_rate",
                    "N/A",
                )
            ),
        )

    with vv2:

        st.metric(
            "Weight",
            str(
                vital_signs.get(
                    "weight",
                    "N/A",
                )
            ),
        )

    with vv3:

        st.metric(
            "Height",
            str(
                vital_signs.get(
                    "height",
                    "N/A",
                )
            ),
        )

    with vv4:

        st.metric(
            "BMI",
            str(
                vital_signs.get(
                    "bmi",
                    "N/A",
                )
            ),
        )


    # ========================================================
    # Medical Problems
    # ========================================================

    st.subheader(
        "🏥 Medical Problems"
    )

    active_conditions = medical_problems.get(
        "active_conditions",
        [],
    )

    chronic_diseases = medical_problems.get(
        "chronic_diseases",
        [],
    )

    previous_surgeries = medical_problems.get(
        "previous_surgeries",
        [],
    )

    hospitalizations = medical_problems.get(
        "hospitalizations",
        [],
    )

    st.write(
        "**Active Conditions**"
    )

    if active_conditions:

        for condition in active_conditions:

            st.write(
                f"- {condition}"
            )

    else:

        st.write(
            "No active conditions extracted."
        )

    st.write(
        "**Chronic Diseases**"
    )

    if chronic_diseases:

        for condition in chronic_diseases:

            st.write(
                f"- {condition}"
            )

    else:

        st.write(
            "No chronic diseases extracted."
        )

    st.write(
        "**Previous Surgeries**"
    )

    if previous_surgeries:

        for surgery in previous_surgeries:

            st.write(
                f"- {surgery}"
            )

    else:

        st.write(
            "No previous surgeries extracted."
        )

    st.write(
        "**Hospitalizations**"
    )

    if hospitalizations:

        for hospitalization in hospitalizations:

            st.write(
                f"- {hospitalization}"
            )

    else:

        st.write(
            "No hospitalizations extracted."
        )


    # ========================================================
    # Medications
    # ========================================================

    st.subheader(
        "💊 Medications"
    )

    current_medications = medications.get(
        "current_medications",
        [],
    )

    if current_medications:

        for medication in current_medications:

            if isinstance(
                medication,
                dict,
            ):

                medication_text = " | ".join(
                    f"{key}: {value}"
                    for key, value
                    in medication.items()
                )

            else:

                medication_text = str(
                    medication
                )

            st.write(
                f"- {medication_text}"
            )

    else:

        st.write(
            "No medications extracted."
        )


    # ========================================================
    # Preventive Health
    # ========================================================

    st.subheader(
        "💉 Preventive Health"
    )

    p1, p2 = st.columns(2)

    with p1:

        st.text_input(
            "Vaccination Status",
            value=str(
                preventive_health.get(
                    "vaccination_status",
                    "",
                ) or ""
            ),
            disabled=True,
        )

    with p2:

        vaccinations = preventive_health.get(
            "vaccinations",
            [],
        )

        if isinstance(
            vaccinations,
            list,
        ):

            vaccinations_text = ", ".join(
                str(item)
                for item in vaccinations
            )

        else:

            vaccinations_text = str(
                vaccinations or ""
            )

        st.text_input(
            "Vaccinations",
            value=vaccinations_text,
            disabled=True,
        )


    # ========================================================
    # SDOH
    # ========================================================

    st.header(
        "🌍 Social Determinants of Health"
    )

    st.info(
        "These extracted SDOH factors can be passed "
        "to the CareEquity risk prioritization and "
        "intervention engine."
    )

    s1, s2 = st.columns(2)

    with s1:

        st.text_input(
            "Insurance Status",
            value=str(
                social_determinants.get(
                    "insurance_status",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Employment Status",
            value=str(
                social_determinants.get(
                    "employment_status",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Housing Status",
            value=str(
                social_determinants.get(
                    "housing_status",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Food Security",
            value=str(
                social_determinants.get(
                    "food_security",
                    "",
                ) or ""
            ),
            disabled=True,
        )

    with s2:

        st.text_input(
            "Education Level",
            value=str(
                social_determinants.get(
                    "education_level",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Language Spoken",
            value=str(
                social_determinants.get(
                    "language_spoken",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Transportation",
            value=str(
                social_determinants.get(
                    "transportation",
                    "",
                ) or ""
            ),
            disabled=True,
        )

        st.text_input(
            "Income Level",
            value=str(
                social_determinants.get(
                    "income_level",
                    "",
                ) or ""
            ),
            disabled=True,
        )


    # ========================================================
    # Extraction Quality
    # ========================================================

    st.subheader(
        "📊 Extraction Quality"
    )

    extraction_metadata = result.get(
        "extraction_metadata",
        {},
    )

    confidence_scores = extraction_metadata.get(
        "confidence_scores",
        {},
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        st.metric(
            "Fields Extracted",
            str(
                extraction_metadata.get(
                    "total_fields_extracted",
                    0,
                )
            ),
        )

    with q2:

        st.metric(
            "High Confidence",
            str(
                confidence_scores.get(
                    "high",
                    0,
                )
            ),
        )

    with q3:

        st.metric(
            "Medium Confidence",
            str(
                confidence_scores.get(
                    "medium",
                    0,
                )
            ),
        )

    with q4:

        page_count = extraction_metadata.get(
            "page_count",
            "N/A",
        )

        st.metric(
            "Pages",
            str(page_count),
        )


    # ========================================================
    # Document Information
    # ========================================================

    st.subheader(
        "📄 Extraction Metadata"
    )

    metadata_col1, metadata_col2 = st.columns(2)

    with metadata_col1:

        st.write(
            f"**File:** "
            f"{result.get('filename', file.name)}"
        )

        st.write(
            f"**Format:** "
            f"{result.get('file_format', file_format)}"
        )

    with metadata_col2:

        st.write(
            f"**Timestamp:** "
            f"{result.get('timestamp', 'N/A')}"
        )

        st.write(
            f"**Document Type:** "
            f"{extraction_metadata.get('document_type', 'N/A')}"
        )


    # ========================================================
    # Raw JSON
    # ========================================================

    with st.expander(
        "View Raw Extraction JSON"
    ):

        st.json(result)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.subheader(
        "⚙️ System"
    )

    st.caption(
        f"Backend: {BACKEND_URL}"
    )

    st.divider()

    if st.button(
        "Check Backend",
        use_container_width=True,
    ):

        try:

            response = requests.get(
                f"{BACKEND_URL}/health",
                timeout=5,
            )

            if response.ok:

                health_data = response.json()

                st.success(
                    "Backend is online ✓"
                )

                st.json(
                    health_data
                )

            else:

                st.error(
                    "Backend returned an error."
                )

        except requests.exceptions.RequestException as error:

            st.error(
                "Backend is unreachable."
            )

            st.caption(
                str(error)
            )