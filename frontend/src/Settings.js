import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import './Settings.css';

function Settings() {
    const [marginThreshold, setMarginThreshold] = useState(50);
    const [notificationEmail, setNotificationEmail] = useState('');
    const [notificationPhone, setNotificationPhone] = useState('');
    const [notificationType, setNotificationType] = useState('email');
    const [updateFrequency, setUpdateFrequency] = useState('daily');
    const [sellerIds, setSellerIds] = useState([]);
    const [cityOptions, setCityOptions] = useState([]);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [isUpdatingPrices, setIsUpdatingPrices] = useState(false);
    const [actionMessage, setActionMessage] = useState('');
    const [actionError, setActionError] = useState('');

    useEffect(() => {
        // Fetch locations from the backend
        fetch(`/api/locations`)
            .then(response => response.json())
            .then(data => {
                const options = Object.entries(data).map(([id, name]) => ({
                    value: id,
                    label: name
                }));
                setCityOptions(options.sort((a, b) => a.label.localeCompare(b.label)));
            })
            .catch(error => {
                console.error('Error fetching locations:', error);
                setActionError('Failed to load locations');
            });

        // Fetch current settings
        fetch(`/api/settings`)
            .then(response => response.json())
            .then(data => {
                setMarginThreshold(data.margin_threshold);
                setNotificationEmail(data.notification_email || '');
                setNotificationPhone(data.notification_phone || '');
                setNotificationType(data.notification_type || 'email');
                setUpdateFrequency(data.update_frequency || 'daily');
                
                // Parse seller_ids if it's a string, otherwise use as is
                let parsedSellerIds = [];
                try {
                    if (typeof data.seller_ids === 'string') {
                        parsedSellerIds = JSON.parse(data.seller_ids);
                    } else if (Array.isArray(data.seller_ids)) {
                        parsedSellerIds = data.seller_ids;
                    }
                } catch (e) {
                    console.error('Error parsing seller IDs:', e);
                }
                
                // Default to Spokane if no seller IDs
                if (!parsedSellerIds || parsedSellerIds.length === 0) {
                    parsedSellerIds = ['198'];
                }
                
                // Convert to objects with value/label if they're just strings
                const formattedSellerIds = parsedSellerIds.map(id => {
                    if (typeof id === 'object' && id.value) {
                        return id;
                    }
                    return { value: id, label: '' }; // Label will be filled when cityOptions loads
                });
                
                setSellerIds(formattedSellerIds);
            })
            .catch(error => {
                console.error('Error fetching settings:', error);
                setActionError('Failed to load settings');
                // Set default seller ID
                setSellerIds([{ value: '198', label: '' }]);
            });
    }, []);

    // Update seller labels when cityOptions change
    useEffect(() => {
        if (cityOptions.length > 0 && sellerIds.length > 0) {
            const updatedSellerIds = sellerIds.map(seller => {
                const matchingOption = cityOptions.find(option => option.value === seller.value);
                return matchingOption || seller;
            });
            setSellerIds(updatedSellerIds);
        }
    }, [cityOptions]);

    const handleSaveSettings = () => {
        if (sellerIds.length === 0) {
            setActionError('Please select at least one location');
            return;
        }

        setIsSaving(true);
        setSaveSuccess(false);
        setActionError('');

        // Extract just the seller IDs for saving
        const sellerIdsToSave = sellerIds.map(seller => seller.value);

        fetch(`/api/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                seller_ids: sellerIdsToSave,
                margin_threshold: marginThreshold,
                notification_email: notificationEmail,
                notification_phone: notificationPhone,
                notification_type: notificationType,
                update_frequency: updateFrequency,
            }),
        })
        .then(response => response.json())
        .then(data => {
            setIsSaving(false);
            setSaveSuccess(true);
            setActionMessage('Settings saved successfully!');
            setTimeout(() => {
                setSaveSuccess(false);
                setActionMessage('');
            }, 3000);
        })
        .catch(error => {
            setIsSaving(false);
            setActionError('Failed to save settings');
            console.error('Error:', error);
        });
    };

    const addSellerId = () => {
        setSellerIds([...sellerIds, { value: '', label: '' }]);
    };

    const updateSellerId = (index, selected) => {
        const newSellerIds = [...sellerIds];
        
        if (!selected) {
            // If the selected option was cleared, remove this seller ID
            newSellerIds.splice(index, 1);
        } else {
            // Update or add the new seller ID
            if (index >= newSellerIds.length) {
                newSellerIds.push(selected);
            } else {
                newSellerIds[index] = selected;
            }
        }
        
        setSellerIds(newSellerIds);
        setActionError('');
    };

    const removeSellerId = (index) => {
        if (sellerIds.length <= 1) {
            setActionError('You must keep at least one location');
            return;
        }
        const newSellerIds = sellerIds.filter((_, i) => i !== index);
        setSellerIds(newSellerIds);
        setActionError('');
    };

    const handleManualSearch = () => {
        // Validate that at least one location is selected
        if (sellerIds.length === 0) {
            setActionError("Please select at least one location before performing a manual search.");
            return;
        }

        // Validate that all locations have valid values
        const invalidSellerIds = sellerIds.filter(seller => !seller.value);
        if (invalidSellerIds.length > 0) {
            setActionError("Please select valid locations for all entries.");
            return;
        }

        setIsSearching(true);
        setActionMessage("Searching for items...");
        setActionError("");

        // Extract just the seller IDs from the selected locations
        const selectedSellerIds = sellerIds.map(seller => seller.value);
        console.log("Sending seller IDs:", selectedSellerIds);

        // Send request to backend
        fetch(`/api/manual-search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ seller_ids: selectedSellerIds }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            setIsSearching(false);
            if (data.error) {
                setActionError(data.error);
            } else {
                setActionMessage(`Search completed successfully! Found ${data.total_items || 'multiple'} items.`);
                setTimeout(() => setActionMessage(""), 5000);
            }
        })
        .catch(error => {
            setIsSearching(false);
            setActionError(`Error: ${error.message}`);
        });
    };

    const handleManualPriceUpdate = () => {
        setIsUpdatingPrices(true);
        setActionMessage('');
        setActionError('');

        fetch(`/api/manual-price-update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            setIsUpdatingPrices(false);
            setActionMessage('Price update completed successfully!');
            setTimeout(() => setActionMessage(''), 3000);
        })
        .catch(error => {
            setIsUpdatingPrices(false);
            setActionError('Error during price update. Please try again.');
            setTimeout(() => setActionError(''), 3000);
        });
    };

    return (
        <div className="settings-container">
            <h2>Settings</h2>
            
            <div className="settings-section">
                <h3>Locations</h3>
                <p>Select the Goodwill locations you want to monitor:</p>
                <div className="seller-ids-container">
                    {sellerIds.map((seller, index) => (
                        <div key={index} className="seller-id-input">
                            <Select
                                className="location-select"
                                options={cityOptions}
                                value={seller}
                                onChange={(selected) => updateSellerId(index, selected)}
                                placeholder="Select a location..."
                                isSearchable={true}
                                isClearable={true}
                                isDisabled={!cityOptions.length}
                            />
                            <button 
                                className="remove-btn" 
                                onClick={() => removeSellerId(index)}
                                disabled={sellerIds.length <= 1}
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                    {sellerIds.length === 0 && (
                        <div className="seller-id-input">
                            <Select
                                className="location-select"
                                options={cityOptions}
                                onChange={(selected) => updateSellerId(0, selected)}
                                placeholder="Select a location..."
                                isSearchable={true}
                                isClearable={true}
                                isDisabled={!cityOptions.length}
                            />
                        </div>
                    )}
                    <button 
                        className="add-btn" 
                        onClick={addSellerId}
                        disabled={!cityOptions.length}
                    >
                        Add Location
                    </button>
                    {!cityOptions.length && (
                        <p className="loading-message">Loading locations...</p>
                    )}
                </div>
            </div>

            <div className="settings-section">
                <h3>Margin Threshold</h3>
                <p>Set the minimum profit margin for notifications:</p>
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

            <div className="settings-section">
                <h3>Notifications</h3>
                <div className="notification-options">
                    <label>
                        <input
                            type="radio"
                            value="email"
                            checked={notificationType === 'email'}
                            onChange={(e) => setNotificationType(e.target.value)}
                        />
                        Email
                    </label>
                    <label>
                        <input
                            type="radio"
                            value="sms"
                            checked={notificationType === 'sms'}
                            onChange={(e) => setNotificationType(e.target.value)}
                        />
                        SMS
                    </label>
                    <label>
                        <input
                            type="radio"
                            value="both"
                            checked={notificationType === 'both'}
                            onChange={(e) => setNotificationType(e.target.value)}
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
                            placeholder="Enter your email"
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
                <select
                    className="frequency-select"
                    value={updateFrequency}
                    onChange={(e) => setUpdateFrequency(e.target.value)}
                >
                    <option value="hourly">Hourly</option>
                    <option value="twice_daily">Twice Daily</option>
                    <option value="daily">Daily</option>
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
                {saveSuccess && <span className="save-success">Settings saved successfully!</span>}
            </div>

            <div className="manual-actions">
                <button
                    className="action-button search-button"
                    onClick={handleManualSearch}
                    disabled={isSearching}
                >
                    {isSearching ? 'Searching...' : 'Manual Search'}
                </button>
                <button
                    className="action-button price-button"
                    onClick={handleManualPriceUpdate}
                    disabled={isUpdatingPrices}
                >
                    {isUpdatingPrices ? 'Updating...' : 'Update Prices'}
                </button>
                {actionMessage && <span className="action-success">{actionMessage}</span>}
                {actionError && <span className="action-error">{actionError}</span>}
            </div>
        </div>
    );
}

export default Settings; 