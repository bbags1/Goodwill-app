import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import './ProductList.css';

function ProductList() {
    const [products, setProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [showId, setShowId] = useState(true);
    const [showSearchTerm, setShowSearchTerm] = useState(true);
    const [showSellerName, setShowSellerName] = useState(true);
    const [showProductName, setShowProductName] = useState(true);
    const [showPrice, setShowPrice] = useState(true);
    const [showEbayPrice, setShowEbayPrice] = useState(true);
    const [showAuctionEndTime, setShowAuctionEndTime] = useState(true);
    const [showPriceDifference, setShowPriceDifference] = useState(true);
    const [searchTermFilter, setSearchTermFilter] = useState([]);
    const [sellerNameFilter, setSellerNameFilter] = useState([]);
    const [minPriceFilter, setMinPriceFilter] = useState('');
    const [maxPriceFilter, setMaxPriceFilter] = useState('');
    const [categories, setCategories] = useState([]);
    const [categoryOptions, setCategoryOptions] = useState([]);
    const [categoryFilter, setCategoryFilter] = useState([]);
    const [filterByMargin, setFilterByMargin] = useState(false);
    const [marginFilter, setMarginFilter] = useState('');
    const [favorites, setFavorites] = useState([]);
    const [viewMode, setViewMode] = useState('all'); // 'all' or 'favorites'
    const [displayMode, setDisplayMode] = useState('grid'); // 'grid' or 'table'
    const [isLoading, setIsLoading] = useState(true);
    const [locations, setLocations] = useState([]);

    // Add function to calculate time remaining
    const getTimeRemaining = (endTime) => {
        if (!endTime) return 'No end time';
        
        const now = new Date();
        const end = new Date(endTime);
        const diff = end - now;
        
        if (diff <= 0) return 'Ended';
        
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    // Add useEffect to update times
    useEffect(() => {
        const timer = setInterval(() => {
            // Force re-render to update times
            setProducts(prev => [...prev]);
        }, 60000); // Update every minute
        
        return () => clearInterval(timer);
    }, []);

   // Fetch categories and locations when the component is mounted
   useEffect(() => {
        setIsLoading(true);
        // Fetch search terms (used for search term filter)
        fetch(`/api/categories`)
            .then(response => response.json())
            .then(data => setCategories(data))
            .catch(error => console.error('Error fetching categories:', error));
        
        // Fetch product categories for the category filter
        fetch(`/api/product-categories`)
            .then(response => response.json())
            .then(data => {
                // Store the results directly in categoryOptions state to ensure they're available
                // even if no products are currently loaded
                const categoryOpts = data.map(category => ({ value: category, label: category }));
                setCategoryOptions(categoryOpts);
            })
            .catch(error => console.error('Error fetching product categories:', error));
        
        // Fetch locations
        fetch(`/api/locations`)
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

    // Load saved display mode from localStorage
    useEffect(() => {
        const savedDisplayMode = localStorage.getItem('displayMode');
        if (savedDisplayMode) {
            setDisplayMode(savedDisplayMode);
        }
        
        // Fetch favorites from the API
        fetchFavorites();
    }, []);

    // Fetch favorites from the backend API
    const fetchFavorites = () => {
        fetch(`/api/favorites`)
            .then(response => response.json())
            .then(data => {
                setFavorites(data);
            })
            .catch(error => console.error('Error fetching favorites:', error));
    };
    
    // Save display mode preference
    useEffect(() => {
        localStorage.setItem('displayMode', displayMode);
    }, [displayMode]);

    // Fetch products
    useEffect(() => {
        setIsLoading(true);
        const params = new URLSearchParams();
        searchTermFilter.forEach(term => params.append('search_term', term));
        sellerNameFilter.forEach(name => params.append('seller_name', name));
        fetch(`/api/products?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                data.sort((a, b) => b.price_difference - a.price_difference);  // Sort the data
                
                // Calculate margin percentage for grid view
                data.forEach(product => {
                    if (product.price && product.ebay_price) {
                        product.margin_percentage = ((product.ebay_price - product.price) / product.ebay_price) * 100;
                    } else {
                        product.margin_percentage = 0;
                    }
                    
                    // Remove the Buy It Now flag
                    // product.is_bin = product.bids === 0 || product.bids === null;
                });
                
                setProducts(data);
                setIsLoading(false);
            })
            .catch(error => {
                console.error('Error fetching products:', error);
                setIsLoading(false);
            });
    }, [searchTermFilter, sellerNameFilter]);

    const handleSearchTermFilterChange = selectedOptions => {
        setSearchTermFilter(selectedOptions ? selectedOptions.map(option => option.value) : []);
    };

    const handleCategoryFilterChange = selectedOptions => {
        setCategoryFilter(selectedOptions ? selectedOptions.map(option => option.value) : []);
    };

    const handleSearch = event => {
        setSearchTerm(event.target.value);
    };

    const handleSellerNameFilterChange = selectedOptions => {
        setSellerNameFilter(selectedOptions ? selectedOptions.map(option => option.value) : []);
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
            // Remove from favorites
            fetch(`/api/favorites?item_id=${productId}`, {
                method: 'DELETE',
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        setFavorites(favorites.filter(id => id !== productId));
                    }
                })
                .catch(error => console.error('Error removing favorite:', error));
        } else {
            // Add to favorites
            fetch(`/api/favorites`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ item_id: productId }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        setFavorites([...favorites, productId]);
                    }
                })
                .catch(error => console.error('Error adding favorite:', error));
        }
    };

    const openGoodwillListing = (productId) => {
        window.open(`https://shopgoodwill.com/item/${productId}`, '_blank');
    };


    let filteredProducts = products
    .filter(product => (
        (product.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) &&
        (searchTermFilter.length === 0 || searchTermFilter.includes(product.search_term)) &&
        (categoryFilter.length === 0 || categoryFilter.includes(product.category_name)) &&
        (sellerNameFilter.length === 0 || sellerNameFilter.includes(product.seller_name)) &&
        (minPriceFilter === '' || (product.price || 0) >= Number(minPriceFilter)) &&
        (maxPriceFilter === '' || (product.price || 0) <= Number(maxPriceFilter)) &&
        (!filterByMargin || (marginFilter === '' || 
            ((product.ebay_price || 0) > 0 && 
             ((((product.ebay_price || 0) - (product.price || 0)) / (product.ebay_price || 0)) >= Number(marginFilter)/100))
        )
    )));

    // Further filter based on view mode
    if (viewMode === 'favorites') {
        filteredProducts = filteredProducts.filter(product => favorites.includes(product.id));
    }

    if (filterByMargin) {
        filteredProducts.sort((a, b) => {
            const marginA = ((a.ebay_price || 0) - (a.price || 0)) / (a.ebay_price || 1);
            const marginB = ((b.ebay_price || 0) - (b.price || 0)) / (b.ebay_price || 1);
            return marginB - marginA;
        });
    } else {
        filteredProducts.sort((a, b) => {
            const diffA = (a.ebay_price || 0) - (a.price || 0);
            const diffB = (b.ebay_price || 0) - (b.price || 0);
            return diffB - diffA;
        });
    }
    
    const searchTermOptions = categories.map(category => ({ value: category, label: category }));
    
    // We don't need to recreate category options here since we're now fetching them directly
    // from the backend and storing them in state
    
    const sellerNameOptions = locations.length > 0 ? 
        locations : 
        Array.from(new Set(products.map(product => product.seller_name)))
            .map(name => ({ value: name, label: name }));

    // Function to render the image with fallback for grid view
    const renderProductImage = (product) => {
        if (!product.image_url) {
            return <div className="no-image">No Image Available</div>;
        }
        
        try {
            // Check if it's a URL or base64 data
            if (typeof product.image_url === 'string' && product.image_url.startsWith('http')) {
                return (
                    <img 
                        src={product.image_url} 
                        alt={product.product_name} 
                        className="product-image"
                        onClick={() => openGoodwillListing(product.id)}
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = 'https://placehold.co/200x200/cccccc/666666?text=No+Image';
                        }}
                    />
                );
            } else if (typeof product.image_url === 'string') {
                return (
                    <img 
                        src={`data:image/jpeg;base64,${product.image_url}`} 
                        alt={product.product_name} 
                        className="product-image"
                        onClick={() => openGoodwillListing(product.id)}
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = 'https://placehold.co/200x200/cccccc/666666?text=No+Image';
                        }}
                    />
                );
            } else {
                return <div className="no-image">Invalid Image</div>;
            }
        } catch (error) {
            console.error("Error rendering image:", error);
            return <div className="no-image">Image Error</div>;
        }
    };

    return (
        <div className="product-container">
            <div className="product-header">
                <div className="search-container">
                    <input 
                        type="text" 
                        placeholder="Search products" 
                        className="search-bar" 
                        value={searchTerm} 
                        onChange={handleSearch} 
                    />
                </div>
                
                <div className="view-controls">
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
                    </div>
                    
                    <div className="display-toggle">
                        <button 
                            className={`view-button ${displayMode === 'grid' ? 'active' : ''}`}
                            onClick={() => setDisplayMode('grid')}
                            title="Grid View"
                        >
                            <i className="fas fa-th"></i>
                        </button>
                        <button 
                            className={`view-button ${displayMode === 'table' ? 'active' : ''}`}
                            onClick={() => setDisplayMode('table')}
                            title="Table View"
                        >
                            <i className="fas fa-table"></i>
                        </button>
                    </div>
                </div>

                {displayMode === 'table' && (
                    <div className="checkbox-container">
                        <label>
                            <input type="checkbox" checked={showId} onChange={e => setShowId(e.target.checked)} />
                            Show ID
                        </label>
                        <label>
                            <input type="checkbox" checked={showSearchTerm} onChange={e => setShowSearchTerm(e.target.checked)} />
                            Show Search Term
                        </label>
                        <label>
                            <input type="checkbox" checked={showSellerName} onChange={e => setShowSellerName(e.target.checked)} />
                            Show Seller Name
                        </label>
                        <label>
                            <input type="checkbox" checked={showProductName} onChange={e => setShowProductName(e.target.checked)} />
                            Show Product Name
                        </label>
                        <label>
                            <input type="checkbox" checked={showPrice} onChange={e => setShowPrice(e.target.checked)} />
                            Show Price
                        </label>
                        <label>
                            <input type="checkbox" checked={showEbayPrice} onChange={e => setShowEbayPrice(e.target.checked)} />
                            Show eBay Price
                        </label>
                        <label>
                            <input type="checkbox" checked={showAuctionEndTime} onChange={e => setShowAuctionEndTime(e.target.checked)} />
                            Show Auction End Time
                        </label>
                        <label>
                            <input type="checkbox" checked={showPriceDifference} onChange={e => setShowPriceDifference(e.target.checked)} />
                            Show Price Difference
                        </label>
                    </div>
                )}

                <div className="filter-container">
                    <div className="filter-row">
                        <div className="filter-item">
                            <label className="filter-label">
                                Filter by Search Term:
                            </label>
                            <Select
                                className="filter-select"
                                isMulti
                                options={searchTermOptions}
                                onChange={handleSearchTermFilterChange}
                            />
                        </div>
                        <div className="filter-item">
                            <label className="filter-label">
                                Filter by Category:
                            </label>
                            <Select
                                className="filter-select"
                                isMulti
                                options={categoryOptions}
                                onChange={handleCategoryFilterChange}
                            />
                        </div>
                    </div>
                    <div className="filter-row">
                        <div className="filter-item">
                            <label className="filter-label">
                                Filter by Seller Name:
                            </label>
                            <Select
                                className="filter-select"
                                isMulti
                                options={sellerNameOptions}
                                onChange={handleSellerNameFilterChange}
                            />
                        </div>
                        <div className="filter-item">
                            <label className="filter-label">
                                Filter by Price:
                            </label>
                            <div className="price-inputs">
                                <input type="number" className="filter-input" placeholder="Min" value={minPriceFilter} onChange={handleMinPriceFilterChange} />
                                <span>to</span>
                                <input type="number" className="filter-input" placeholder="Max" value={maxPriceFilter} onChange={handleMaxPriceFilterChange} />
                            </div>
                        </div>
                        <div className="filter-item">
                            <label className="filter-label">
                                Filter by Margin:
                            </label>
                            <div className="margin-filter">
                                <label>
                                    <input type="checkbox" checked={filterByMargin} onChange={handleFilterByMarginChange} />
                                    Enable
                                </label>
                                {filterByMargin && (
                                    <div className="margin-input">
                                        <input type="number" className="filter-input" placeholder="Min %" value={marginFilter} onChange={handleMarginFilterChange} />
                                        <span>%</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="results-count">
                    Showing {filteredProducts.length} items
                </div>
            </div>
            
            {isLoading ? (
                <div className="loading-spinner">Loading products...</div>
            ) : (
                <>
                    {displayMode === 'grid' ? (
                        <div className="product-grid">
                            {filteredProducts.length === 0 ? (
                                <div className="no-products">No products found matching your criteria.</div>
                            ) : (
                                filteredProducts.map(product => (
                                    <div 
                                        key={product.id} 
                                        className={`product-card ${favorites.includes(product.id) ? 'favorite' : ''}`}
                                    >
                                        <div className="product-image-container">
                                            {renderProductImage(product)}
                                        </div>
                                        
                                        <div className="product-info">
                                            <h3 className="product-name" onClick={() => openGoodwillListing(product.id)}>
                                                {product.product_name}
                                            </h3>
                                            
                                            <div className="time-remaining">
                                                <span className="label">Ends in:</span> {getTimeRemaining(product.auction_end_time)}
                                            </div>
                                            
                                            <div className="product-details">
                                                <div className="price-info">
                                                    <div className="current-price">
                                                        <span className="label">Current:</span> ${product.price ? product.price.toFixed(2) : '0.00'}
                                                    </div>
                                                    <div className="resale-price">
                                                        <span className="label">Resale:</span> ${product.ebay_price ? product.ebay_price.toFixed(2) : '0.00'}
                                                    </div>
                                                </div>
                                                
                                                <div className="margin-info">
                                                    <div className="profit">
                                                        <span className="label">Profit:</span> ${product.ebay_price && product.price ? (product.ebay_price - product.price).toFixed(2) : '0.00'}
                                                    </div>
                                                    <div className="margin-percent">
                                                        <span className="label">Margin:</span> {product.margin_percentage ? product.margin_percentage.toFixed(0) : '0'}%
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <div className="seller-info">
                                                <span className="label">Seller:</span> {product.seller_name}
                                            </div>
                                            
                                            <div className="product-actions">
                                                <button 
                                                    className={`action-button favorite-button ${favorites.includes(product.id) ? 'active' : ''}`}
                                                    onClick={() => toggleFavorite(product.id)}
                                                >
                                                    {favorites.includes(product.id) ? '★ Favorited' : '☆ Favorite'}
                                                </button>
                                                
                                                <button 
                                                    className="action-button view-button"
                                                    onClick={() => openGoodwillListing(product.id)}
                                                >
                                                    View Listing
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    {showId && <th>ID</th>}
                                    {showSearchTerm && <th>Search Term</th>}
                                    {showSellerName && <th>Seller Name</th>}
                                    {showProductName && <th>Product Name</th>}
                                    {showPrice && <th>Price</th>}
                                    {showEbayPrice && <th>eBay Price</th>}
                                    {showAuctionEndTime && <th>Auction End Time (Pacific Time)</th>}
                                    {showPriceDifference && <th>Price Difference</th>}
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                            {filteredProducts.map(product => {
                                const priceDifference = (product.ebay_price || 0) - (product.price || 0);
                                return (
                                    <tr key={product.id} className={`${favorites.includes(product.id) ? 'favorite-row' : ''}`}>
                                        {showId && <td><a href={`https://shopgoodwill.com/item/${product.id}`} target="_blank" rel="noopener noreferrer">{product.id}</a></td>}
                                        {showSearchTerm && <td>{product.search_term}</td>}
                                        {showSellerName && <td>{product.seller_name}</td>}
                                        {showProductName && <td>{product.product_name}</td>}
                                        {showPrice && <td>${(product.price || 0).toFixed(2)}</td>}
                                        {showEbayPrice && <td>${(product.ebay_price || 0).toFixed(2)}</td>}
                                        {showAuctionEndTime && <td>{getTimeRemaining(product.auction_end_time)}</td>}
                                        {showPriceDifference && <td>${priceDifference.toFixed(2)}</td>}
                                        <td className="table-actions">
                                            <button 
                                                className={`table-action-button ${favorites.includes(product.id) ? 'active' : ''}`}
                                                onClick={() => toggleFavorite(product.id)}
                                                title={favorites.includes(product.id) ? "Remove from Favorites" : "Add to Favorites"}
                                            >
                                                {favorites.includes(product.id) ? '★' : '☆'}
                                            </button>
                                        </td>
                                    </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </>
            )}
        </div>
    );
}

export default ProductList;
