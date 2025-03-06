import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import './Settings.css';

function Settings() {
    const [locations, setLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState({ value: '198', label: 'WA, Spokane' });
    const [marginThreshold, setMarginThreshold] = useState(50);
    const [notificationEmail, setNotificationEmail] = useState('');
    const [notificationPhone, setNotificationPhone] = useState('');
    const [notificationType, setNotificationType] = useState('email');
    const [updateFrequency, setUpdateFrequency] = useState('daily');
    const [searchTerms, setSearchTerms] = useState(['']);
    const [sellerIds, setSellerIds] = useState(['19', '198']);
    const [cityOptions, setCityOptions] = useState([]);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [isUpdatingPrices, setIsUpdatingPrices] = useState(false);
    const [actionMessage, setActionMessage] = useState('');
    const [actionError, setActionError] = useState('');

    // Fetch locations from seller_map.json
    useEffect(() => {
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/locations`)
            .then(response => response.json())
            .then(data => {
                const locationOptions = Object.entries(data).map(([id, name]) => ({
                    value: id,
                    label: name
                }));
                setLocations(locationOptions);
                setCityOptions(locationOptions);
            });
    }, []);

    // Fetch user settings
    useEffect(() => {
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/settings`)
            .then(response => response.json())
            .then(data => {
                if (data.location) {
                    setSelectedLocation({ value: data.location, label: locations.find(loc => loc.value === data.location)?.label || 'WA, Spokane' });
                }
                if (data.margin_threshold) {
                    setMarginThreshold(data.margin_threshold);
                }
                if (data.notification_email) {
                    setNotificationEmail(data.notification_email);
                }
                if (data.notification_phone) {
                    setNotificationPhone(data.notification_phone);
                }
                if (data.notification_type) {
                    setNotificationType(data.notification_type);
                }
                if (data.update_frequency) {
                    setUpdateFrequency(data.update_frequency);
                }
                if (data.search_terms && Array.isArray(data.search_terms)) {
                    setSearchTerms(data.search_terms.length > 0 ? data.search_terms : ['']);
                }
                if (data.seller_ids && Array.isArray(data.seller_ids)) {
                    setSellerIds(data.seller_ids.length > 0 ? data.seller_ids : ['19', '198']);
                }
            })
            .catch(error => {
                console.error('Error fetching settings:', error);
            });
    }, [locations]);

    const handleSaveSettings = () => {
        setIsSaving(true);
        
        const settings = {
            location: selectedLocation.value,
            margin_threshold: marginThreshold,
            notification_email: notificationEmail,
            notification_phone: notificationPhone,
            notification_type: notificationType,
            update_frequency: updateFrequency,
            search_terms: searchTerms.filter(term => term.trim() !== ''),
            seller_ids: sellerIds.filter(id => id.trim() !== '')
        };

        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        })
        .then(response => response.json())
        .then(data => {
            setIsSaving(false);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            setIsSaving(false);
        });
    };

    const addSearchTerm = () => {
        setSearchTerms([...searchTerms, '']);
    };

    const updateSearchTerm = (index, value) => {
        const newSearchTerms = [...searchTerms];
        newSearchTerms[index] = value;
        setSearchTerms(newSearchTerms);
    };

    const removeSearchTerm = (index) => {
        const newSearchTerms = [...searchTerms];
        newSearchTerms.splice(index, 1);
        setSearchTerms(newSearchTerms);
    };

    const addSellerId = () => {
        setSellerIds([...sellerIds, '']);
    };

    const updateSellerId = (index, value) => {
        const newSellerIds = [...sellerIds];
        newSellerIds[index] = value;
        setSellerIds(newSellerIds);
    };

    const removeSellerId = (index) => {
        const newSellerIds = [...sellerIds];
        newSellerIds.splice(index, 1);
        setSellerIds(newSellerIds);
    };

    const handleManualSearch = () => {
        setIsSearching(true);
        setActionMessage('');
        setActionError('');
        
        // Filter out empty search terms
        const filteredSearchTerms = searchTerms.filter(term => term.trim() !== '');
        const filteredSellerIds = sellerIds.filter(id => id.trim() !== '');
        
        if (filteredSearchTerms.length === 0 || filteredSellerIds.length === 0) {
            setActionError('Please enter at least one search term and location');
            setIsSearching(false);
            return;
        }
        
        setActionMessage('Searching Goodwill for items... This may take a few minutes.');
        
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/manual-search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_terms: filteredSearchTerms,
                seller_ids: filteredSellerIds
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setActionMessage(data.message);
            } else {
                setActionError(data.error || 'An error occurred during the search');
            }
            setIsSearching(false);
        })
        .catch(error => {
            setActionError('Failed to connect to the server');
            setIsSearching(false);
        });
    };

    const handleManualPriceUpdate = () => {
        setIsUpdatingPrices(true);
        setActionMessage('');
        setActionError('');
        
        setActionMessage('Updating prices with Gemini AI... This may take a few minutes.');
        
        fetch(`http://${process.env.REACT_APP_SERVER_IP}:5001/manual-price-update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setActionMessage(data.message);
            } else {
                setActionError(data.error || 'An error occurred during price update');
            }
            setIsUpdatingPrices(false);
        })
        .catch(error => {
            setActionError('Failed to connect to the server');
            setIsUpdatingPrices(false);
        });
    };

    return (
        <div className="settings-container">
            <h2>Settings</h2>
            
            <div className="settings-section">
                <h3>Location</h3>
                <p>Select your default location for item searches:</p>
                <Select
                    className="location-select"
                    value={selectedLocation}
                    onChange={setSelectedLocation}
                    options={locations}
                    isSearchable={true}
                />
            </div>
            
            <div className="settings-section">
                <h3>Search Criteria</h3>
                <p>Enter search terms for items you're interested in:</p>
                
                <div className="search-terms-container">
                    {searchTerms.map((term, index) => (
                        <div key={index} className="search-term-input">
                            <input
                                type="text"
                                value={term}
                                onChange={(e) => updateSearchTerm(index, e.target.value)}
                                placeholder="Enter search term"
                            />
                            <button 
                                type="button" 
                                className="remove-btn"
                                onClick={() => removeSearchTerm(index)}
                                disabled={searchTerms.length === 1}
                            >
                                &times;
                            </button>
                        </div>
                    ))}
                    <button 
                        type="button" 
                        className="add-btn"
                        onClick={addSearchTerm}
                    >
                        + Add Search Term
                    </button>
                </div>

                <p>Filter by Locations:</p>
                <div className="seller-ids-container">
                    {sellerIds.map((id, index) => (
                        <div key={index} className="seller-id-input">
                            <Select
                                className="location-select"
                                value={cityOptions.find(option => option.value === id) || null}
                                onChange={(selectedOption) => updateSellerId(index, selectedOption ? selectedOption.value : '')}
                                options={cityOptions}
                                isSearchable={true}
                                placeholder="Select a location"
                            />
                            <button 
                                type="button" 
                                className="remove-btn"
                                onClick={() => removeSellerId(index)}
                                disabled={sellerIds.length === 1}
                            >
                                &times;
                            </button>
                        </div>
                    ))}
                    <button 
                        type="button" 
                        className="add-btn"
                        onClick={addSellerId}
                    >
                        + Add Location
                    </button>
                </div>
            </div>
            
            <div className="settings-section">
                <h3>Manual Actions</h3>
                <p>Manually trigger data collection and price estimation:</p>
                <div className="manual-actions">
                    <button 
                        className="action-button search-button" 
                        onClick={handleManualSearch}
                        disabled={isSearching}
                    >
                        {isSearching ? 'Searching...' : 'Search Goodwill'}
                    </button>
                    <button 
                        className="action-button price-button" 
                        onClick={handleManualPriceUpdate}
                        disabled={isUpdatingPrices}
                    >
                        {isUpdatingPrices ? 'Updating Prices...' : 'Update Prices with Gemini'}
                    </button>
                </div>
                {actionMessage && <div className="action-success">{actionMessage}</div>}
                {actionError && <div className="action-error">{actionError}</div>}
            </div>
            
            <div className="settings-section">
                <h3>Profit Margin</h3>
                <p>Set the minimum profit margin threshold for notifications:</p>
                <div className="slider-container">
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={marginThreshold}
                        onChange={(e) => setMarginThreshold(parseInt(e.target.value))}
                        className="margin-slider"
                    />
                    <span className="margin-value">{marginThreshold}%</span>
                </div>
            </div>
            
            <div className="settings-section">
                <h3>Notifications</h3>
                <p>How would you like to receive notifications about interesting items?</p>
                <div className="notification-options">
                    <label>
                        <input
                            type="radio"
                            name="notification-type"
                            value="email"
                            checked={notificationType === 'email'}
                            onChange={() => setNotificationType('email')}
                        />
                        Email
                    </label>
                    <label>
                        <input
                            type="radio"
                            name="notification-type"
                            value="sms"
                            checked={notificationType === 'sms'}
                            onChange={() => setNotificationType('sms')}
                        />
                        Text Message
                    </label>
                    <label>
                        <input
                            type="radio"
                            name="notification-type"
                            value="both"
                            checked={notificationType === 'both'}
                            onChange={() => setNotificationType('both')}
                        />
                        Both
                    </label>
                </div>
                
                {(notificationType === 'email' || notificationType === 'both') && (
                    <div className="notification-input">
                        <label>Email Address:</label>
                        <input
                            type="email"
                            value={notificationEmail}
                            onChange={(e) => setNotificationEmail(e.target.value)}
                            placeholder="Enter your email address"
                        />
                    </div>
                )}
                
                {(notificationType === 'sms' || notificationType === 'both') && (
                    <div className="notification-input">
                        <label>Phone Number:</label>
                        <input
                            type="tel"
                            value={notificationPhone}
                            onChange={(e) => setNotificationPhone(e.target.value)}
                            placeholder="Enter your phone number"
                        />
                    </div>
                )}
            </div>
            
            <div className="settings-section">
                <h3>Update Frequency</h3>
                <p>How often should the app check for new items?</p>
                <select
                    value={updateFrequency}
                    onChange={(e) => setUpdateFrequency(e.target.value)}
                    className="frequency-select"
                >
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="twice_daily">Twice Daily</option>
                    <option value="weekly">Weekly</option>
                </select>
            </div>
            
            <div className="settings-actions">
                <button
                    className="save-button"
                    onClick={handleSaveSettings}
                    disabled={isSaving}
                >
                    {isSaving ? 'Saving...' : 'Save Settings'}
                </button>
                
                {saveSuccess && (
                    <div className="save-success">
                        Settings saved successfully!
                    </div>
                )}
            </div>
        </div>
    );
}

export default Settings; 