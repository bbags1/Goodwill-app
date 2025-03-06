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
    const [filterByMargin, setFilterByMargin] = useState(false);
    const [marginFilter, setMarginFilter] = useState('');

   // Fetch categories when the component is mounted
   useEffect(() => {
    fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/categories`)
        .then(response => response.json())
        .then(data => setCategories(data));
    }, []);

    useEffect(() => {
        const params = new URLSearchParams();
        searchTermFilter.forEach(term => params.append('search_term', term));
        sellerNameFilter.forEach(name => params.append('seller_name', name));
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/products?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                data.sort((a, b) => b.price_difference - a.price_difference);  // Sort the data
                setProducts(data);
            });
    }, [searchTermFilter, sellerNameFilter]);

    const handleSearchTermFilterChange = selectedOptions => {
        setSearchTermFilter(selectedOptions.map(option => option.value));
    };

    const handleSearch = event => {
        setSearchTerm(event.target.value);
    };

    const handleSellerNameFilterChange = selectedOptions => {
        setSellerNameFilter(selectedOptions.map(option => option.value));
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


    let filteredProducts = products
    .filter(product =>
        product.product_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        (searchTermFilter.length === 0 || searchTermFilter.includes(product.search_term)) &&
        (sellerNameFilter.length === 0 || sellerNameFilter.includes(product.seller_name)) &&
        (minPriceFilter === '' || product.price >= Number(minPriceFilter)) &&
        (maxPriceFilter === '' || product.price <= Number(maxPriceFilter)) &&
        (!filterByMargin || (marginFilter === '' || ((product.ebay_price- product.price) / product.ebay_price) >= Number(marginFilter)))
    );

    if (filterByMargin) {
    filteredProducts.sort((a, b) => ((b.ebay_price - b.price) / b.ebay_price) - ((a.ebay_price - a.price) / a.ebay_price));
}else {
    filteredProducts.sort((a, b) => b.ebay_price - a.price - (a.ebay_price - a.price));  // Sort by price difference
    }
    
    const searchTermOptions = categories.map(category => ({ value: category, label: category }));

    const sellerNameOptions = Array.from(new Set(products.map(product => product.seller_name)))
        .map(name => ({ value: name, label: name }));

    
        

    return (
        <div>
            <input type="text" placeholder="Search products" className="search-bar" value={searchTerm} onChange={handleSearch} />
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
            <div className="filter-container">
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
                    <input type="number" className="filter-input" placeholder="Min" value={minPriceFilter} onChange={handleMinPriceFilterChange} />
                    <input type="number" className="filter-input" placeholder="Max" value={maxPriceFilter} onChange={handleMaxPriceFilterChange} />
                </div>
                <div className="filter-item">
                    <label className="filter-label">
                        Filter by Margin:
                    </label>
                    <input type="checkbox" checked={filterByMargin} onChange={handleFilterByMarginChange} />
                    <input type="number" className="filter-input" placeholder="Min" value={marginFilter} onChange={handleMarginFilterChange} />
                </div>
            </div>
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
                    </tr>
                </thead>
                <tbody>
                {filteredProducts.map(product => {
                    const priceDifference = product.ebay_price - product.price;
                    return (
                        <tr key={product.id}>
                            {showId && <td><a href={`https://shopgoodwill.com/item/${product.id}`} target="_blank" rel="noopener noreferrer">{product.id}</a></td>}
                            {showSearchTerm && <td>{product.search_term}</td>}
                            {showSellerName && <td>{product.seller_name}</td>}
                            {showProductName && <td>{product.product_name}</td>}
                            {showPrice && <td>${product.price.toFixed(2)}</td>}
                            {showEbayPrice && <td>${product.ebay_price.toFixed(2)}</td>}
                            {showAuctionEndTime && <td>{product.auction_end_time}</td>}
                            {showPriceDifference && <td>${priceDifference.toFixed(2)}</td>}
                        </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

export default ProductList;
