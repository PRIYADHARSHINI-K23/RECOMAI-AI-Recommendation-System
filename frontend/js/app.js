/**
 * RECOMAI - Master Client Application Router & State Manager
 * Coordinates all 16 views, interactive cards, modals, and telemetry.
 * Polished for Final-Year CSE Project Review & Portfolio Demonstration.
 */

(function() {
  'use strict';

  // Reliable fallback image for engineering curricula
  const DEFAULT_RESOURCE_IMAGE = 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80';

  class RecomaiApp {
    constructor() {
      this.currentView = 'landing';
      this.activeCategoryFilter = '';
      this.activeDifficultyFilter = '';
      this.activeSortFilter = 'popular';
      this.categories = [];
      this.selectedItemForModal = null;
      
      this.init();
    }

    async init() {
      this.bindEvents();
      this.updateAuthUI();
      
      // Load categories for filters and chips
      await this.loadCategories();

      // Initial view routing
      if (window.api.isAuthenticated()) {
        this.navigate('dashboard');
      } else {
        this.navigate('landing');
      }

      // Populate landing page live previews
      this.loadLandingPreviews();
    }

    // =========================================================================
    // ROUTING & NAVIGATION
    // =========================================================================
    navigate(viewName) {
      // Guard protected routes
      const protectedViews = ['dashboard', 'favorites', 'profile', 'insights'];
      if (protectedViews.includes(viewName) && !window.api.isAuthenticated()) {
        this.showToast('Please sign in to access this personalized section', 'info');
        this.openAuthModal('login');
        return;
      }

      if (viewName === 'admin-dashboard' && !window.api.isAdmin()) {
        this.showToast('Administrative privileges required', 'error');
        this.navigate('dashboard');
        return;
      }

      // Deactivate all views
      document.querySelectorAll('.app-view').forEach(el => el.classList.remove('active'));

      // Activate target view
      const targetViewEl = document.getElementById(`view-${viewName}`);
      if (targetViewEl) {
        targetViewEl.classList.add('active');
        this.currentView = viewName;
      }

      // Update Nav Link States
      document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.view === viewName);
      });

      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });

      // View-specific data loader hooks
      this.onViewActivated(viewName);
    }

    async onViewActivated(viewName) {
      if (viewName === 'dashboard') {
        await this.loadDashboardFeeds();
      } else if (viewName === 'discover') {
        await this.loadDiscoverItems();
      } else if (viewName === 'favorites') {
        await this.loadFavorites();
      } else if (viewName === 'profile') {
        await this.loadProfileData();
      } else if (viewName === 'insights') {
        await this.loadInsights();
      } else if (viewName === 'admin-dashboard') {
        await this.loadAdminPortal();
      }
    }

    // =========================================================================
    // UI EVENT LISTENERS
    // =========================================================================
    bindEvents() {
      // Data-view navigation buttons
      document.querySelectorAll('[data-view]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const target = btn.dataset.view;
          this.navigate(target);
          document.getElementById('user-dropdown-menu')?.classList.remove('show');
        });
      });

      // Brand Logo click -> Home or Dashboard
      document.getElementById('brand-logo-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigate(window.api.isAuthenticated() ? 'dashboard' : 'landing');
      });

      // Global Search input (Enter key)
      const globalSearch = document.getElementById('global-search-input');
      globalSearch?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const q = globalSearch.value.trim();
          if (q) {
            this.executeSemanticSearch(q);
          }
        }
      });

      // ⌘K / Ctrl+K keyboard shortcut for search
      window.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
          e.preventDefault();
          globalSearch?.focus();
        }
      });

      // User avatar dropdown toggle
      const avatarBtn = document.getElementById('user-avatar-btn');
      const dropdownMenu = document.getElementById('user-dropdown-menu');
      avatarBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu?.classList.toggle('show');
      });
      window.addEventListener('click', () => dropdownMenu?.classList.remove('show'));

      // Auth modal triggers
      document.getElementById('btn-login-open')?.addEventListener('click', () => this.openAuthModal('login'));
      document.getElementById('btn-register-open')?.addEventListener('click', () => this.openAuthModal('register'));
      document.getElementById('hero-get-started-btn')?.addEventListener('click', () => this.openAuthModal('register'));
      document.getElementById('cta-register-btn')?.addEventListener('click', () => this.openAuthModal('register'));
      document.getElementById('btn-close-auth-modal')?.addEventListener('click', () => this.closeModal('modal-auth'));
      
      // Explore Demo buttons
      const handleDemoLogin = async () => {
        if (window.api.isAuthenticated()) {
          this.navigate('dashboard');
        } else {
          await this.handleLogin('demo@recomai.io', 'Demo@123');
        }
      };
      document.getElementById('hero-explore-demo-btn')?.addEventListener('click', handleDemoLogin);
      document.getElementById('cta-demo-login-btn')?.addEventListener('click', handleDemoLogin);

      // In-modal Demo Access buttons
      document.getElementById('btn-demo-student')?.addEventListener('click', async () => {
        await this.handleLogin('demo@recomai.io', 'Demo@123');
      });
      document.getElementById('btn-demo-admin')?.addEventListener('click', async () => {
        await this.handleLogin('admin@recomai.io', 'Admin@123');
      });

      // Switch between Login and Register views in auth modal
      document.getElementById('switch-to-register')?.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchAuthMode('register');
      });
      document.getElementById('switch-to-login')?.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchAuthMode('login');
      });

      // Login Form Submit
      document.getElementById('form-login')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const pass = document.getElementById('login-password').value;
        await this.handleLogin(email, pass);
      });

      // Register Form Submit
      document.getElementById('form-register')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const full_name = document.getElementById('reg-fullname').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const role = document.getElementById('reg-role').value;
        await this.handleRegister({ full_name, email, password, role });
      });

      // Logout
      document.getElementById('btn-logout')?.addEventListener('click', () => {
        window.api.clearAuth();
        this.updateAuthUI();
        this.showToast('You have been signed out', 'info');
        this.navigate('landing');
      });

      // Onboarding Form Submit
      document.getElementById('form-onboarding')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleOnboardingSubmit();
      });

      // Discover Toolbar Filters
      document.getElementById('discover-search-input')?.addEventListener('input', this.debounce(() => {
        this.loadDiscoverItems();
      }, 320));

      document.getElementById('filter-category')?.addEventListener('change', (e) => {
        this.activeCategoryFilter = e.target.value;
        this.loadDiscoverItems();
      });
      document.getElementById('filter-difficulty')?.addEventListener('change', (e) => {
        this.activeDifficultyFilter = e.target.value;
        this.loadDiscoverItems();
      });
      document.getElementById('filter-sort')?.addEventListener('change', (e) => {
        this.activeSortFilter = e.target.value;
        this.loadDiscoverItems();
      });

      // Dashboard Feed Strategy Tabs
      document.querySelectorAll('.feed-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          document.querySelectorAll('.feed-tab').forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          const strategy = tab.dataset.strategy;
          this.filterDashboardFeed(strategy);
        });
      });

      // Refresh Feed Button
      document.getElementById('btn-refresh-feed')?.addEventListener('click', () => {
        this.loadDashboardFeeds();
        this.showToast('Recommendations refreshed based on your latest activity', 'success');
      });

      // Profile Preferences Form
      document.getElementById('profile-preferences-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleProfileSave();
      });

      // Admin Tabs
      document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
          document.querySelectorAll('.admin-tab-content').forEach(c => c.classList.remove('active'));
          tab.classList.add('active');
          const targetId = `admin-tab-${tab.dataset.adminTab}`;
          document.getElementById(targetId)?.classList.add('active');

          if (tab.dataset.adminTab === 'categories') {
            this.loadAdminCategoriesTable();
          } else if (tab.dataset.adminTab === 'items') {
            this.loadAdminItemsTable();
          } else if (tab.dataset.adminTab === 'users') {
            this.loadAdminUsersTable();
          }
        });
      });

      // Admin Add Item Modal
      document.getElementById('btn-admin-add-item')?.addEventListener('click', () => {
        this.openAdminItemModal();
      });
      document.getElementById('btn-close-admin-modal')?.addEventListener('click', () => {
        this.closeModal('modal-admin-item');
      });
      document.getElementById('form-admin-item')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleAdminSaveItem();
      });

      // Admin Category Modal
      document.getElementById('btn-admin-add-category')?.addEventListener('click', () => {
        this.openAdminCategoryModal();
      });
      document.getElementById('btn-close-admin-category-modal')?.addEventListener('click', () => {
        this.closeModal('modal-admin-category');
      });
      document.getElementById('form-admin-category')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleAdminSaveCategory();
      });

      // Auto-slug generation for category name
      document.getElementById('admin-cat-name')?.addEventListener('input', (e) => {
        const id = document.getElementById('admin-category-id')?.value;
        if (!id) {
          const slugInput = document.getElementById('admin-cat-slug');
          if (slugInput) {
            slugInput.value = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
          }
        }
      });

      // Modal Close Buttons
      document.getElementById('btn-close-why-modal')?.addEventListener('click', () => this.closeModal('modal-why-recommended'));
      document.getElementById('btn-close-item-modal')?.addEventListener('click', () => this.closeModal('modal-item-detail'));

      // Auth expired event
      window.addEventListener('recomai:auth-expired', () => {
        this.updateAuthUI();
        this.showToast('Session expired. Please sign in again.', 'info');
        this.navigate('landing');
      });
    }

    // =========================================================================
    // AUTHENTICATION & ONBOARDING
    // =========================================================================
    updateAuthUI() {
      const isAuth = window.api.isAuthenticated();
      const user = window.api.user;

      const authButtons = document.getElementById('auth-buttons-container');
      const userMenu = document.getElementById('user-menu-container');
      const navAdmin = document.getElementById('nav-admin');
      const adminDivider = document.getElementById('admin-menu-divider');
      const adminLink = document.getElementById('dropdown-admin-link');

      if (isAuth && user) {
        authButtons.style.display = 'none';
        userMenu.style.display = 'block';

        const initials = user.full_name ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'U';
        document.getElementById('user-avatar-initials').textContent = initials;
        document.getElementById('dropdown-user-name').textContent = user.full_name;
        document.getElementById('dropdown-user-email').textContent = user.email;
        document.getElementById('dropdown-user-role').textContent = user.role === 'admin' ? 'Administrator' : 'Student / Engineer';

        const isAdmin = user.role === 'admin';
        if (navAdmin) navAdmin.style.display = isAdmin ? 'inline-block' : 'none';
        if (adminDivider) adminDivider.style.display = isAdmin ? 'block' : 'none';
        if (adminLink) adminLink.style.display = isAdmin ? 'flex' : 'none';
      } else {
        authButtons.style.display = 'flex';
        userMenu.style.display = 'none';
        if (navAdmin) navAdmin.style.display = 'none';
        if (adminDivider) adminDivider.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
      }
    }

    openAuthModal(mode = 'login') {
      this.switchAuthMode(mode);
      this.openModal('modal-auth');
    }

    switchAuthMode(mode) {
      const loginView = document.getElementById('auth-login-view');
      const regView = document.getElementById('auth-register-view');
      if (mode === 'register') {
        loginView.style.display = 'none';
        regView.style.display = 'block';
      } else {
        loginView.style.display = 'block';
        regView.style.display = 'none';
      }
    }

    async handleLogin(email, password) {
      try {
        await window.api.login(email, password);
        this.closeModal('modal-auth');
        this.updateAuthUI();
        this.showToast(`Welcome back, ${window.api.user.full_name}!`, 'success');
        this.navigate(window.api.isAdmin() ? 'admin-dashboard' : 'dashboard');
      } catch (err) {
        this.showToast(err.message || 'Login failed', 'error');
      }
    }

    async handleRegister(payload) {
      try {
        await window.api.register(payload);
        this.closeModal('modal-auth');
        this.updateAuthUI();
        this.showToast('Account created successfully!', 'success');
        this.openOnboardingModal();
      } catch (err) {
        this.showToast(err.message || 'Registration failed', 'error');
      }
    }

    openOnboardingModal() {
      const container = document.getElementById('onboarding-categories-chips');
      if (container && this.categories.length) {
        container.innerHTML = this.categories.map(c => `
          <label class="interest-chip">
            <input type="checkbox" name="ob-cats" value="${c.name}">
            <span>${c.name}</span>
          </label>
        `).join('');
      }
      this.openModal('modal-onboarding');
    }

    async handleOnboardingSubmit() {
      const selectedCats = Array.from(document.querySelectorAll('input[name="ob-cats"]:checked')).map(el => el.value);
      const expRadio = document.querySelector('input[name="ob-exp"]:checked');
      const exp = expRadio ? expRadio.value : 'Intermediate';

      if (!selectedCats.length) {
        this.showToast('Please select at least one engineering category to prime your recommendations', 'warning');
        return;
      }

      try {
        await window.api.updatePreferences({
          preferred_categories: selectedCats,
          preferred_tags: selectedCats.map(c => c.toLowerCase().replace(/\s+/g, '-')),
          experience_level: exp
        });

        this.closeModal('modal-onboarding');
        this.showToast('Preferences saved! Your recommendations are ready.', 'success');
        this.navigate('dashboard');
      } catch (err) {
        this.showToast(err.message, 'error');
      }
    }

    // =========================================================================
    // DATA LOADERS & VIEWS
    // =========================================================================
    async loadCategories() {
      try {
        this.categories = await window.api.getCategories();
        
        // Filter dropdowns
        const filterCatSelect = document.getElementById('filter-category');
        const adminCatSelect = document.getElementById('admin-input-category');
        const optionsHtml = this.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

        if (filterCatSelect) filterCatSelect.innerHTML = `<option value="">All Categories</option>${optionsHtml}`;
        if (adminCatSelect) adminCatSelect.innerHTML = optionsHtml;

        // Clean Category Chips in Discover page (without browser scrollbars)
        const chipsContainer = document.getElementById('category-chips-container');
        if (chipsContainer) {
          chipsContainer.innerHTML = `
            <button class="cat-chip-btn active" data-cat="" role="tab">All Disciplines</button>
            ${this.categories.map(c => `<button class="cat-chip-btn" data-cat="${c.id}" role="tab">${c.name}</button>`).join('')}
          `;

          chipsContainer.querySelectorAll('.cat-chip-btn').forEach(btn => {
            btn.addEventListener('click', () => {
              chipsContainer.querySelectorAll('.cat-chip-btn').forEach(b => b.classList.remove('active'));
              btn.classList.add('active');
              this.activeCategoryFilter = btn.dataset.cat;
              if (filterCatSelect) filterCatSelect.value = btn.dataset.cat;
              this.loadDiscoverItems();
            });
          });
        }
      } catch (err) {
        console.error('Failed to load categories', err);
      }
    }

    async loadLandingPreviews() {
      const container = document.getElementById('landing-preview-cards');
      if (!container) return;
      try {
        const feed = await window.api.getFeed('trending', 3);
        container.innerHTML = feed.items.map(rec => this.renderItemCard(rec)).join('');
        this.attachCardEventListeners(container);
      } catch (err) {
        container.innerHTML = `<p class="text-muted text-center">Engine warming up...</p>`;
      }
    }

    async loadDashboardFeeds() {
      const user = window.api.user;
      if (user) {
        document.getElementById('dash-greeting').textContent = `Welcome back, ${user.full_name}`;
        const prefs = user.preferences;
        const topicCount = prefs && prefs.preferred_categories ? prefs.preferred_categories.length : 3;
        document.getElementById('dash-interests-count').textContent = topicCount;
      }

      try {
        const data = await window.api.getDashboardRecommendations();

        // 1. Recommended For You
        const gridRec = document.getElementById('grid-recommended-for-you');
        if (gridRec) {
          gridRec.innerHTML = data.recommended_for_you.length 
            ? data.recommended_for_you.map(r => this.renderItemCard(r)).join('')
            : '<div class="empty-state"><h3>No recommendations yet</h3><p>Complete your profile preferences to activate your personalized feed.</p><button class="btn btn-primary" onclick="window.recomai.navigate(\'profile\')">Configure Interests</button></div>';
          this.attachCardEventListeners(gridRec);
        }

        // 2. Trending For You
        const gridTrending = document.getElementById('grid-trending-for-you');
        if (gridTrending) {
          gridTrending.innerHTML = data.trending_for_you.map(r => this.renderItemCard(r)).join('');
          this.attachCardEventListeners(gridTrending);
        }

        // 3. Based On Interests
        const gridInterests = document.getElementById('grid-based-on-interests');
        if (gridInterests) {
          gridInterests.innerHTML = data.based_on_interests.map(r => this.renderItemCard(r)).join('');
          this.attachCardEventListeners(gridInterests);
        }

        // 4. Recently Viewed
        const gridHistory = document.getElementById('grid-recently-viewed');
        if (gridHistory) {
          gridHistory.innerHTML = data.recently_viewed.length
            ? data.recently_viewed.map(item => this.renderItemCard({ item, match_percentage: 90, score: 0.9, explanation: { headline: "Viewed in your recent session" } })).join('')
            : '<div class="empty-state"><div class="empty-icon">👁</div><h3>No recently viewed items</h3><p>Explore resources in Discover to populate your history.</p></div>';
          this.attachCardEventListeners(gridHistory);
        }
      } catch (err) {
        console.error('Failed to load dashboard feeds', err);
        this.showToast('Could not load recommendation feeds', 'error');
      }
    }

    filterDashboardFeed(strategy) {
      const secRec = document.getElementById('section-rec-for-you');
      const secTrending = document.getElementById('section-trending');
      const secInterests = document.getElementById('section-interests');
      const secHistory = document.getElementById('section-recently-viewed');

      secRec.style.display = (strategy === 'all' || strategy === 'hybrid') ? 'block' : 'none';
      secTrending.style.display = (strategy === 'all' || strategy === 'trending') ? 'block' : 'none';
      secInterests.style.display = (strategy === 'all' || strategy === 'preference') ? 'block' : 'none';
      secHistory.style.display = (strategy === 'all' || strategy === 'history') ? 'block' : 'none';
    }

    async loadDiscoverItems() {
      const container = document.getElementById('discover-items-grid');
      const countEl = document.getElementById('discover-results-count');
      const searchInput = document.getElementById('discover-search-input');
      const q = searchInput ? searchInput.value.trim() : '';

      try {
        let items = [];
        if (q) {
          const searchResults = await window.api.semanticSearch(q, {
            category_id: this.activeCategoryFilter,
            difficulty: this.activeDifficultyFilter
          });
          items = searchResults.map(r => r.item);
          if (countEl) countEl.textContent = `Found ${items.length} semantically relevant resources for "${q}"`;
          container.innerHTML = searchResults.map(r => this.renderItemCard(r)).join('');
        } else {
          items = await window.api.getItems({
            category_id: this.activeCategoryFilter,
            difficulty: this.activeDifficultyFilter,
            sort_by: this.activeSortFilter
          });
          if (countEl) countEl.textContent = `Displaying ${items.length} catalog resources`;
          container.innerHTML = items.map(item => this.renderItemCard({ item, match_percentage: Math.round(item.rating_avg * 19.5), score: item.rating_avg / 5, explanation: { headline: `Rated ${item.rating_avg}★ with ${item.views_count} views` } })).join('');
        }

        if (!items.length) {
          container.innerHTML = `<div class="empty-state"><h3>No matching resources</h3><p>Try refining your search terms or category filters.</p></div>`;
        } else {
          this.attachCardEventListeners(container);
        }
      } catch (err) {
        console.error('Discover items error', err);
        container.innerHTML = `<div class="empty-state">Failed to load catalog resources.</div>`;
      }
    }

    async executeSemanticSearch(query) {
      this.navigate('discover');
      const searchInput = document.getElementById('discover-search-input');
      if (searchInput) searchInput.value = query;
      await this.loadDiscoverItems();
      this.showToast(`Semantic search executed for: "${query}"`, 'info');
    }

    async loadFavorites() {
      const container = document.getElementById('favorites-items-grid');
      try {
        const favs = await window.api.getFavorites();
        if (!favs.length) {
          container.innerHTML = `
            <div class="empty-state">
              <div class="empty-icon">🔖</div>
              <h3>No favorites saved yet</h3>
              <p>Click the bookmark icon on any recommendation card to save resources here.</p>
              <button class="btn btn-primary" onclick="window.recomai.navigate('discover')">Explore Catalog</button>
            </div>
          `;
        } else {
          container.innerHTML = favs.map(item => this.renderItemCard({ item, match_percentage: 95, score: 0.95, explanation: { headline: "Saved in your favorites collection" } })).join('');
          this.attachCardEventListeners(container);
        }
      } catch (err) {
        container.innerHTML = `<div class="empty-state">Failed to load favorites.</div>`;
      }
    }

    async loadProfileData() {
      const user = window.api.user;
      if (!user) return;

      document.getElementById('profile-display-name').textContent = user.full_name;
      document.getElementById('profile-display-email').textContent = user.email;
      document.getElementById('profile-display-role').textContent = user.role === 'admin' ? 'Administrator' : 'Student / Engineer';
      document.getElementById('profile-avatar-large').textContent = user.full_name.slice(0, 2).toUpperCase();

      const prefs = user.preferences || {};
      const expSelect = document.getElementById('pref-experience-level');
      if (expSelect) expSelect.value = prefs.experience_level || 'Intermediate';

      const tagsInput = document.getElementById('pref-tags-input');
      if (tagsInput) tagsInput.value = (prefs.preferred_tags || []).join(', ');

      const bioInput = document.getElementById('pref-bio-input');
      if (bioInput) bioInput.value = prefs.bio || '';

      // Checkbox grid for categories
      const catGrid = document.getElementById('pref-categories-grid');
      if (catGrid && this.categories.length) {
        const userCats = (prefs.preferred_categories || []).map(c => c.toLowerCase());
        catGrid.innerHTML = this.categories.map(c => `
          <label class="interest-chip">
            <input type="checkbox" name="pref-cats" value="${c.name}" ${userCats.includes(c.name.toLowerCase()) ? 'checked' : ''}>
            <span>${c.name}</span>
          </label>
        `).join('');
      }

      // User interaction stats
      try {
        const insights = await window.api.getUserInsights();
        document.getElementById('profile-likes-stat').textContent = insights.interaction_stats.likes;
        document.getElementById('profile-ratings-stat').textContent = insights.interaction_stats.ratings;
        document.getElementById('profile-favs-stat').textContent = insights.interaction_stats.favorites;
      } catch (err) {
        console.warn('Could not load profile stats', err);
      }
    }

    async handleProfileSave() {
      const selectedCats = Array.from(document.querySelectorAll('input[name="pref-cats"]:checked')).map(el => el.value);
      const exp = document.getElementById('pref-experience-level').value;
      const tagsStr = document.getElementById('pref-tags-input').value;
      const bio = document.getElementById('pref-bio-input').value;

      const tags = tagsStr.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);

      try {
        await window.api.updatePreferences({
          preferred_categories: selectedCats,
          preferred_tags: tags,
          experience_level: exp,
          bio
        });
        this.showToast('Learning preferences saved! Recommendations re-indexed.', 'success');
        this.updateAuthUI();
      } catch (err) {
        this.showToast(err.message || 'Failed to update preferences', 'error');
      }
    }

    async loadInsights() {
      try {
        const data = await window.api.getUserInsights();

        // Metrics
        document.getElementById('metric-views').textContent = data.interaction_stats.views;
        document.getElementById('metric-likes').textContent = data.interaction_stats.likes;
        document.getElementById('metric-ratings').textContent = data.interaction_stats.ratings;
        document.getElementById('metric-favs').textContent = data.interaction_stats.favorites;

        // Discipline Affinity Breakdown Bars
        const barsContainer = document.getElementById('insights-bars-container');
        if (barsContainer && data.affinity_radar) {
          barsContainer.innerHTML = data.affinity_radar.map(item => `
            <div class="bar-row">
              <div class="bar-header">
                <span>${item.dimension}</span>
                <span class="text-muted font-mono">${item.score}% Affinity</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" style="width: ${item.score}%;"></div>
              </div>
            </div>
          `).join('');
        }

        // Tag Cloud
        const tagCloud = document.getElementById('insights-tags-cloud');
        if (tagCloud && data.top_tags) {
          tagCloud.innerHTML = data.top_tags.map(t => `
            <span class="tag-chip font-mono">#${t.tag} (${t.count})</span>
          `).join('');
        }

        // Activity Timeline
        const timeline = document.getElementById('insights-activity-timeline');
        if (timeline && data.recent_activity) {
          timeline.innerHTML = data.recent_activity.length
            ? data.recent_activity.map(act => `
                <div class="activity-item-row">
                  <div>
                    <strong>${act.type}</strong> on <span class="gradient-text">${act.item_title}</span>
                    <div class="text-muted" style="font-size: 0.8rem;">${act.details}</div>
                  </div>
                  <span class="text-muted font-mono" style="font-size: 0.78rem;">${this.formatDateTime(act.timestamp)}</span>
                </div>
              `).join('')
            : '<div class="text-muted">No interactions recorded yet. Browse and rate resources to populate your timeline.</div>';
        }
      } catch (err) {
        console.error('Insights error', err);
        this.showToast('Could not load AI Insights', 'error');
      }
    }

    // =========================================================================
    // ADMIN PORTAL
    // =========================================================================
    async loadAdminPortal() {
      try {
        const stats = await window.api.getAdminAnalytics();
        document.getElementById('admin-total-users').textContent = stats.total_users;
        document.getElementById('admin-total-items').textContent = stats.total_items;
        document.getElementById('admin-total-interactions').textContent = stats.total_interactions;
        document.getElementById('admin-avg-rating').textContent = `${stats.average_platform_rating}★`;

        // Most viewed list
        const viewedList = document.getElementById('admin-most-viewed-list');
        if (viewedList) {
          viewedList.innerHTML = stats.most_viewed_items.map(item => `
            <li class="ranked-item">
              <div>
                <strong>${item.title}</strong>
                <div class="text-muted" style="font-size: 0.8rem;">${item.category}</div>
              </div>
              <span class="match-badge">${item.views} Views</span>
            </li>
          `).join('');
        }

        // Most liked list
        const likedList = document.getElementById('admin-most-liked-list');
        if (likedList) {
          likedList.innerHTML = stats.most_liked_items.map(item => `
            <li class="ranked-item">
              <div>
                <strong>${item.title}</strong>
                <div class="text-muted" style="font-size: 0.8rem;">${item.category}</div>
              </div>
              <span class="match-badge" style="border-color: rgba(239, 68, 68, 0.45); color: #f87171;">${item.likes} Likes</span>
            </li>
          `).join('');
        }

        // Items, categories, and users tables
        await this.loadAdminItemsTable();
        await this.loadAdminCategoriesTable();
        await this.loadAdminUsersTable();
      } catch (err) {
        console.error('Admin portal error', err);
        this.showToast('Failed to load admin telemetry', 'error');
      }
    }

    async loadAdminItemsTable() {
      const tbody = document.getElementById('admin-items-tbody');
      try {
        const items = (await window.api.getAdminItems())
              .slice()
              .sort((a, b) => a.id - b.id);
        tbody.innerHTML = items.map(item => `
          <tr>
            <td><code>#${item.id}</code></td>
            <td><strong>${item.title}</strong></td>
            <td><span class="tag-chip">${item.category_name || '-'}</span></td>
            <td><span class="badge ${item.difficulty_level === 'Advanced' ? 'badge-danger' : 'badge-accent'}">${item.difficulty_level}</span></td>
            <td>${item.rating_avg}★ (${item.rating_count})</td>
            <td>${item.views_count}</td>
            <td>${item.likes_count}</td>
            <td>
              <button class="btn btn-glass btn-sm" onclick="window.recomai.openAdminItemModal(${JSON.stringify(item).replace(/"/g, '&quot;')})">Edit</button>
              <button class="btn btn-secondary btn-sm text-danger" onclick="window.recomai.deleteAdminItem(${item.id})">Delete</button>
            </td>
          </tr>
        `).join('');
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Failed to load items</td></tr>`;
      }
    }

    async loadAdminCategoriesTable() {
      const tbody = document.getElementById('admin-categories-tbody');
      if (!tbody) return;
      try {
        let categories = await window.api.getAdminCategories();
        if (!categories || !categories.length) {
          categories = (this.categories && this.categories.length) ? this.categories : await window.api.getCategories();
        }
        if (!categories || !categories.length) {
          tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No categories found. Click "Add Category" to create one.</td></tr>`;
          return;
        }
        tbody.innerHTML = categories.map(cat => `
          <tr>
            <td><code>#${cat.id}</code></td>
            <td><strong>${cat.name}</strong></td>
            <td><code>${cat.slug}</code></td>
            <td><span class="tag-chip">${cat.icon || 'sparkles'}</span></td>
            <td>${cat.items_count || 0}</td>
            <td class="font-mono text-muted">${new Date(cat.created_at).toLocaleDateString()}</td>
            <td>
              <button class="btn btn-glass btn-sm" onclick="window.recomai.openAdminCategoryModal(${JSON.stringify(cat).replace(/"/g, '&quot;')})">Edit</button>
              <button class="btn btn-secondary btn-sm text-danger" onclick="window.recomai.deleteAdminCategory(${cat.id}, '${encodeURIComponent(cat.name)}')">Delete</button>
            </td>
          </tr>
        `).join('');
      } catch (err) {
        console.error('Category table load error:', err);
        if (this.categories && this.categories.length) {
          tbody.innerHTML = this.categories.map(cat => `
            <tr>
              <td><code>#${cat.id}</code></td>
              <td><strong>${cat.name}</strong></td>
              <td><code>${cat.slug}</code></td>
              <td><span class="tag-chip">${cat.icon || 'sparkles'}</span></td>
              <td>${cat.items_count || 0}</td>
              <td class="font-mono text-muted">${new Date(cat.created_at).toLocaleDateString()}</td>
              <td>
                <button class="btn btn-glass btn-sm" onclick="window.recomai.openAdminCategoryModal(${JSON.stringify(cat).replace(/"/g, '&quot;')})">Edit</button>
                <button class="btn btn-secondary btn-sm text-danger" onclick="window.recomai.deleteAdminCategory(${cat.id}, '${encodeURIComponent(cat.name)}')">Delete</button>
              </td>
            </tr>
          `).join('');
        } else {
          tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Failed to load categories</td></tr>`;
        }
      }
    }

    async loadAdminUsersTable() {
      const tbody = document.getElementById('admin-users-tbody');
      try {
        const users = (await window.api.getAdminUsers())
              .slice()
              .sort((a, b) => a.id - b.id);
        const currentUserId = window.api.user ? window.api.user.id : null;
        tbody.innerHTML = users.map(u => `
          <tr>
            <td><code>#${u.id}</code></td>
            <td><strong>${u.full_name}</strong></td>
            <td>${u.email}</td>
            <td><span class="role-badge">${u.role}</span></td>
            <td><span class="badge badge-success">Active</span></td>
            <td class="font-mono text-muted">${new Date(u.created_at).toLocaleDateString()}</td>
            <td>
              ${u.id !== currentUserId ? `
                <button class="btn btn-secondary btn-sm text-danger" onclick="window.recomai.deleteAdminUser(${u.id}, '${encodeURIComponent(u.full_name)}')">Delete</button>
              ` : `<span class="text-muted" style="font-size: 0.8rem;">Current User</span>`}
            </td>
          </tr>
        `).join('');
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Failed to load users</td></tr>`;
      }
    }

    openAdminItemModal(existingItem = null) {
      const titleEl = document.getElementById('admin-modal-title');
      const idInput = document.getElementById('admin-item-id');
      const titleInput = document.getElementById('admin-input-title');
      const catSelect = document.getElementById('admin-input-category');
      const slugInput = document.getElementById('admin-input-slug');
      const descInput = document.getElementById('admin-input-desc');
      const contentInput = document.getElementById('admin-input-content');
      const diffSelect = document.getElementById('admin-input-difficulty');
      const tagsInput = document.getElementById('admin-input-tags');
      const imgInput = document.getElementById('admin-input-image');

      if (catSelect && this.categories && this.categories.length) {
        catSelect.innerHTML = this.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
      }

      if (existingItem) {
        titleEl.textContent = `Edit Resource #${existingItem.id}`;
        idInput.value = existingItem.id;
        titleInput.value = existingItem.title;
        if (catSelect) catSelect.value = existingItem.category_id;
        slugInput.value = existingItem.slug;
        descInput.value = existingItem.description;
        contentInput.value = existingItem.content || '';
        diffSelect.value = existingItem.difficulty_level;
        tagsInput.value = (existingItem.tags || []).join(', ');
        imgInput.value = existingItem.image_url || '';
      } else {
        titleEl.textContent = 'Add New Resource';
        idInput.value = '';
        titleInput.value = '';
        slugInput.value = '';
        descInput.value = '';
        contentInput.value = '';
        tagsInput.value = '';
        imgInput.value = '';
      }
      this.openModal('modal-admin-item');
    }

    async handleAdminSaveItem() {
      const id = document.getElementById('admin-item-id').value;
      const title = document.getElementById('admin-input-title').value;
      const category_id = parseInt(document.getElementById('admin-input-category').value);
      const slug = document.getElementById('admin-input-slug').value;
      const description = document.getElementById('admin-input-desc').value;
      const content = document.getElementById('admin-input-content').value;
      const difficulty_level = document.getElementById('admin-input-difficulty').value;
      const tags = document.getElementById('admin-input-tags').value.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
      const image_url = document.getElementById('admin-input-image').value || DEFAULT_RESOURCE_IMAGE;

      const payload = { title, category_id, slug, description, content, difficulty_level, tags, image_url };

      try {
        if (id) {
          await window.api.updateAdminItem(id, payload);
          this.showToast('Resource updated successfully!', 'success');
        } else {
          await window.api.createAdminItem(payload);
          this.showToast('New resource added and indexed for recommendations!', 'success');
        }
        this.closeModal('modal-admin-item');
        await this.loadAdminItemsTable();
      } catch (err) {
        this.showToast(err.message || 'Operation failed', 'error');
      }
    }

    async deleteAdminItem(id) {
      if (!confirm(`Are you sure you want to delete resource #${id}?`)) return;
      try {
        await window.api.deleteAdminItem(id);
        this.showToast('Resource deleted', 'info');
        await this.loadAdminItemsTable();
      } catch (err) {
        this.showToast(err.message, 'error');
      }
    }

    openAdminCategoryModal(existingCat = null) {
      const titleEl = document.getElementById('admin-category-modal-title');
      const idInput = document.getElementById('admin-category-id');
      const nameInput = document.getElementById('admin-cat-name');
      const slugInput = document.getElementById('admin-cat-slug');
      const descInput = document.getElementById('admin-cat-description');
      const iconInput = document.getElementById('admin-cat-icon');

      if (existingCat) {
        if (titleEl) titleEl.textContent = `Edit Category #${existingCat.id}`;
        if (idInput) idInput.value = existingCat.id;
        if (nameInput) nameInput.value = existingCat.name;
        if (slugInput) slugInput.value = existingCat.slug;
        if (descInput) descInput.value = existingCat.description || '';
        if (iconInput) iconInput.value = existingCat.icon || 'sparkles';
      } else {
        if (titleEl) titleEl.textContent = 'Add New Category';
        if (idInput) idInput.value = '';
        if (nameInput) nameInput.value = '';
        if (slugInput) slugInput.value = '';
        if (descInput) descInput.value = '';
        if (iconInput) iconInput.value = 'sparkles';
      }
      this.openModal('modal-admin-category');
    }

    async handleAdminSaveCategory() {
      const id = document.getElementById('admin-category-id')?.value;
      const name = document.getElementById('admin-cat-name')?.value.trim();
      const slug = document.getElementById('admin-cat-slug')?.value.trim();
      const description = document.getElementById('admin-cat-description')?.value.trim() || null;
      const icon = document.getElementById('admin-cat-icon')?.value.trim() || 'sparkles';

      if (!name || !slug) {
        this.showToast('Category name and slug are required', 'error');
        return;
      }

      const payload = { name, slug, description, icon };

      try {
        if (id) {
          await window.api.updateAdminCategory(id, payload);
          this.showToast(`Category "${name}" updated successfully!`, 'success');
        } else {
          await window.api.createAdminCategory(payload);
          this.showToast(`Category "${name}" created and added to catalog!`, 'success');
        }
        this.closeModal('modal-admin-category');
        await this.loadAdminCategoriesTable();
        await this.loadCategories();
      } catch (err) {
        this.showToast(err.message || 'Operation failed', 'error');
      }
    }

    async deleteAdminCategory(id, encodedName) {
      const name = decodeURIComponent(encodedName || `Category #${id}`);
      if (!confirm(`Are you sure you want to delete category "${name}"? All associated items will also be removed.`)) return;
      try {
        const res = await window.api.deleteAdminCategory(id);
        this.showToast(res.message || 'Category deleted', 'info');
        await this.loadAdminCategoriesTable();
        await this.loadCategories();
        await this.loadAdminItemsTable();
      } catch (err) {
        this.showToast(err.message || 'Failed to delete category', 'error');
      }
    }

    async deleteAdminUser(id, encodedName) {
      const name = decodeURIComponent(encodedName || `User #${id}`);
      if (!confirm(`Are you sure you want to delete user "${name}" and all associated records?`)) return;
      try {
        const res = await window.api.deleteAdminUser(id);
        this.showToast(res.message || 'User deleted successfully', 'info');
        await this.loadAdminUsersTable();
      } catch (err) {
        this.showToast(err.message || 'Failed to delete user', 'error');
      }
    }

    // =========================================================================
    // ITEM CARD RENDERING & INTERACTIONS (NO BROKEN IMAGES)
    // =========================================================================
    renderItemCard(recommendation) {
      const item = recommendation.item || recommendation;
      const matchPct = recommendation.match_percentage || 92;
      const explanation = recommendation.explanation || { headline: 'Recommended based on learning profile' };
      const reasonsJson = encodeURIComponent(JSON.stringify(explanation));

      const imgUrl = item.image_url || DEFAULT_RESOURCE_IMAGE;

      return `
        <div class="item-card" data-item-id="${item.id}">
          <div class="item-card-media">
            <img 
              src="${imgUrl}" 
              alt="${item.title}" 
              class="item-card-image" 
              loading="lazy" 
              onerror="this.onerror=null;this.src='${DEFAULT_RESOURCE_IMAGE}';"
            >
            <div class="item-card-match">
              <span class="match-badge">⚡ ${matchPct}% Match</span>
            </div>
            <div class="item-card-category-badge">${item.category_name || 'Computer Science'}</div>
          </div>

          <div class="item-card-body">
            <h3 class="item-card-title">${item.title}</h3>
            <p class="item-card-desc">${item.description}</p>

            <!-- "Why Recommended" clickable trigger -->
            <div class="item-card-why" data-action="why" data-title="${encodeURIComponent(item.title)}" data-match="${matchPct}" data-reasons="${reasonsJson}">
              <span>💡 ${explanation.headline || 'Matches your interest profile'}</span>
              <span class="why-info-icon">Why?</span>
            </div>

            <div class="item-card-tags">
              ${(item.tags || []).slice(0, 3).map(t => `<span class="tag-chip">#${t}</span>`).join('')}
              <span class="tag-chip">${item.difficulty_level || 'Intermediate'}</span>
            </div>

            <div class="item-card-footer">
              <div class="item-stats">
                <span class="item-stat-icon">★ ${item.rating_avg}</span>
                <span class="item-stat-icon">👁 ${item.views_count}</span>
              </div>
              <div class="item-card-actions">
                <button class="icon-btn ${item.is_liked ? 'active-like' : ''}" data-action="like" data-id="${item.id}" title="Like this resource">
                  ♥
                </button>
                <button class="icon-btn ${item.is_favorited ? 'active-fav' : ''}" data-action="favorite" data-id="${item.id}" title="Save to favorites">
                  ★
                </button>
                <button class="btn btn-secondary btn-sm" data-action="view-detail" data-id="${item.id}">
                  Inspect
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    attachCardEventListeners(parentContainer) {
      // Why Recommended trigger
      parentContainer.querySelectorAll('[data-action="why"]').forEach(el => {
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          const title = decodeURIComponent(el.dataset.title);
          const match = el.dataset.match;
          const reasonsData = JSON.parse(decodeURIComponent(el.dataset.reasons));
          this.openWhyModal(title, match, reasonsData);
        });
      });

      // Inspect / View Details
      parentContainer.querySelectorAll('[data-action="view-detail"]').forEach(el => {
        el.addEventListener('click', async (e) => {
          e.stopPropagation();
          const id = el.dataset.id;
          await this.openItemDetailModal(id);
        });
      });

      // Like toggle
      parentContainer.querySelectorAll('[data-action="like"]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (!window.api.isAuthenticated()) {
            this.showToast('Please sign in to like items and adapt recommendations', 'info');
            this.openAuthModal('login');
            return;
          }
          const id = btn.dataset.id;
          try {
            const res = await window.api.toggleLike(id);
            btn.classList.toggle('active-like', res.is_liked);
            this.showToast(res.message, 'success');
          } catch (err) {
            this.showToast(err.message, 'error');
          }
        });
      });

      // Favorite toggle
      parentContainer.querySelectorAll('[data-action="favorite"]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (!window.api.isAuthenticated()) {
            this.showToast('Please sign in to save items to favorites', 'info');
            this.openAuthModal('login');
            return;
          }
          const id = btn.dataset.id;
          try {
            const res = await window.api.toggleFavorite(id);
            btn.classList.toggle('active-fav', res.is_favorited);
            this.showToast(res.message, 'success');
          } catch (err) {
            this.showToast(err.message, 'error');
          }
        });
      });
    }

    // =========================================================================
    // MODAL HANDLERS
    // =========================================================================
    openModal(modalId) {
      document.getElementById(modalId)?.classList.add('show');
    }

    closeModal(modalId) {
      document.getElementById(modalId)?.classList.remove('show');
    }

    openWhyModal(title, matchPercentage, data) {
      document.getElementById('why-match-badge').textContent = `${matchPercentage}% Match`;
      document.getElementById('why-item-title').textContent = title;
      document.getElementById('why-headline').textContent = data.headline || 'Why this was recommended';

      const reasonsList = document.getElementById('why-reasons-list');
      if (reasonsList) {
        const reasons = data.reasons && data.reasons.length ? data.reasons : [
          "Directly aligns with your selected technical categories.",
          "Strong semantic affinity measured by MAX high-dimensional embeddings.",
          "Ranked with top community consensus by Mojo SIMD scoring."
        ];
        reasonsList.innerHTML = reasons.map(r => `<li>${r}</li>`).join('');
      }

      const weightsContainer = document.getElementById('why-factor-weights');
      if (weightsContainer && data.factor_weights) {
        const weights = data.factor_weights;
        weightsContainer.innerHTML = Object.entries(weights).map(([k, v]) => `
          <div class="bar-row">
            <div class="bar-header">
              <span style="text-transform: capitalize;">${k.replace(/_/g, ' ')}</span>
              <span class="font-mono text-muted">${Math.round(v * 100)}%</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${Math.round(v * 100)}%;"></div>
            </div>
          </div>
        `).join('');
      }

      this.openModal('modal-why-recommended');
    }

    async openItemDetailModal(itemId) {
      const contentEl = document.getElementById('item-detail-content');
      contentEl.innerHTML = '<div class="loading-state">Retrieving resource details...</div>';
      this.openModal('modal-item-detail');

      try {
        const item = await window.api.getItem(itemId);
        this.selectedItemForModal = item;

        // Fetch related items
        const related = await window.api.getRelatedRecommendations(itemId);

        contentEl.innerHTML = `
          <div class="item-detail-header">
            <span class="badge badge-accent">${item.category_name || 'Engineering'}</span>
            <span class="badge ${item.difficulty_level === 'Advanced' ? 'badge-danger' : 'badge-success'}">${item.difficulty_level}</span>
            <h1 class="modal-title" style="margin-top: 10px; line-height: 1.3;">${item.title}</h1>
            <div class="item-stats" style="margin-bottom: 22px;">
              <span>★ ${item.rating_avg} (${item.rating_count} reviews)</span>
              <span>👁 ${item.views_count} views</span>
              <span>♥ ${item.likes_count} likes</span>
            </div>
          </div>

          <div class="item-detail-body">
            <p style="font-size: 1.08rem; line-height: 1.65; margin-bottom: 22px;">${item.description}</p>
            ${item.content ? `<div class="code-box" style="background: rgba(0,0,0,0.45); padding: 20px; border-radius: var(--radius-md); font-family: var(--font-mono); font-size: 0.9rem; margin-bottom: 26px; line-height: 1.55; border: 1px solid var(--glass-border);">${item.content}</div>` : ''}

            <div class="interactive-rating-section" style="background: rgba(255,255,255,0.03); padding: 22px; border-radius: var(--radius-lg); margin-bottom: 32px; border: 1px solid var(--glass-border);">
              <h4 style="margin-bottom: 10px;">Rate this resource (updates recommendation weights):</h4>
              <div class="star-rating-widget" id="detail-star-widget" aria-label="Rating stars">
                ${[1, 2, 3, 4, 5].map(n => `<span class="star ${n <= (item.user_rating || 0) ? 'active' : ''}" data-star="${n}" role="button" tabindex="0">★</span>`).join('')}
              </div>
              <span class="text-muted" id="detail-rating-feedback" style="font-size: 0.85rem; margin-top: 8px; display: block;">
                ${item.user_rating ? `You previously rated this resource ${item.user_rating}★` : 'Click a star to record your rating.'}
              </span>
            </div>

            <div class="related-section">
              <h3 style="margin-bottom: 16px;">Semantically Related Resources</h3>
              <div class="grid grid-2" id="detail-related-grid">
                ${related.length ? related.map(r => this.renderItemCard(r)).join('') : '<p class="text-muted">No related resources found.</p>'}
              </div>
            </div>
          </div>
        `;

        // Star Rating Click Listeners
        const stars = contentEl.querySelectorAll('#detail-star-widget .star');
        stars.forEach(star => {
          star.addEventListener('click', async () => {
            if (!window.api.isAuthenticated()) {
              this.showToast('Please sign in to submit a rating', 'info');
              return;
            }
            const score = parseFloat(star.dataset.star);
            try {
              await window.api.submitRating(itemId, score);
              stars.forEach(s => s.classList.toggle('active', parseFloat(s.dataset.star) <= score));
              document.getElementById('detail-rating-feedback').textContent = `Thank you! Rating of ${score}★ recorded.`;
              this.showToast(`Rated ${score}★. AI profile updated!`, 'success');
            } catch (err) {
              this.showToast(err.message, 'error');
            }
          });
        });

        // Related Card Listeners
        const relatedGrid = contentEl.querySelector('#detail-related-grid');
        if (relatedGrid) this.attachCardEventListeners(relatedGrid);

      } catch (err) {
        contentEl.innerHTML = `<div class="empty-state">Failed to load resource details.</div>`;
      }
    }

    // =========================================================================
    // TOAST NOTIFICATIONS & UTILITIES
    // =========================================================================
    showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `<span>${message}</span>`;
      container.appendChild(toast);

      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    }

    debounce(func, wait) {
      let timeout;
      return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
      };
    }

    formatDateTime(isoString) {
      if (!isoString) return '';
      let str = String(isoString).trim();
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(str) && !str.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(str)) {
        str += 'Z';
      }
      const date = new Date(str);
      if (isNaN(date.getTime())) return isoString;
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }

  // Initialize Global Application
  window.recomai = new RecomaiApp();
})();

