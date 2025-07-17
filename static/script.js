// script.js
document.addEventListener('DOMContentLoaded', function () {
    console.log('System is running!');

    // Example: Add interactivity to the login form
    const loginForm = document.querySelector('form');
    if (loginForm) {
        loginForm.addEventListener('submit', function (event) {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            if (!email || !password) {
                alert('Please fill in all fields.');
                event.preventDefault();
            }
        });
    }
});