import { compose_email, reply_email } from './components/compose.js';
import { load_mailbox } from './components/inbox.js';
import { load_email } from './components/email.js';
import { sendEmail } from './utils/api.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize event listeners
    initializeEventListeners();
    
    // By default, load the inbox
    load_mailbox('inbox');
});

function initializeEventListeners() {
    // Navigation buttons
    document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
    document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
    document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
    document.querySelector('#compose').addEventListener('click', compose_email);

    // Compose form submission
    document.querySelector('#compose-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('recipients', document.querySelector('#compose-recipients').value);
        formData.append('subject', document.querySelector('#compose-subject').value);
        formData.append('body', document.querySelector('#compose-body').value);
        
        // Add attachments if any
        const attachments = document.querySelector('#compose-attachments').files;
        for (let i = 0; i < attachments.length; i++) {
            formData.append('attachments', attachments[i]);
        }
        
        sendEmail(formData)
            .then(result => {
                if (result.message === "Email sent successfully.") {
                    load_mailbox('sent');
                } else {
                    alert(result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to send email. Please try again.');
            });
    });
} 