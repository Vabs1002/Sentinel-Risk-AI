/**
 * SentinelRisk Drop-In Checkout Protection SDK v2.0
 * Collects real device behavioral signals at checkout:
 *   - Canvas fingerprint hash (GPU/font rendering identity)
 *   - WebGL renderer string (hardware GPU identifier)
 *   - Checkout dwell velocity (time-on-page before submitting)
 *   - Screen resolution + color depth
 *   - Timezone-based address entropy estimate
 *
 * Include one line in your checkout page:
 *   <script src="https://sentinel-risk-ai.vercel.app/sentinel.js"></script>
 *
 * Then call: const result = await window.SentinelRisk.evaluateOrder({ amount, payment_mode, ... })
 */
(function (window, document) {
  const CURRENT_ORIGIN = window.location.origin || '';
  const SENTINEL_API_URL = (
    CURRENT_ORIGIN.includes('vercel.app') ||
    CURRENT_ORIGIN.includes('localhost') ||
    CURRENT_ORIGIN.includes('127.0.0.1')
  )
    ? (CURRENT_ORIGIN + '/api/v1/risk/score')
    : 'https://sentinel-risk-ai.vercel.app/api/v1/risk/score';

  function getCanvasFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.textBaseline = 'alphabetic';
      ctx.font = '14px Arial, sans-serif';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText('SentinelRisk \u2713', 2, 15);
      ctx.fillStyle = 'rgba(102, 204, 0, 0.8)';
      ctx.fillText('Device Signal', 4, 18);
      const raw = canvas.toDataURL();
      let h = 0;
      for (let i = 0; i < raw.length; i++) {
        h = Math.imul(31, h) + raw.charCodeAt(i) | 0;
      }
      return Math.abs(h);
    } catch (e) {
      return 0;
    }
  }

  function getWebGLRenderer() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return '';
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL).substring(0, 64) : '';
    } catch (e) {
      return '';
    }
  }

  function getAddressEntropy() {
    // Timezone + screen profile gives a legitimate-user signal
    // Indian timezone + standard screen = higher entropy (more legitimate)
    const tz = (Intl && Intl.DateTimeFormat) ? Intl.DateTimeFormat().resolvedOptions().timeZone : '';
    const isIndianTz = tz.includes('Kolkata') || tz.includes('India');
    const screenSig = window.screen.width * window.screen.height * window.screen.colorDepth;
    const base = isIndianTz ? 0.70 : 0.42;
    const noise = (screenSig % 100) / 1000;
    return Math.min(0.99, parseFloat((base + noise).toFixed(3)));
  }

  class SentinelRiskSDK {
    constructor() {
      this.startTime = Date.now();
      this.canvasHash = getCanvasFingerprint();
      this.webglRenderer = getWebGLRenderer();
      this.addressEntropy = getAddressEntropy();
      this.screenProfile = window.screen.width + 'x' + window.screen.height + 'x' + window.screen.colorDepth;
      console.log('[SentinelRisk v2.0] Active Protection Initialized');
    }

    async evaluateOrder(orderData) {
      const dwellSeconds = parseFloat(((Date.now() - this.startTime) / 1000).toFixed(1));
      const payload = {
        order_id:                orderData.order_id || ('ORD-' + (Math.random() * 900000 + 100000 | 0)),
        order_amount:            parseFloat(orderData.amount || 1500.0),
        payment_mode:            orderData.payment_mode === 'COD' ? 0 : 1,
        is_cod:                  orderData.payment_mode === 'COD' ? 1 : 0,
        checkout_dwell_seconds:  dwellSeconds,
        pincode_historical_rto:  parseFloat(orderData.pincode_rto || 0.25),
        device_order_count_24h:  parseInt(orderData.device_count || 1),
        device_unique_vpa_count: parseInt(orderData.vpa_count || 1),
        address_entropy:         this.addressEntropy,
        cart_item_count:         parseInt(orderData.cart_items || 1),
        hour_of_day:             new Date().getHours(),
        ip_reputation_risk:      parseFloat(orderData.ip_risk || 0.05),
        category_risk:           parseFloat(orderData.category_risk || 0.25),
        phone_carrier_risk:      parseFloat(orderData.carrier_risk || 0.05),
        distance_km:             parseFloat(orderData.distance_km || 80.0),
        user_order_count:        parseInt(orderData.user_order_count || 1),
        user_historical_rto:     parseFloat(orderData.user_rto || 0.0),
      };

      try {
        const res = await fetch(SENTINEL_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        return await res.json();
      } catch (err) {
        // Fail open — never block checkout on SDK error
        return { decision: 'APPROVE', risk_score: 0.05, action_code: 'FALLBACK_PASS' };
      }
    }
  }

  window.SentinelRisk = new SentinelRiskSDK();
})(window, document);
