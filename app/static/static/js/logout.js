document.getElementById('logout-btn').addEventListener('click', async () => {
    // Clear the JWT token from localStorage
    localStorage.removeItem('access_token');
    
    // Optionally, you could also inform the server about the logout
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`  // Send the token if needed for revocation
            }
        });
        
        if (response.ok) {
            // Redirect the user to the login page after successful logout
            window.location.href = '/login';
        } else {
            // Handle any errors (optional)
            alert("Logout failed. Please try again.");
        }
    } catch (error) {
        console.error("Error during logout:", error);
        alert("An error occurred during logout.");
    }
});
