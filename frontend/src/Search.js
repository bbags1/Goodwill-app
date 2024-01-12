import React, { useState } from 'react';
import './Search.css';

function Search() {
    const [input, setInput] = useState('');
    const [searchItems, setSearchItems] = useState([]);

    const handleInputChange = (event) => {
        setInput(event.target.value);
    };

    const handleInputKeyPress = (event) => {
        if (event.key === ',') {
            setSearchItems(prevItems => [...prevItems, input.trim()]);
            setInput('');
        }
    };

    const handleDeleteItem = (itemToDelete) => {
        setSearchItems(prevItems => prevItems.filter(item => item !== itemToDelete));
    };

    const handleSearch = () => {
        // Call the backend
        fetch('http://localhost:5000/get_products', { // Update with your backend URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                searchItems: searchItems,
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    };

    return (
        <div className="search-container">
            <input
                type="text"
                value={input}
                onChange={handleInputChange}
                onKeyPress={handleInputKeyPress}
                placeholder="Search"
                className="search-bar"
            />
            <i className="search-icon">🔍</i>
            <button onClick={handleSearch} className="search-button">Search</button>
            <div className="search-items-container">
                {searchItems.map((item, index) => (
                    <div key={index} className="search-item">
                        {item}
                        <button onClick={() => handleDeleteItem(item)} className="delete-button">Delete</button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Search;