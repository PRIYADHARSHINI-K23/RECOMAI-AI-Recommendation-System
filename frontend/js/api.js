/**
 * RECOMAI API Client
 * Centralized fetch handler for REST endpoints with JWT authentication.
 */

const API_BASE = '/api/v1';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('recomai_token') || null;
    this.user = JSON.parse(localStorage.getItem('recomai_user') || 'null');
  }

  setAuth(token, user) {
    this.token = token;
    this.user = user;
    if (token) {
      localStorage.setItem('recomai_token', token);
      localStorage.setItem('recomai_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('recomai_token');
      localStorage.removeItem('recomai_user');
    }
  }

  clearAuth() {
    this.setAuth(null, null);
  }

  isAuthenticated() {
    return !!this.token;
  }

  isAdmin() {
    return this.user && this.user.role === 'admin';
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      // Auto logout on 401
      if (response.status === 401 && this.token) {
        this.clearAuth();
        window.dispatchEvent(new CustomEvent('recomai:auth-expired'));
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = data && (data.detail || data.message) ? (data.detail || data.message) : `HTTP ${response.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // Auth endpoints
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: { email, password }
    });
    this.setAuth(data.access_token, data.user);
    return data;
  }

  async register(payload) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: payload
    });
    this.setAuth(data.access_token, data.user);
    return data;
  }

  async getMe() {
    return this.request('/auth/me');
  }

  async updatePreferences(preferences) {
    const updatedUser = await this.request('/auth/preferences', {
      method: 'PUT',
      body: preferences
    });
    this.user = updatedUser;
    localStorage.setItem('recomai_user', JSON.stringify(updatedUser));
    return updatedUser;
  }

  // Items & Categories endpoints
  async getCategories() {
    return this.request('/items/categories');
  }

  async getItems(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    return this.request(`/items?${query.toString()}`);
  }

  async getItem(id) {
    return this.request(`/items/${id}`);
  }

  // Recommendations endpoints
  async getDashboardRecommendations() {
    return this.request('/recommendations/dashboard');
  }

  async getFeed(strategy = 'hybrid', limit = 15) {
    return this.request(`/recommendations/feed?strategy=${strategy}&limit=${limit}`);
  }

  async getRelatedRecommendations(itemId) {
    return this.request(`/recommendations/item/${itemId}/related`);
  }

  async getEngineStatus() {
    return this.request('/recommendations/status');
  }

  // Semantic Search
  async semanticSearch(query, filters = {}) {
    const params = new URLSearchParams({ q: query });
    if (filters.category_id) params.append('category_id', filters.category_id);
    if (filters.difficulty) params.append('difficulty', filters.difficulty);
    return this.request(`/search?${params.toString()}`);
  }

  // Interactions endpoints
  async recordInteraction(itemId, type, dwellTime = 0.0) {
    return this.request('/interactions', {
      method: 'POST',
      body: { item_id: itemId, interaction_type: type, dwell_time_seconds: dwellTime }
    });
  }

  async toggleLike(itemId) {
    return this.request(`/interactions/like/${itemId}`, { method: 'POST' });
  }

  async toggleFavorite(itemId) {
    return this.request(`/interactions/favorite/${itemId}`, { method: 'POST' });
  }

  async submitRating(itemId, score, review = null) {
    return this.request('/interactions/rate', {
      method: 'POST',
      body: { item_id: itemId, score, review }
    });
  }

  async getFavorites() {
    return this.request('/interactions/favorites');
  }

  // AI Insights
  async getUserInsights() {
    return this.request('/insights/me');
  }

  // Admin Portal
  async getAdminAnalytics() {
    return this.request('/admin/analytics');
  }

  async getAdminItems() {
    return this.request('/admin/items');
  }

  async createAdminItem(payload) {
    return this.request('/admin/items', {
      method: 'POST',
      body: payload
    });
  }

  async updateAdminItem(id, payload) {
    return this.request(`/admin/items/${id}`, {
      method: 'PUT',
      body: payload
    });
  }

  async deleteAdminItem(id) {
    return this.request(`/admin/items/${id}`, { method: 'DELETE' });
  }

  // Admin — Category Management
  async getAdminCategories() {
    try {
      const data = await this.request('/admin/categories');
      if (Array.isArray(data) && data.length) return data;
    } catch (err) {
      console.warn('Admin categories endpoint notice, falling back to catalog categories:', err);
    }
    return this.getCategories();
  }

  async createAdminCategory(payload) {
    return this.request('/admin/categories', {
      method: 'POST',
      body: payload
    });
  }

  async updateAdminCategory(id, payload) {
    return this.request(`/admin/categories/${id}`, {
      method: 'PUT',
      body: payload
    });
  }

  async deleteAdminCategory(id) {
    return this.request(`/admin/categories/${id}`, { method: 'DELETE' });
  }

  // Admin — User Management
  async getAdminUsers() {
    return this.request('/admin/users');
  }

  async deleteAdminUser(id) {
    return this.request(`/admin/users/${id}`, { method: 'DELETE' });
  }
}

window.api = new ApiClient();
