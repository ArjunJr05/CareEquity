const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
const ec2BackendIp = (hostname === 'localhost' || hostname === '127.0.0.1') ? 'localhost' : '18.60.232.212';

export const MAIN_BACKEND_URL = `http://${ec2BackendIp}:8000`;
export const SYSTEM_BACKEND_URL = `http://${ec2BackendIp}:8000`;
export const PREDICTION_BACKEND_URL = `http://${ec2BackendIp}:8002`;
export const OCR_BACKEND_URL = `http://${ec2BackendIp}:8001`;
export const RAG_BACKEND_URL = `http://${ec2BackendIp}:8002`;
export const KG_BACKEND_URL = `http://${ec2BackendIp}:8004`;
export const AGENT_BACKEND_URL = `http://${ec2BackendIp}:8003`;

export const RAZORPAY_KEY_ID = import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_TRtTOuWOsWyK15';

