const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

export const MAIN_BACKEND_URL = `http://${hostname}:8000`;
export const SYSTEM_BACKEND_URL = `http://${hostname}:8000`;
export const PREDICTION_BACKEND_URL = `http://${hostname}:8002`;
export const OCR_BACKEND_URL = `http://${hostname}:8001`;
export const RAG_BACKEND_URL = `http://${hostname}:8002`;
export const KG_BACKEND_URL = `http://${hostname}:8004`;
export const AGENT_BACKEND_URL = `http://${hostname}:8003`;

export const RAZORPAY_KEY_ID = import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_TRtTOuWOsWyK15';

