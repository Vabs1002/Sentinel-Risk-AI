/**
 * SentinelRisk - Drop-In Universal Risk & Margin Defense SDK v1.2
 * Dynamically adapts to any domain or deployment environment.
 */
(function (window, document) {
  const CURRENT_ORIGIN = window.location.origin || '';
  const SENTINEL_API_URL = (CURRENT_ORIGIN.includes('vercel.app') || CURRENT_ORIGIN.includes('localhost') || CURRENT_ORIGIN.includes('127.0.0.1'))
    ? (CURRENT_ORIGIN + '/api/v1/risk/score')
    : 'https://sentinel-risk-ai.vercel.app/api/v1/risk/score';

  class SentinelRiskSDK {
    constructor() {
      this.startTime = Date.now();
      console.log('[+] SentinelRisk Universal Drop-In SDK Initialized (Active Protection)');
    }

    async evaluateOrder(orderData) {
      const dwellSeconds = (Date.now() - this.startTime) / 1000.0;
      const payload = {
        order_id: orderData.order_id || ('ORD-' + Math.floor(Math.random() * 900000 + 100000)),
        order_amount: parseFloat(orderData.amount || 1500.0),
        payment_mode: orderData.payment_mode === 'COD' ? 0 : 1,
        is_cod: orderData.payment_mode === 'COD' ? 1 : 0,
        checkout_dwell_seconds: dwellSeconds,
        pincode_historical_rto: parseFloat(orderData.pincode_rto || 0.25),
        device_order_count_24h: 1
      };

      try {
        const res = await fetch(SENTINEL_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        return await res.json();
      } catch (err) {
        return { decision: 'APPROVE', risk_score: 0.05, action_code: 'FALLBACK_PASS' };
      }
    }
  }

  window.SentinelRisk = new SentinelRiskSDK();
})(window, document);
