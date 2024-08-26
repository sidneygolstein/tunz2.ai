async function fetchProtectedResource(url) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('You need to log in first.');
        window.location.href = '/login';  // Redirect to login if no token found
        return;
    }

    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,  // Include the token in the Authorization header
            'Content-Type': 'application/json'
        }
    });

    if (response.ok) {
        const data = await response.json();
        console.log(data);  // Handle the protected resource
    } else if (response.status === 401) {
        alert("Session expired, please log in again.");
        localStorage.removeItem('access_token');
        window.location.href = '/login';  // Redirect to login if the token is invalid or expired
    } else {
        const data = await response.json();
        alert(data.msg);
    }
}
