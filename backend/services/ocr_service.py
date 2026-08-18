"""
OCR Service Module
==================
Handles optical character recognition and data extraction from health reports.

Structure:
  - OCRProcessor: Main OCR engine (Tesseract)
  - DocumentPreprocessor: Image cleaning & preparation
  - FieldExtractor: Regex-based field extraction from OCR text
"""

import cv2
import numpy as np
import pytesseract
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: DATA CLASSES & ENUMS
# ============================================================================

class DocumentType(str, Enum):
    """Supported document types"""
    LAB_REPORT = "lab_report"
    MEDICAL_RECORD = "medical_record"
    PRESCRIPTION = "prescription"
    VITAL_SIGNS = "vital_signs"
    GENERIC = "generic"


@dataclass
class ProcessingConfig:
    """Configuration for OCR processing"""
    threshold_value: int = 127
    blur_kernel: Tuple[int, int] = (5, 5)
    dilation_iterations: int = 2
    erosion_iterations: int = 2
    tesseract_config: str = "--psm 6"  # PSM = Page Segmentation Mode


@dataclass
class PreprocessedImage:
    """Result of image preprocessing"""
    original: np.ndarray
    preprocessed: np.ndarray
    rotation_angle: float
    contrast_score: float


@dataclass
class OCRResult:
    """Result of OCR processing"""
    raw_text: str
    confidence: float
    page_num: int
    processing_time: float
    document_type: Optional[str] = None


# ============================================================================
# SECTION 2: DOCUMENT PREPROCESSOR
# ============================================================================

class DocumentPreprocessor:
    """
    Handles image preprocessing for better OCR accuracy.
    
    Operations:
      - Deskew (rotate to correct angle)
      - Denoise
      - Contrast enhancement
      - Binary thresholding
    """

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()

    def detect_rotation_angle(self, image: np.ndarray) -> float:
        """
        Detect image rotation angle using edge detection.
        
        Returns: angle in degrees (-90 to 90)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, 
                               minLineLength=50, maxLineGap=10)
        
        if lines is None or len(lines) == 0:
            return 0.0
        
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            angles.append(angle)
        
        # Median angle for robustness
        median_angle = np.median(angles)
        
        # Normalize to [-90, 90]
        if median_angle > 45:
            median_angle -= 90
        elif median_angle < -45:
            median_angle += 90
        
        return float(median_angle)

    def rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle"""
        if angle == 0:
            return image
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
        
        return rotated

    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from image"""
        denoised = cv2.fastNlMeansDenoising(image, None, h=10, 
                                            templateWindowSize=7,
                                            searchWindowSize=21)
        return denoised

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        return enhanced

    def binary_threshold(self, image: np.ndarray) -> np.ndarray:
        """Convert to binary (black and white) for better OCR"""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        _, binary = cv2.threshold(image, self.config.threshold_value, 
                                 255, cv2.THRESH_BINARY)
        return binary

    def morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """Apply erosion and dilation to clean up text"""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        dilated = cv2.dilate(image, kernel, 
                           iterations=self.config.dilation_iterations)
        eroded = cv2.erode(dilated, kernel, 
                          iterations=self.config.erosion_iterations)
        
        return eroded

    def calculate_contrast_score(self, image: np.ndarray) -> float:
        """Calculate contrast quality score (0-1)"""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Laplacian variance as contrast measure
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        
        # Normalize to 0-1 (empirically ~100 is good contrast)
        score = min(laplacian_var / 100.0, 1.0)
        
        return float(score)

    def preprocess(self, image: np.ndarray) -> PreprocessedImage:
        """
        Full preprocessing pipeline.
        
        Steps:
          1. Detect and correct rotation
          2. Denoise
          3. Enhance contrast
          4. Binary threshold
          5. Morphological operations
        """
        # Step 1: Deskew
        rotation_angle = self.detect_rotation_angle(image)
        rotated = self.rotate_image(image, rotation_angle)
        
        # Step 2: Denoise
        denoised = self.denoise(rotated)
        
        # Step 3: Enhance contrast
        enhanced = self.enhance_contrast(denoised)
        
        # Step 4: Binary threshold
        binary = self.binary_threshold(enhanced)
        
        # Step 5: Morphological operations
        processed = self.morphological_operations(binary)
        
        # Quality score
        contrast_score = self.calculate_contrast_score(image)
        
        return PreprocessedImage(
            original=image,
            preprocessed=processed,
            rotation_angle=rotation_angle,
            contrast_score=contrast_score
        )


# ============================================================================
# SECTION 3: OCR PROCESSOR
# ============================================================================

class OCRProcessor:
    """
    Main OCR processing engine using Tesseract.
    
    Handles:
      - Document segmentation
      - Text extraction with confidence
      - Multi-language support
    """

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.preprocessor = DocumentPreprocessor(config)

    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from image using Tesseract.
        
        Returns: OCRResult with text and confidence metrics
        """
        import time
        start_time = time.time()
        
        # Preprocess image
        preprocessed = self.preprocessor.preprocess(image)
        
        # OCR with Tesseract
        try:
            raw_text = pytesseract.image_to_string(
                preprocessed.preprocessed,
                config=self.config.tesseract_config
            )
            
            # Get confidence
            data = pytesseract.image_to_data(preprocessed.preprocessed)
            confidences = [int(line.split('\t')[10]) 
                          for line in data.split('\n')[1:] 
                          if len(line.split('\t')) == 12 and 
                          line.split('\t')[10] != '-1']
            
            avg_confidence = np.mean(confidences) / 100 if confidences else 0.0
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}")
            raw_text = ""
            avg_confidence = 0.0
        
        processing_time = time.time() - start_time
        
        return OCRResult(
            raw_text=raw_text,
            confidence=float(avg_confidence),
            page_num=1,
            processing_time=processing_time
        )

    def extract_from_multiple_pages(self, 
                                   image_paths: List[Path]) -> List[OCRResult]:
        """Extract text from multiple document pages"""
        results = []
        
        for page_num, image_path in enumerate(image_paths, 1):
            image = cv2.imread(str(image_path))
            if image is None:
                logger.warning(f"Could not read image: {image_path}")
                continue
            
            result = self.extract_text(image)
            result.page_num = page_num
            results.append(result)
        
        return results


