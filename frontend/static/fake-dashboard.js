/**
 * Fake Dashboard Bootstrapper
 * - Starts / stops synthetic telemetry streaming on the backend
 * - Uses the existing JWT token in localStorage
 */

(function () {
  const token = localStorage.getItem('access_token');
  if (!token) return;

  const API_URL = `${window.location.protocol}//${window.location.host}`;

  async function startFake() {
    try {
      const res = await fetch(`${API_URL}/api/demo/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device_id: window.userDeviceId || undefined }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      console.log('[FakeDashboard] started:', data);
    } catch (e) {
      console.error('[FakeDashboard] start failed:', e);
      alert('Failed to start fake data. Open console for details.');
    }
  }

  async function stopFake() {
    try {
      const res = await fetch(`${API_URL}/api/demo/stop`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      console.log('[FakeDashboard] stopped:', data);
    } catch (e) {
      console.error('[FakeDashboard] stop failed:', e);
      alert('Failed to stop fake data. Open console for details.');
    }
  }

  // Expose for manual testing
  window.FakeDashboard = { startFake, stopFake };
})();

