import re

from .parser_generic import (
    MedicalDocParser,
    ExtractionResult,
    PatientInfo,
    ClinicalContext,
    VitalSigns,
    MedicalProblems,
    Medications,
    PreventiveHealth,
    SocialDeterminants,
)


class PatientDetailsParser(MedicalDocParser):
    """
    Extract comprehensive patient information
    from a medical document.
    """

    def parse(self) -> ExtractionResult:

        patient_info = self._parse_patient_info()

        clinical_context = self._parse_clinical_context()

        vital_signs = self._parse_vital_signs()

        medical_problems = self._parse_medical_problems()

        medications = self._parse_medications()

        preventive_health = self._parse_preventive_health()

        social_determinants = self._parse_social_determinants()

        return ExtractionResult(
            patient_info=patient_info,
            clinical_context=clinical_context,
            vital_signs=vital_signs,
            medical_problems=medical_problems,
            medications=medications,
            preventive_health=preventive_health,
            social_determinants=social_determinants,
            metadata=self.get_metadata(),
            document_type="patient_details",
        )

    # =========================================================
    # Patient Information
    # =========================================================

    def _parse_patient_info(self):

        # Extract patient name - look for specific patterns (NOT generic "Name")
        name, _, _ = self.extract_with_confidence(
            "patient_name",
            r"Patient\s*Name\s*\|\s*([A-Z][a-zA-Z\s.'-]+?)(?:\s*\||$)",
            processor=lambda x: x.strip() if x and len(x) > 1 and not any(kw in x.lower() for kw in ['admission', 'discharge', 'date']) else None,
        )

        # Extract DOB - specific format
        dob, _, _ = self.extract_with_confidence(
            "date_of_birth",
            r"DOB\s*\|\s*(\d{1,2}/\d{1,2}/\d{4})",
            processor=lambda x: x.strip() if x else None,
        )

        # Extract age - must be reasonable (1-150)
        age, _, _ = self.extract_with_confidence(
            "age",
            r"Age\s*/?\s*Sex\s*\|\s*(\d{1,3})\s*Years",
            processor=lambda x: int(x.strip()) if x and x.strip().isdigit() and 1 <= int(x.strip()) <= 150 else None,
        )

        # Extract gender - specific context
        gender, _, _ = self.extract_with_confidence(
            "gender",
            r"Age\s*/?\s*Sex\s*\|\s*\d+\s*Years\s*/\s*(Male|Female|M|F)",
            processor=lambda x: x.strip() if x else None,
        )

        # Extract MRN/UHID - specific format
        mrn, _, _ = self.extract_with_confidence(
            "mrn",
            r"(?:UHID|MRN)\s*\|\s*([A-Z0-9-]+)",
            processor=lambda x: x.strip() if x and len(x) > 2 else None,
        )

        # Extract phone - digits only pattern
        phone, _, _ = self.extract_with_confidence(
            "phone",
            r"Phone\s*\|\s*(\d{10,}|\+\d{1,3}\s*\d{6,})",
            processor=lambda x: x.strip() if x else None,
        )

        # Extract email - must contain @ and domain
        email, _, _ = self.extract_with_confidence(
            "email",
            r"Email\s*\|\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            processor=lambda x: x.strip() if x else None,
        )

        # Extract address - specific context
        address, _, _ = self.extract_with_confidence(
            "address",
            r"Address\s*\|\s*([^\n|]+(?:Chennai|Mumbai|Delhi|Bangalore|Hyderabad)[^\n|]*)",
            processor=lambda x: x.strip() if x and len(x) > 5 else None,
        )

        return PatientInfo(
            name=name,
            date_of_birth=dob,
            age=age,
            gender=gender,
            mrn=mrn,
            phone=phone,
            email=email,
            address=address,
        )

    # =========================================================
    # Clinical Context
    # =========================================================

    def _parse_clinical_context(self):

        # Chief complaint - look for specific section headers
        chief_complaint, _, _ = self.extract_with_confidence(
            "chief_complaint",
            r"Chief\s*Complaint\s*\|\s*([^\n|]+?)(?:\||$)",
            processor=lambda x: x.strip() if x and len(x) > 3 and 'admission' not in x.lower() else None,
        )

        reason_for_visit, _, _ = self.extract_with_confidence(
            "reason_for_visit",
            r"Reason\s*for\s*Visit\s*\|\s*([^\n|]+?)(?:\||$)",
            processor=lambda x: x.strip() if x and len(x) > 3 else None,
        )

        # Medical history - extract full history section
        medical_history, _, _ = self.extract_with_confidence(
            "medical_history",
            r"(?:OF\s*PRESENT\s*ILLNESS|PAST\s*HISTORY|HISTORY)\s*\n([^A-Z]*?)(?=\n[A-Z\s]{2,}:|$)",
            processor=lambda x: self._extract_conditions(x) if x else None,
        )

        # Current medications - extract from discharge advice or medications section
        current_meds, _, _ = self.extract_with_confidence(
            "current_medications",
            r"(?:MEDICATIONS|Medications|Tab\.\s)([^A-Z]*?)(?=\n\n|$)",
            processor=lambda x: self._extract_medications_list(x) if x else None,
        )

        # Allergies - specific section
        allergies, _, _ = self.extract_with_confidence(
            "allergies",
            r"(?:Allergies|ALLERGIES|Drug\s*Allergies)\s*\n([^\n]+)",
            processor=lambda x: [x.strip()] if x and x.strip() and 'no' not in x.lower() else None,
        )

        provider_notes, _, _ = self.extract_with_confidence(
            "provider_notes",
            r"(?:ADVICE|ADVICE ON DISCHARGE|Assessment)\s*\n([^A-Z]*?)(?=\n[A-Z\s]{2,}:|$)",
            processor=lambda x: x.strip()[:500] if x and len(x) > 10 else None,
        )

        return ClinicalContext(
            chief_complaint=chief_complaint,
            reason_for_visit=reason_for_visit,
            medical_history=medical_history,
            current_medications=current_meds,
            allergies=allergies,
            provider_notes=provider_notes,
        )

    # =========================================================
    # Vital Signs
    # =========================================================

    def _parse_vital_signs(self):

        # Blood pressure - specific format with | separator
        bp, _, _ = self.extract_with_confidence(
            "blood_pressure",
            r"(?:BP|Blood\s*Pressure|Vitals)\s*\|\s*(\d{2,3}/\d{2,3})",
            processor=lambda x: x.strip() if x else None,
        )

        # Heart rate - standalone number after HR or Pulse
        hr, _, _ = self.extract_with_confidence(
            "heart_rate",
            r"Pulse\s*(\d{2,3})/min",
            processor=lambda x: int(x.strip()) if x and x.strip().isdigit() and 40 <= int(x.strip()) <= 200 else None,
        )

        # Temperature - specific Fahrenheit format
        temp, _, _ = self.extract_with_confidence(
            "temperature",
            r"Temp\s*(\d{2,3}(?:\.\d{1,2})?)°?F",
            processor=lambda x: float(x.strip()) if x and 95 <= float(x.strip()) <= 106 else None,
        )

        # Respiratory rate - specific format
        rr, _, _ = self.extract_with_confidence(
            "respiratory_rate",
            r"RR\s*(\d{1,2})/min",
            processor=lambda x: int(x.strip()) if x and x.strip().isdigit() and 8 <= int(x.strip()) <= 40 else None,
        )

        # Oxygen saturation - percentage format
        o2, _, _ = self.extract_with_confidence(
            "oxygen_saturation",
            r"(?:O2|SpO2|Oxygen\s*Saturation)\s*(\d{2,3})%?",
            processor=lambda x: float(x.strip()) if x and 70 <= float(x.strip()) <= 100 else None,
        )

        # Weight - specific kg format
        weight, _, _ = self.extract_with_confidence(
            "weight",
            r"(?:Weight|Wt)\s*(\d{2,3}(?:\.\d{1,2})?)\s*kg",
            processor=lambda x: float(x.strip()) if x and 20 <= float(x.strip()) <= 300 else None,
        )

        # Height - cm or inches
        height, _, _ = self.extract_with_confidence(
            "height",
            r"Height\s*([0-9.]+\s*(?:cm|m|feet|inches|ft))",
            processor=lambda x: x.strip() if x else None,
        )

        # BMI - calculated value
        bmi, _, _ = self.extract_with_confidence(
            "bmi",
            r"BMI\s*~?\s*(\d{2}(?:\.\d{1,2})?)",
            processor=lambda x: float(x.strip()) if x and 10 <= float(x.strip()) <= 60 else None,
        )

        return VitalSigns(
            blood_pressure=bp,
            heart_rate=hr,
            temperature=temp,
            respiratory_rate=rr,
            oxygen_saturation=o2,
            weight=weight,
            height=height,
            bmi=bmi,
        )

    # =========================================================
    # Medical Problems
    # =========================================================

    def _parse_medical_problems(self):

        active_conditions, _, _ = self.extract_with_confidence(
            "active_conditions",
            r"(?:Active\s*Conditions|Current\s*Problems|Medical\s*Problems)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        chronic_diseases, _, _ = self.extract_with_confidence(
            "chronic_diseases",
            r"(?:Chronic\s*Diseases|Chronic\s*Conditions)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        surgeries, _, _ = self.extract_with_confidence(
            "previous_surgeries",
            r"(?:Surgical\s*History|Previous\s*Surgeries|Surgeries)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        hospitalizations, _, _ = self.extract_with_confidence(
            "hospitalizations",
            r"(?:Hospitalizations|Hospital\s*History|Recent\s*Hospitalizations)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        return MedicalProblems(
            active_conditions=active_conditions,
            chronic_diseases=chronic_diseases,
            previous_surgeries=surgeries,
            hospitalizations=hospitalizations,
        )

    # =========================================================
    # Medications
    # =========================================================

    def _parse_medications(self):

        current_meds, _, _ = self.extract_with_confidence(
            "medications",
            r"(?:Current\s*Medications|Medications)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        allergies, _, _ = self.extract_with_confidence(
            "medication_allergies",
            r"(?:Allergies|Drug\s*Allergies|NKDA)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        adverse_reactions, _, _ = self.extract_with_confidence(
            "adverse_reactions",
            r"(?:Adverse\s*Reactions|Adverse\s*Events)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        return Medications(
            current_medications=current_meds,
            allergies=allergies,
            adverse_reactions=adverse_reactions,
        )

    # =========================================================
    # Preventive Health
    # =========================================================

    def _parse_preventive_health(self):

        vax_status, _, _ = self.extract_with_confidence(
            "vaccination_status",
            r"(?:Vaccination\s*Status|Up-to-date|Vaccinated)[\s:]*\n?(Yes|No|Partial|Unknown)",
            processor=lambda x: x.strip(),
        )

        vaccinations, _, _ = self.extract_with_confidence(
            "vaccinations",
            r"(?:Vaccinations|Immunizations|Vaccines)[\s:]*\n?([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|$)",
            processor=self._to_list,
        )

        return PreventiveHealth(
            vaccination_status=vax_status,
            vaccinations=vaccinations,
        )

    # =========================================================
    # SDOH
    # =========================================================

    def _parse_social_determinants(self):

        # Insurance - specific context from SDOH section
        insurance_status, _, _ = self.extract_with_confidence(
            "insurance_status",
            r"(?:Insurance|Insurance\s*Status)\s*\|\s*(Yes|No|Unknown|Uninsured|Underinsured)",
            processor=lambda x: x.strip() if x else None,
        )

        # Employment - from specific section
        employment, _, _ = self.extract_with_confidence(
            "employment_status",
            r"(?:Employment|Occupation|Employment\s*Status)\s*\|\s*([^\n|]+)",
            processor=lambda x: x.strip() if x and len(x) > 2 and 'admission' not in x.lower() else None,
        )

        # Housing - specific socioeconomic status
        housing, _, _ = self.extract_with_confidence(
            "housing_status",
            r"(?:Housing|Living\s*Situation|Socio-Economic\s*Status)\s*\|\s*(Stable|Unstable|Homeless|Class\s*[IVX]+|[^\n|]+)",
            processor=lambda x: x.strip() if x else None,
        )

        # Food security - specific indicator
        food_security, _, _ = self.extract_with_confidence(
            "food_security",
            r"Food\s*Security\s*\|\s*(Secure|Insecure|Unknown)",
            processor=lambda x: x.strip() if x else None,
        )

        # Education - NOT generic "are essential"
        education, _, _ = self.extract_with_confidence(
            "education_level",
            r"(?:Education|Education\s*Level)\s*\|\s*([^\n|]+?)(?:\||$)",
            processor=lambda x: x.strip() if x and len(x) > 2 and x.strip().lower() not in ['are essential.', ''] else None,
        )

        # Language
        language, _, _ = self.extract_with_confidence(
            "language_spoken",
            r"(?:Language|Primary\s*Language)\s*\|\s*([^\n|]+?)(?:\||$)",
            processor=lambda x: x.strip() if x and len(x) > 2 else None,
        )

        # Transportation - yes/no or availability
        transportation, _, _ = self.extract_with_confidence(
            "transportation",
            r"Transportation\s*\|\s*(Yes|No|Limited|Unknown)",
            processor=lambda x: x.strip() if x else None,
        )

        # Income level
        income, _, _ = self.extract_with_confidence(
            "income_level",
            r"(?:Income|Income\s*Level)\s*\|\s*([^\n|]+?)(?:\||$)",
            processor=lambda x: x.strip() if x and len(x) > 2 else None,
        )

        return SocialDeterminants(
            insurance_status=insurance_status,
            employment_status=employment,
            housing_status=housing,
            food_security=food_security,
            education_level=education,
            language_spoken=language,
            transportation=transportation,
            income_level=income,
        )

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _to_list(value):
        """Convert delimited text to list."""
        if not value:
            return None

        items = re.split(r"[,;\n]", value)
        items = [
            item.strip(" -•\t")
            for item in items
            if item.strip(" -•\t")
        ]
        return items or None

    @staticmethod
    def _extract_conditions(text):
        """Extract medical conditions from narrative text."""
        if not text:
            return None
        
        # Split by common delimiters and clean
        lines = re.split(r'[\n,;]', text)
        conditions = []
        for line in lines:
            line = line.strip(' -•\t')
            # Filter out section headers and very short items
            if line and len(line) > 5 and not any(kw in line.upper() for kw in ['HISTORY', 'EXAMINATION', 'INVESTIGATION']):
                conditions.append(line)
        
        return conditions[:10] if conditions else None  # Limit to 10 items

    @staticmethod
    def _extract_medications_list(text):
        """Extract medications from prescription text."""
        if not text:
            return None
        
        # Look for Tab., Inj., patterns
        meds = re.findall(r'Tab\.\s+([^\n,]+?)(?:\s+\d+\s*(?:mg|ml|%)|[\n,]|$)', text)
        meds.extend(re.findall(r'Inj\.\s+([^\n,]+?)(?:\s+\d+\s*(?:mg|ml|%)|[\n,]|$)', text))
        
        cleaned = []
        for med in meds:
            med = med.strip()
            if med and len(med) > 2:
                cleaned.append(med)
        
        return cleaned[:15] if cleaned else None  # Limit to 15 medications