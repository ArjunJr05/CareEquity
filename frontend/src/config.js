const isLocal = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

export const MAIN_BACKEND_URL = isLocal 
  ? 'http://localhost:8000' 
  : 'https://careequity-main-backend.onrender.com';

export const SYSTEM_BACKEND_URL = isLocal 
  ? 'http://localhost:8000' 
  : 'https://careequity-system-backend.onrender.com';

export const PREDICTION_BACKEND_URL = isLocal 
  ? 'http://localhost:8002' 
  : 'https://careequity-prediction-model.onrender.com';

export const RAZORPAY_KEY_ID = import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_TRtTOuWOsWyK15';
