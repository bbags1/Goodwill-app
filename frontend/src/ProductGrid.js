import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import './ProductGrid.css';

function ProductGrid() {
    const [products, setProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchTermFilter, setSearchTermFilter] = useState([]);
    const [sellerNameFilter, setSellerNameFilter] = useState(['198']); // Default to Spokane
    const [minPriceFilter, setMinPriceFilter] = useState('');
    const [maxPriceFilter, setMaxPriceFilter] = useState('');
    const [categories, setCategories] = useState([]);
    const [locations, setLocations] = useState([]);
    const [filterByMargin, setFilterByMargin] = useState(true); // Default to filtering by margin
    const [marginFilter, setMarginFilter] = useState('50'); // Default to 50% margin
    const [favorites, setFavorites] = useState([]);
    const [promising, setPromising] = useState([]);
    const [viewMode, setViewMode] = useState('all'); // 'all', 'favorites', or 'promising'
    const [isLoading, setIsLoading] = useState(true);
    const [showFilters, setShowFilters] = useState(false);

    // Fetch categories when the component is mounted
    useEffect(() => {
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/categories`)
            .then(response => response.json())
            .then(data => setCategories(data))
            .catch(error => console.error('Error fetching categories:', error));
            
        // Fetch locations from the /locations endpoint
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/locations`)
            .then(response => response.json())
            .then(data => {
                const locationOptions = Object.entries(data).map(([id, name]) => ({
                    value: id,
                    label: name
                }));
                setLocations(locationOptions);
            })
            .catch(error => console.error('Error fetching locations:', error));
    }, []);

    // Fetch products based on filters
    useEffect(() => {
        setIsLoading(true);
        const params = new URLSearchParams();
        searchTermFilter.forEach(term => params.append('search_term', term));
        sellerNameFilter.forEach(name => params.append('seller_name', name));
        
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/products?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                // Calculate margin percentage for each product
                data.forEach(product => {
                    product.margin_percentage = product.ebay_price ? 
                        ((product.ebay_price - product.price) / product.ebay_price) * 100 : 0;
                    
                    // Determine if it's a Buy It Now item (this is a placeholder - adjust based on your actual data)
                    product.is_bin = product.bids === 0 || product.bids === null;
                });
                
                // Sort by margin percentage if filterByMargin is true
                if (filterByMargin) {
                    data.sort((a, b) => b.margin_percentage - a.margin_percentage);
                } else {
                    data.sort((a, b) => b.price_difference - a.price_difference);
                }
                
                setProducts(data);
                setIsLoading(false);
            })
            .catch(error => {
                console.error('Error fetching products:', error);
                setIsLoading(false);
            });
    }, [searchTermFilter, sellerNameFilter]);

    // Load saved favorites and promising items from localStorage
    useEffect(() => {
        const savedFavorites = localStorage.getItem('favorites');
        if (savedFavorites) {
            setFavorites(JSON.parse(savedFavorites));
        }
        
        const savedPromising = localStorage.getItem('promising');
        if (savedPromising) {
            setPromising(JSON.parse(savedPromising));
        }
    }, []);

    // Save favorites to localStorage when they change
    useEffect(() => {
        localStorage.setItem('favorites', JSON.stringify(favorites));
    }, [favorites]);

    // Save promising items to localStorage when they change
    useEffect(() => {
        localStorage.setItem('promising', JSON.stringify(promising));
    }, [promising]);

    const handleSearchTermFilterChange = selectedOptions => {
        setSearchTermFilter(selectedOptions ? selectedOptions.map(option => option.value) : []);
    };

    const handleSearch = event => {
        setSearchTerm(event.target.value);
    };

    const handleSellerNameFilterChange = selectedOptions => {
        setSellerNameFilter(selectedOptions ? selectedOptions.map(option => option.value) : ['198']);
    };

    const handleMinPriceFilterChange = event => {
        setMinPriceFilter(event.target.value);
    };

    const handleMaxPriceFilterChange = event => {
        setMaxPriceFilter(event.target.value);
    };

    const handleFilterByMarginChange = event => {
        setFilterByMargin(event.target.checked);
    };

    const handleMarginFilterChange = event => {
        setMarginFilter(event.target.value);
    };

    const toggleFavorite = (productId) => {
        if (favorites.includes(productId)) {
            setFavorites(favorites.filter(id => id !== productId));
        } else {
            setFavorites([...favorites, productId]);
        }
    };

    const togglePromising = (productId) => {
        if (promising.includes(productId)) {
            setPromising(promising.filter(id => id !== productId));
        } else {
            setPromising([...promising, productId]);
        }
    };

    const openGoodwillListing = (productId) => {
        window.open(`https://shopgoodwill.com/item/${productId}`, '_blank');
    };

    // Filter products based on search term, price range, and margin
    let filteredProducts = products.filter(product =>
        product.product_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        (minPriceFilter === '' || product.price >= Number(minPriceFilter)) &&
        (maxPriceFilter === '' || product.price <= Number(maxPriceFilter)) &&
        (!filterByMargin || marginFilter === '' || product.margin_percentage >= Number(marginFilter))
    );

    // Further filter based on view mode
    if (viewMode === 'favorites') {
        filteredProducts = filteredProducts.filter(product => favorites.includes(product.id));
    } else if (viewMode === 'promising') {
        filteredProducts = filteredProducts.filter(product => promising.includes(product.id));
    }

    const searchTermOptions = categories.map(category => ({ value: category, label: category }));

    // Use the fetched locations instead of hardcoding them
    const sellerNameOptions = locations.length > 0 ? locations : [{ value: '198', label: 'WA, Spokane' }];

    return (
        <div className="product-grid-container">
            <div className="product-grid-header">
                <div className="search-container">
                    <input 
                        type="text" 
                        placeholder="Search products" 
                        className="search-bar" 
                        value={searchTerm} 
                        onChange={handleSearch} 
                    />
                    <button 
                        className="filter-toggle-button" 
                        onClick={() => setShowFilters(!showFilters)}
                    >
                        {showFilters ? 'Hide Filters' : 'Show Filters'}
                    </button>
                </div>
                
                <div className="view-mode-tabs">
                    <button 
                        className={`tab-button ${viewMode === 'all' ? 'active' : ''}`}
                        onClick={() => setViewMode('all')}
                    >
                        All Items
                    </button>
                    <button 
                        className={`tab-button ${viewMode === 'favorites' ? 'active' : ''}`}
                        onClick={() => setViewMode('favorites')}
                    >
                        Favorites ({favorites.length})
                    </button>
                    <button 
                        className={`tab-button ${viewMode === 'promising' ? 'active' : ''}`}
                        onClick={() => setViewMode('promising')}
                    >
                        Promising ({promising.length})
                    </button>
                </div>
                
                {showFilters && (
                    <div className="filters-container">
                        <div className="filter-row">
                            <div className="filter-group">
                                <label>Categories:</label>
                                <Select
                                    isMulti
                                    name="categories"
                                    options={searchTermOptions}
                                    className="basic-multi-select"
                                    classNamePrefix="select"
                                    onChange={handleSearchTermFilterChange}
                                    placeholder="Select categories..."
                                />
                            </div>
                            
                            <div className="filter-group">
                                <label>Locations:</label>
                                <Select
                                    isMulti
                                    name="locations"
                                    options={sellerNameOptions}
                                    className="basic-multi-select"
                                    classNamePrefix="select"
                                    onChange={handleSellerNameFilterChange}
                                    defaultValue={locations.find(loc => loc.value === '198') ? [locations.find(loc => loc.value === '198')] : [{ value: '198', label: 'WA, Spokane' }]}
                                    placeholder="Select locations..."
                                />
                            </div>
                        </div>
                        
                        <div className="filter-row">
                            <div className="filter-group">
                                <label>Price Range:</label>
                                <div className="price-inputs">
                                    <input
                                        type="number"
                                        placeholder="Min $"
                                        value={minPriceFilter}
                                        onChange={handleMinPriceFilterChange}
                                    />
                                    <span>to</span>
                                    <input
                                        type="number"
                                        placeholder="Max $"
                                        value={maxPriceFilter}
                                        onChange={handleMaxPriceFilterChange}
                                    />
                                </div>
                            </div>
                            
                            <div className="filter-group">
                                <div className="margin-filter">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={filterByMargin}
                                            onChange={handleFilterByMarginChange}
                                        />
                                        Filter by Margin
                                    </label>
                                    {filterByMargin && (
                                        <div className="margin-input">
                                            <input
                                                type="number"
                                                placeholder="Min %"
                                                value={marginFilter}
                                                onChange={handleMarginFilterChange}
                                            />
                                            <span>%</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            
            {isLoading ? (
                <div className="loading-spinner">Loading products...</div>
            ) : (
                <div className="product-grid">
                    {filteredProducts.length === 0 ? (
                        <div className="no-products">No products found matching your criteria.</div>
                    ) : (
                        filteredProducts.map(product => (
                            <div 
                                key={product.id} 
                                className={`product-card ${favorites.includes(product.id) ? 'favorite' : ''} ${promising.includes(product.id) ? 'promising' : ''}`}
                            >
                                <div className="product-image-container">
                                    <img 
                                        src={`data:image/jpeg;base64,${product.image_url}`} 
                                        alt={product.product_name} 
                                        className="product-image"
                                        onClick={() => openGoodwillListing(product.id)}
                                    />
                                    {product.is_bin && (
                                        <div className="bin-badge">Buy It Now</div>
                                    )}
                                </div>
                                
                                <div className="product-info">
                                    <h3 className="product-name" onClick={() => openGoodwillListing(product.id)}>
                                        {product.product_name}
                                    </h3>
                                    
                                    <div className="product-details">
                                        <div className="price-info">
                                            <div className="current-price">
                                                <span className="label">Current:</span> ${product.price.toFixed(2)}
                                            </div>
                                            <div className="resale-price">
                                                <span className="label">Resale:</span> ${product.ebay_price.toFixed(2)}
                                            </div>
                                        </div>
                                        
                                        <div className="margin-info">
                                            <div className="profit">
                                                <span className="label">Profit:</span> ${(product.ebay_price - product.price).toFixed(2)}
                                            </div>
                                            <div className="margin-percent">
                                                <span className="label">Margin:</span> {product.margin_percentage.toFixed(0)}%
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className="product-actions">
                                        <button 
                                            className={`action-button favorite-button ${favorites.includes(product.id) ? 'active' : ''}`}
                                            onClick={() => toggleFavorite(product.id)}
                                        >
                                            {favorites.includes(product.id) ? '★ Favorited' : '☆ Favorite'}
                                        </button>
                                        
                                        <button 
                                            className={`action-button promising-button ${promising.includes(product.id) ? 'active' : ''}`}
                                            onClick={() => togglePromising(product.id)}
                                        >
                                            {promising.includes(product.id) ? '✓ Promising' : '○ Promising'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}

export default ProductGrid; 