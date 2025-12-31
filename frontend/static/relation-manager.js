class RelationManager {
    /**
     * 初始化关联管理器
     * @param {Object} options - 配置选项
     * @param {string} options.type - 关联类型：'project' 或 'activity'
     * @param {HTMLElement} options.container - 容器元素
     * @param {function} options.onChange - 关联变化时的回调函数
     * @param {Object} options.apiConfig - API配置
     */
    constructor(options) {
        this.type = options.type;
        this.container = options.container;
        this.onChange = options.onChange;
        this.apiConfig = options.apiConfig;
        
        // 初始化状态
        this.selectedItems = new Map();
        this.searchResults = [];
        this.isSearching = false;
        this.searchTimeout = null;
        
        // 创建UI
        this.initUI();
        
        // 绑定事件
        this.bindEvents();
    }

    /**
     * 初始化UI
     */
    initUI() {
        this.container.innerHTML = `
            <div class="relation-manager">
                <div class="relation-header">
                    <h3>${this.type === 'project' ? '项目' : '活动'}管理</h3>
                    <div class="relation-actions">
                        <div class="search-box">
                            <input type="text" id="${this.type}-search" placeholder="搜索${this.type === 'project' ? '项目' : '活动'}...">
                            <button id="${this.type}-search-btn" class="search-btn">搜索</button>
                        </div>
                    </div>
                </div>
                
                <div class="relation-content">
                    <div class="search-results" id="${this.type}-results">
                        <div class="empty-state">请输入关键词搜索${this.type === 'project' ? '项目' : '活动'}</div>
                    </div>
                    
                    <div class="selected-items" id="${this.type}-selected">
                        <h4>已选择的${this.type === 'project' ? '项目' : '活动'}</h4>
                        <div class="items-list" id="${this.type}-items-list">
                            <div class="empty-state">暂无选择</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 搜索输入事件
        const searchInput = this.container.querySelector(`#${this.type}-search`);
        const searchBtn = this.container.querySelector(`#${this.type}-search-btn`);
        
        searchBtn.addEventListener('click', () => this.search());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.search();
            }
        });
        
        // 自动搜索事件（输入时防抖搜索）
        searchInput.addEventListener('input', () => this.autoSearch());
    }

    /**
     * 搜索项目或活动
     */
    async search() {
        const searchInput = this.container.querySelector(`#${this.type}-search`);
        const keyword = searchInput.value.trim();
        
        if (!keyword) {
            this.searchResults = [];
            this.updateUI();
            return;
        }
        
        this.isSearching = true;
        this.updateUI();
        
        try {
            const endpoint = this.type === 'project' ? '/api/projects' : '/api/activities';
            const response = await fetch(`${endpoint}?search=${encodeURIComponent(keyword)}`);
            const result = await response.json();
            
            if (result.success) {
                this.searchResults = result.data;
            } else {
                this.searchResults = [];
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.searchResults = [];
        } finally {
            this.isSearching = false;
            this.updateUI();
        }
    }
    
    /**
     * 自动搜索功能（防抖）
     */
    autoSearch() {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        this.searchTimeout = setTimeout(() => {
            this.search();
        }, 300); // 300ms防抖
    }

    /**
     * 更新UI
     */
    updateUI() {
        this.renderSearchResults();
        this.renderSelectedItems();
    }

    /**
     * 渲染搜索结果
     */
    renderSearchResults() {
        const resultsContainer = this.container.querySelector(`#${this.type}-results`);
        
        if (this.isSearching) {
            resultsContainer.innerHTML = '<div class="loading-state">搜索中...</div>';
            return;
        }
        
        if (this.searchResults.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state">没有找到匹配的结果</div>';
            return;
        }
        
        resultsContainer.innerHTML = this.searchResults.map(item => {
            const isSelected = this.selectedItems.has(item.id);
            return `
                <div class="result-item ${isSelected ? 'selected' : ''}" data-id="${item.id}">
                    <div class="item-info">
                        <h5>${item.title}</h5>
                        <p>${item.description ? item.description.substring(0, 50) + (item.description.length > 50 ? '...' : '') : ''}</p>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-primary btn-small ${isSelected ? 'btn-danger' : 'btn-primary'}" 
                                onclick="${isSelected ? `relationManager.${this.type}.remove(${item.id})` : `relationManager.${this.type}.add(${item.id}, ${JSON.stringify(item)})`}">
                            ${isSelected ? '移除' : '添加'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * 渲染已选择的项目或活动
     */
    renderSelectedItems() {
        const itemsList = this.container.querySelector(`#${this.type}-items-list`);
        
        if (this.selectedItems.size === 0) {
            itemsList.innerHTML = '<div class="empty-state">暂无选择</div>';
            return;
        }
        
        itemsList.innerHTML = Array.from(this.selectedItems.values()).map(item => `
            <div class="selected-item" data-id="${item.id}">
                <div class="item-info">
                    <h5>${item.title}</h5>
                </div>
                <div class="item-actions">
                    <button class="btn btn-danger btn-small" onclick="relationManager.${this.type}.remove(${item.id})">
                        移除
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * 添加关联项
     * @param {number} id - 项目或活动ID
     * @param {Object} item - 项目或活动对象
     */
    add(id, item) {
        this.selectedItems.set(id, item);
        this.updateUI();
        this.onChange && this.onChange(Array.from(this.selectedItems.values()));
    }

    /**
     * 移除关联项
     * @param {number} id - 项目或活动ID
     */
    remove(id) {
        this.selectedItems.delete(id);
        this.updateUI();
        this.onChange && this.onChange(Array.from(this.selectedItems.values()));
    }

    /**
     * 设置已选择的项
     * @param {Array} items - 项目或活动数组
     */
    setSelected(items) {
        this.selectedItems.clear();
        items.forEach(item => {
            this.selectedItems.set(item.id, item);
        });
        this.updateUI();
    }
    
    /**
     * 加载已关联的数据
     * @param {number} artistId - 艺人ID
     */
    async loadRelatedData(artistId) {
        if (!artistId) {
            return;
        }
        
        this.isLoadingRelated = true;
        this.updateUI();
        
        try {
            // 使用现有的艺人详情API获取关联数据
            const response = await fetch(`/api/artists/${artistId}`);
            const result = await response.json();
            
            if (result.success) {
                const artist = result.data;
                // 根据关联类型提取对应的数据
                const relatedData = this.type === 'project' ? artist.projects : artist.activities;
                this.setSelected(relatedData || []);
            }
        } catch (error) {
            console.error('加载关联数据失败:', error);
        } finally {
            this.isLoadingRelated = false;
            this.updateUI();
        }
    }

    /**
     * 获取已选择的项
     * @returns {Array} 已选择的项目或活动数组
     */
    getSelected() {
        return Array.from(this.selectedItems.values());
    }

    /**
     * 清空已选择的项
     */
    clear() {
        this.selectedItems.clear();
        this.updateUI();
        this.onChange && this.onChange([]);
    }
}

// 全局relationManager对象，方便在HTML中直接调用
window.relationManager = window.relationManager || {};

// RelationManager的TypeScript类型定义
/*
declare class RelationManager {
    constructor(options: {
        type: 'project' | 'activity';
        container: HTMLElement;
        onChange?: (items: any[]) => void;
        apiConfig: any;
    });
    
    search(): Promise<void>;
    add(id: number, item: any): void;
    remove(id: number): void;
    setSelected(items: any[]): void;
    getSelected(): any[];
    clear(): void;
}

declare namespace relationManager {
    let project: RelationManager;
    let activity: RelationManager;
}
*/