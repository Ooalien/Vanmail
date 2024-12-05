document.addEventListener('DOMContentLoaded', function() {
    // Use buttons to toggle between views
    document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
    document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
    document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
    document.querySelector('#compose').addEventListener('click', compose_email);

    // By default, load the inbox
    load_mailbox('inbox');
});

function compose_email() {
    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#single-email').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';

    // Clear out composition fields
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
}

function load_mailbox(mailbox) {
    // Show the mailbox and hide other views
    document.querySelector('#emails-view').style.display = 'block';
    document.querySelector('#single-email').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';

    // Show the mailbox name
    document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

    // Load the emails for that mailbox
    fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {
        // Create email elements
        emails.forEach(email => {
            const element = document.createElement('div');
            element.className = 'email-item';
            element.innerHTML = `
                <div class="email-sender">${email.sender}</div>
                <div class="email-subject">${email.subject}</div>
                <div class="email-timestamp">${email.timestamp}</div>
            `;
            
            // Add click handler
            element.addEventListener('click', () => load_email(email.id));
            
            document.querySelector('#emails-view').append(element);
        });
    });
}

function load_email(id) {
    fetch(`/emails/${id}`)
    .then(response => response.json())
    .then(email => {
        // Mark as read
        if (!email.read) {
            fetch(`/emails/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ read: true })
            });
        }

        // Display the email
        document.querySelector('#emails-view').style.display = 'none';
        document.querySelector('#compose-view').style.display = 'none';
        const emailView = document.querySelector('#single-email');
        emailView.style.display = 'block';
        emailView.innerHTML = `
            <h3>${email.subject}</h3>
            <div>From: ${email.sender}</div>
            <div>To: ${email.recipients.join(', ')}</div>
            <div>Timestamp: ${email.timestamp}</div>
            <hr>
            <div>${email.body}</div>
        `;
    });
}