# ============================================================================
# SECTION 4: FIELD EXTRACTOR
# ============================================================================

class HealthReportFieldExtractor:
    """
    Extracts specific health fields from OCR text using regex patterns.
    
    Extracts:
      - Patient demographics (name, DOB, age)
      - Vital signs (BP, HR, temp)
      - Lab values (glucose, cholesterol, HbA1c)
      - Medical history
    """

    # Define regex patterns for common health fields
    PATTERNS = {
        # Demographics
        'patient_name': r'(?:Patient|Name)[\s:]*([A-Za-z\s]+?)(?:\n|Date)',
        'date_of_birth': r'(?:DOB|Date of Birth)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'age': r'(?:Age|AGE)[\s:]*(\d{1,3})',
        'gender': r'(?:Sex|Gender)[\s:]*([MF]|Male|Female)',
        'zipcode': r'(?:Zip|Zipcode|ZIP CODE)[\s:]*(\d{5})',
        
        # Vital Signs
        'blood_pressure': r'(?:BP|Blood Pressure)[\s:]*(\d{2,3})[/-](\d{2,3})',
        'heart_rate': r'(?:HR|Heart Rate)[\s:]*(\d{2,3})',
        'temperature': r'(?:Temp|Temperature)[\s:]*(\d{2,3}\.?\d*)',
        'height': r'(?:Height)[\s:]*(\d{1,3}\.?\d*)\s*(?:cm|in)',
        'weight': r'(?:Weight)[\s:]*(\d{1,3}\.?\d*)\s*(?:kg|lbs)',
        'bmi': r'(?:BMI)[\s:]*(\d{1,2}\.?\d*)',
        
        # Lab Values
        'glucose': r'(?:Glucose|Fasting Glucose)[\s:]*(\d{2,3}\.?\d*)',
        'hba1c': r'(?:HbA1c|Hemoglobin A1c)[\s:]*(\d{1,2}\.?\d*)',
        'cholesterol': r'(?:Total Cholesterol)[\s:]*(\d{2,3}\.?\d*)',
        'ldl': r'(?:LDL)[\s:]*(\d{2,3}\.?\d*)',
        'hdl': r'(?:HDL)[\s:]*(\d{2,3}\.?\d*)',
        'triglycerides': r'(?:Triglycerides)[\s:]*(\d{2,3}\.?\d*)',
        
        # Medical History
        'diabetes': r'(?:Diabetes|Diabetic)[\s:]*([Yy]es|[Nn]o|Type\s*[12])',
        'hypertension': r'(?:Hypertension|High Blood Pressure)[\s:]*([Yy]es|[Nn]o)',
        'smoking': r'(?:Smoking|Smoker)[\s:]*([Yy]es|[Nn]o|Former|Never|Current)',
    }

    @staticmethod
    def extract_fields(text: str) -> Dict[str, Any]:
        """
        Extract health fields from OCR text.
        
        Returns: Dictionary of extracted fields with values and confidence
        """
        extracted = {}
        
        for field_name, pattern in HealthReportFieldExtractor.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                if isinstance(matches[0], tuple):
                    # Multiple capture groups
                    extracted[field_name] = matches[0]
                else:
                    # Single capture group
                    extracted[field_name] = matches[0]
        
        return extracted

    @staticmethod
    def normalize_field(field_name: str, value: str) -> Any:
        """
        Normalize extracted field values to proper types.
        
        Converts strings to appropriate types (int, float, bool, etc.)
        """
        value = value.strip() if isinstance(value, str) else value
        
        # Boolean fields
        if field_name in ['diabetes', 'hypertension', 'smoking']:
            if isinstance(value, str):
                if value.lower() in ['yes', 'true', 'y']:
                    return True
                elif value.lower() in ['no', 'false', 'n']:
                    return False
            return value
        
        # Numeric fields
        if field_name in ['age', 'heart_rate', 'temperature', 'height', 
                         'weight', 'bmi', 'glucose', 'hba1c', 'cholesterol',
                         'ldl', 'hdl', 'triglycerides']:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        # Date fields
        if field_name == 'date_of_birth':
            return value  # Return as-is for now, format separately
        
        return value


