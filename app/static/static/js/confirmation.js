document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('confirmation-modal');
    const confirmYes = document.getElementById('confirm-yes');
    const confirmNo = document.getElementById('confirm-no');
    let formToSubmit = null;

    // Attach click event listeners to buttons with data-action attributes
    document.querySelectorAll('button[data-action]').forEach(button => {
        button.addEventListener('click', event => {
            event.preventDefault();  // Prevent the form from submitting immediately

            formToSubmit = button.closest('form');  // Get the form that the button belongs to
            console.log("Form to submit identified:", formToSubmit);

            // Show the confirmation modal
            modal.style.display = 'block';
        });
    });

    // Handle the "Yes" button click in the confirmation modal
    confirmYes.addEventListener('click', async () => {
        console.log("Yes button clicked");
        if (formToSubmit) {
            await submitFormAsAjax(formToSubmit);  // Submit the form via AJAX
        }
        modal.style.display = 'none';  // Hide the modal after form submission
    });

    // Handle the "No" button click in the confirmation modal
    confirmNo.addEventListener('click', () => {
        console.log("No button clicked, closing modal");
        modal.style.display = 'none';  // Just hide the modal if the user cancels
    });

    async function submitFormAsAjax(form) {
        console.log("Submitting form via AJAX");
    
        try {
            const formData = new FormData(form);
            const formDataObject = {};
            formData.forEach((value, key) => {
                formDataObject[key] = value;
            });
    
            console.log("Form data prepared for submission:", formDataObject);
    
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formDataObject),
                credentials: 'include'
            });
    
            if (response.ok) {
                const data = await response.json();
                console.log("Form submitted successfully:", data);
                window.location.href = data.redirect_url;
            } else {
                console.error("Unexpected non-JSON response:", response);
                const errorText = await response.text();
                console.error(errorText);
                alert("An unexpected error occurred. Please try again.");
            }
        } catch (error) {
            console.error('Error during form submission:', error);
            alert('An error occurred while submitting the form.');
        }
    }    
});