# ============================================================================
# SECTION 5: MAIN OCR PIPELINE
# ============================================================================

class OCRPipeline:
    """
    Complete OCR pipeline orchestrator.
    
    Workflow:
      1. Load document image
      2. Preprocess for OCR quality
      3. Extract text with Tesseract
      4. Parse health-specific fields
      5. Normalize and validate
    """

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.ocr_processor = OCRProcessor(config)
        self.field_extractor = HealthReportFieldExtractor()

    def process_document(self, image_path: str) -> Dict[str, Any]:
        """
        Process a single document end-to-end.
        
        Args:
            image_path: Path to document image
        
        Returns:
            Dictionary with extracted fields, raw text, and metadata
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # OCR
        ocr_result = self.ocr_processor.extract_text(image)
        
        # Extract fields
        raw_fields = self.field_extractor.extract_fields(ocr_result.raw_text)
        
        # Normalize fields
        normalized_fields = {
            field: self.field_extractor.normalize_field(field, value)
            for field, value in raw_fields.items()
        }
        
        return {
            'raw_text': ocr_result.raw_text,
            'extracted_fields': normalized_fields,
            'confidence': ocr_result.confidence,
            'rotation_angle': self.ocr_processor.preprocessor
                                   .detect_rotation_angle(image),
            'processing_time': ocr_result.processing_time,
            'source_file': image_path
        }

    def process_multiple_documents(self, image_paths: List[str]) -> List[Dict]:
        """Process multiple document pages"""
        results = []
        
        for image_path in image_paths:
            try:
                result = self.process_document(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {str(e)}")
                results.append({
                    'error': str(e),
                    'source_file': image_path
                })
        
        return results
